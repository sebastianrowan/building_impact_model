# from calculations import *
# from utils import *
# from parse import *
import parse
import calculations
import utils

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import datetime
import os
import sys

# What flood depths should be included in the analysis?
MIN_DEPTH = -1
MAX_DEPTH = 16 #16
STEP = .1

# How many simulations should be generated at each flood depth?
N = 100 #500

# Should specific material choices be made for each component for each simulation? (If False, unit cost and ghg are sampled from distribution)
SPECIFIC = True

# Should results be aggregated at the component level? (Set to False to aggregate to building level)
COMPONENT = False


# Where should the results be saved?
RESULT_FILENAME = f"../results/mcs_res1-all_{N}iter{"_specific" if SPECIFIC else ""}{"_component-means" if COMPONENT else ""}.parquet"

# RNG Seed for reproducibility 
SEED = 29705
RNG = np.random.default_rng(seed = SEED)

def main():
    # print(os.getcwd())
    lca_data_path = "../data/component_cost_lca_data.xlsx"
    floorplan_data_path = "../data/floor_plans_raw.xlsx"

    print("Loading datasets...")
    # cost = load_cost_data(path)
    lca_data = pd.read_excel(lca_data_path, sheet_name="Cost_LCA_Coupled")
    plans = pd.read_excel(floorplan_data_path, sheet_name="floor_plans")

    ### Below, specify which subset of plans to run the analysis on ###
    plans = plans[(plans['type'] == "Single-Family")].reset_index()
    # print(plans.shape)
    # print(np.max(plans['ridge_height']))
    # sys.exit() # stop code here to check dataset size

    print("Calculating total building cost from RS means regression...")
    plans['rs_means_cost'] = calculations.calc_rs_means_cost(
        plans['num_floors'], 
        plans['sqft'], 
        (plans['n_bath1'] + plans['n_bath2'])
    )

    plan0 = plans.copy(deep=True).iloc[0]
    # plans = plans.iloc[1:]

    print("Iterate through floorplans and run MCS...")
    start = datetime.datetime.now()

    # **NOTE: parse.parse_floorplan() may cause error when running with original (non-specific component) functions**
    #         this is because certain components were removed from the parse function during the implementation of 
    #         coupled cost and lca data. I have not tested it but if it does fail there are two solutions:
    #           1. remove the components from the cost and lca spreadsheets
    #           2. uncomment the rows for the removed components from the parse function

    # TODO: consider adding logic that ensures the correct function is being used based on config var selection
    result = generate_component_mcs_results_specific(parse.parse_floorplan(plan0), lca_data)
    schema = pa.Schema.from_pandas(result)
    print(schema)
    i = 1
    with pq.ParquetWriter(RESULT_FILENAME, schema) as writer:
        for index, plan in plans.iterrows():
            print(f"Running simulations for floor plan {plan["plan_id"]} ({i} of {plans.shape[0]})")
            parsed_plan = parse.parse_floorplan(plan.copy(deep=True))
            # results = pd.concat([
            #     results,
            #     generate_component_mcs_results_specific(parsed_plan, lca_data)
            #     # generate_component_mcs_results_specific(parsed_plan, lca_data)
            # ])
            result = generate_component_mcs_results_specific(parsed_plan, lca_data)
            batch = pa.RecordBatch.from_pandas(result, schema=schema)
            writer.write_batch(batch)
            i += 1

    # print("saving results")

    # results.to_parquet(RESULT_FILENAME) 
    end = datetime.datetime.now()
    print(f"Time elapsed: {end - start}")

def generate_component_mcs_results(plan, cost, co2):

    #TODO: filter rows in lca_data to randomly select one item for each component
    #  before joining to floor plan.
    components = plan.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    components = components[(components['component_type'] == "structure")]
    
    simulations = utils.generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N)
    result = calculations.flood_structure(simulations)
    result['unit_cost_triang'] = calculations.calc_unit_cost_co2_triang(
        RNG,
        result['total_cost_min'],
        result['total_cost_max'],
        result['total_cost_mean']
    )

    result['unit_co2_triang'] = calculations.calc_unit_cost_co2_triang(
        RNG,
        result['unit_co2_min'],
        result['unit_co2_max'],
        result['unit_co2_mean']
    )

    result['damage_cost_triang'] = result['damage_quantity'] * result['unit_cost_triang']
    result['damage_co2_triang'] = result['damage_quantity'] * result['unit_co2_triang']

    return(result)

def generate_component_mcs_results_specific(plan, lca_data):
    plan = plan[(plan['component_type'] == "structure")]

    # *** This block should be wrapped in separate function (calculations.generate_simulations_specific())
    floods = np.arange(MIN_DEPTH,MAX_DEPTH,STEP)

    rep = len(pd.unique(lca_data.component))
    lca_data_sims = lca_data.groupby('component').sample(N, replace=True, random_state=RNG)

    lca_data_sims['run'] = np.tile(np.arange(N),rep)
    components = plan.merge(lca_data_sims, how = 'left', left_on = 'component_join', right_on = 'component')
   
    
    components_flooded = components.groupby(['component_x','run']).sample(floods.shape[0],replace=True, random_state=RNG)
    floods = np.tile(floods,components.shape[0])

    components_flooded['flood_depth'] = floods
    # ***

    result = calculations.flood_structure(components_flooded)

    result['damage_cost'] = result['damage_quantity'] * result['total_cost']
    result['damage_co2'] = result['damage_quantity'] * result['kg_co2e_fu']
    # result = result[['component_x', 'plan_id', 'sqft', 'num_floors', 'rs_means_cost', 'component_join', 'component_y','product', 'run', 'flood_depth', 'damage_cost', 'damage_co2']]

    result = result.groupby(['component_x', 'plan_id', 'sqft', 'num_floors', 'rs_means_cost', 'flood_depth'], observed=True).agg(
        mean_damage = ('damage_cost', 'mean'),
        mean_co2 = ('damage_co2', 'mean')
    ).reset_index()

    result = result.convert_dtypes(dtype_backend='pyarrow')

    return(result)

def floorplan_mcs(plan, cost, co2):
    components = plan.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    components = components[(components['component_type'] == "structure")]
    
    simulations = calculations.generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N) 

    result = calculations.flood_structure(simulations)


    result['unit_cost_triang'] = calculations.calc_unit_cost_co2_triang(
        RNG,
        result['total_cost_min'],
        result['total_cost_max'],
        result['total_cost_mean']
    )

    result['unit_co2_triang'] = calculations.calc_unit_cost_co2_triang(
        RNG,
        result['unit_co2_min'],
        result['unit_co2_max'],
        result['unit_co2_mean']
    )
    
    result['damage_cost_triang'] = result['damage_quantity'] * result['unit_cost_triang']
    # result['damage_cost_potential'] = result['quantity'] * result['unit_cost_triang']
    # result['damage_cost_min'] = result['damage_quantity'] * result['unit_cost_min']
    # result['damage_cost_max'] = result['damage_quantity'] * result['unit_cost_max']
    # result['damage_cost_mean'] = result['damage_quantity'] * result['unit_cost_mean']

    result['damage_co2_triang'] = result['damage_quantity'] * result['unit_co2_triang']
    # result['damage_co2_min'] = result['damage_quantity'] * result['unit_co2_min']
    # result['damage_co2_max'] = result['damage_quantity'] * result['unit_co2_max']
    # result['damage_co2_mean'] = result['damage_quantity'] * result['unit_co2_mean']
    

    # print("Aggregating results...")
    result = result.groupby(['run', 'plan_id', 'sqft', 'num_floors', 'nbed', 'nbath', 'ncar', 'rs_means_cost', 'flood_depth'], observed=True).agg(
        sum_damage = ('damage_cost_triang', 'sum'),
        sum_co2 = ('damage_co2_triang', 'sum')
    ).reset_index()

    return(result)

def floorplan_mcs_specific(plan, lca_data):
    plan = plan[(plan['component_type'] == "structure")]

    # *** This block should be wrapped in separate function (calculations.generate_simulations_specific())
    floods = np.arange(MIN_DEPTH,MAX_DEPTH,STEP)

    rep = len(pd.unique(lca_data.component))
    lca_data_sims = lca_data.groupby('component').sample(N, replace=True, random_state=RNG)

    lca_data_sims['run'] = np.tile(np.arange(N),rep)
    components = plan.merge(lca_data_sims, how = 'left', left_on = 'component_join', right_on = 'component')
   
    
    components_flooded = components.groupby(['component_x','run']).sample(floods.shape[0],replace=True, random_state=RNG)
    floods = np.tile(floods,components.shape[0])

    components_flooded['flood_depth'] = floods
    # ***
    
    result = calculations.flood_structure(components_flooded)

    result['damage_cost'] = result['damage_quantity'] * result['total_cost']
    result['damage_co2'] = result['damage_quantity'] * result['kg_co2e_fu']
    
    # print(result[(result['component_x']=="Facade") & (result['plan_id']=='11700HZ')][['run','plan_id', 'flood_depth', 'component_x', 'total_cost','damage_quantity','damage_cost']])

    result = result.groupby(['run', 'plan_id', 'sqft', 'num_floors', 'nbed', 'nbath', 'ncar', 'rs_means_cost', 'flood_depth'], observed=True).agg(
        sum_damage = ('damage_cost', 'sum'),
        sum_co2 = ('damage_co2', 'sum')
    ).reset_index()

    return(result)

def print_components():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # print(os.getcwd())
    lca_data_path = "../data/component_lca_data.xlsx"
    floorplan_data_path = "../data/floor_plans_raw.xlsx"

    plans = pd.read_excel(floorplan_data_path, sheet_name="floor_plans")

    plans = plans[
        (plans['roof_footprint'] > 0) &
        (plans['type'] == "Single-Family") &
        (plans['num_floors'] == 1)
    ]

    print("Calculating total building cost from RS means regression...")
    plans['rs_means_cost'] = calculations.calc_rs_means_cost(
        plans['num_floors'], 
        plans['sqft'], 
        (plans['n_bath1'] + plans['n_bath2'])
    )

    plan0 = plans.copy(deep=True).iloc[0]

    comps = parse.parse_floorplan(plan0)
    comps = comps[['component', 'component_type', 'unit', 'failure_calculation', 'quantity', 'min', 'max', 'mode']]
    comps.to_html('../components.html')

def test():
    lca_data_path = "../data/component_cost_lca_data.xlsx"
    N = 5
    plans = pd.read_excel(lca_data_path, sheet_name="test_fp")
    lca_data = pd.read_excel(lca_data_path, sheet_name="test_comp")

    rep = len(pd.unique(lca_data.component))
    lca_data_sims = lca_data.groupby('component').sample(N, replace=True, random_state=RNG)
    lca_data_sims['run'] = np.tile(np.arange(N),rep)

    print(lca_data_sims)
    joined = plans.merge(lca_data_sims, how = 'left', left_on='component_join', right_on='component')
    print(joined)
    
    floods = calculations.generate_floods(0, 1, 0.5, N)
    simulations = floods.merge(joined, how = 'left', on='run')
    print(simulations)
    return


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
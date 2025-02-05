# from calculations import *
# from utils import *
# from parse import *
import parse
import calculations
import utils

from scipy.stats import triang
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import datetime
import os

# What flood depths should be included in the analysis?
MIN_DEPTH = -1
MAX_DEPTH = 16
STEP = .1

# How many simulations should be generated at each flood depth?
N = 500

# Where should the results be saved?
RESULT_FILENAME = f"../results/mcs_res1-all_{N}iter.parquet"

# RNG Seed for reproducibility 
SEED = 29705
RNG = np.random.default_rng(seed = SEED)

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # print(os.getcwd())
    lca_data_path = "../data/component_lca_data.xlsx"
    floorplan_data_path = "../data/floor_plans_raw.xlsx"

    print("Loading datasets...")
    # cost = load_cost_data(path)
    cost = utils.load_rs_means_cost_data(lca_data_path)
    
    co2 = utils.load_co2_data(lca_data_path)

    plans = pd.read_excel(floorplan_data_path, sheet_name="floor_plans")

    ### Below, specify which subset of plans to run the analysis on ###
    plans = plans[
        (plans['roof_footprint'] > 0)
        & (plans['type'] == "Single-Family")
    ]
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
    plans = plans.iloc[1:]

    print("Iterate through floorplans and run MCS...")
    start = datetime.datetime.now()

    # results = floorplan_mcs(parse_floorplan(plan0), cost, co2)
    results = generate_component_mcs_results(parse.parse_floorplan(plan0), cost, co2)
    
    for index, plan in plans.iterrows():
        print(index)
        parsed_plan = parse.parse_floorplan(plan.copy(deep=True))
        results = pd.concat([
            results,
            # floorplan_mcs(parsed_plan, cost, co2)
            generate_component_mcs_results(parsed_plan, cost, co2)
        ])
    print("saving results")

    results.to_parquet(RESULT_FILENAME) 
    end = datetime.datetime.now()
    print(f"Time elapsed: {end - start}")

def generate_component_mcs_results(plan, cost, co2):
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
    result = result.groupby(['run', 'plan_id', 'sqft', 'num_floors', 'rs_means_cost', 'flood_depth'], observed=True).agg(
        sum_damage = ('damage_cost_triang', 'sum'),
        sum_co2 = ('damage_co2_triang', 'sum')
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

if __name__ == "__main__":
    main()
from calculations import *
from utils import *
from visualizations import *
from parse import *

from scipy.stats import triang
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

MIN_DEPTH = -2
MAX_DEPTH = 30
STEP = .1
N = 25
SEED = 521871
RNG = np.random.default_rng(seed = SEED)

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # print(os.getcwd())
    path = "../data/component_quantities_and_depth_damage.xlsx"

    print("Loading datasets...")
    # cost = load_cost_data(path)
    cost = load_rs_means_cost_data(path)
    
    co2 = load_co2_data(path)

    plans = pd.read_excel(path, sheet_name="floor_plans")


    plans = plans.loc[pd.notna(plans['ridge_height'])]

    print("Calculating total building cost from RS means regression...")
    plans['rs_means_cost'] = calc_rs_means_cost(
        plans['num_floors'], 
        plans['sqft'], 
        (plans['n_bath1'] + plans['n_bath2'])
    )

    plan0 = plans.copy(deep=True).iloc[0]
    plans = plans.iloc[1:]

    print("Parsing floorplans...")
    parsed_plans = parse_floorplan(plan0)

    for index, plan in plans.iterrows():
        x = parse_floorplan(plan.copy(deep=True))
        parsed_plans = pd.concat([parsed_plans, x])

    

    components = parsed_plans.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    # Exclude contents for now. After reviewing literature 
    # components = components[(components['component_type'] == "structure") & (components['component_join'] != 'Facade')]
    components = components[(components['component_type'] == "structure")]

    print("Generating flood simulations...")
    simulations = generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N) 

    check_col = np.where(simulations['max'] <= simulations['min'], True, False)
    simulations['check_col'] = check_col

    print("Flooding structures...")
    result = flood_structure(simulations)

    print("Calculating costs and emissions for each flood...")
    result['unit_cost_triang'] = calc_unit_cost_co2_triang(
        RNG,
        result['total_cost_min'],
        result['total_cost_max'],
        result['total_cost_mean']
    )

    result['unit_co2_triang'] = calc_unit_cost_co2_triang(
        RNG,
        result['unit_co2_min'],
        result['unit_co2_max'],
        result['unit_co2_mean']
    )
    
    result['damage_cost_triang'] = result['damage_quantity'] * result['unit_cost_triang']
    result['damage_cost_potential'] = result['quantity'] * result['unit_cost_triang']
    result['damage_cost_min'] = result['damage_quantity'] * result['unit_cost_min']
    result['damage_cost_max'] = result['damage_quantity'] * result['unit_cost_max']
    result['damage_cost_mean'] = result['damage_quantity'] * result['unit_cost_mean']

    result['damage_co2_triang'] = result['damage_quantity'] * result['unit_co2_triang']
    result['damage_co2_min'] = result['damage_quantity'] * result['unit_co2_min']
    result['damage_co2_max'] = result['damage_quantity'] * result['unit_co2_max']
    result['damage_co2_mean'] = result['damage_quantity'] * result['unit_co2_mean']

    print("Aggregating results...")
    data = result.groupby(['run', 'plan_id', 'sqft', 'num_floors', 'rs_means_cost', 'flood_depth'], observed=True).agg(
        sum_damage_triang = ('damage_cost_triang', 'sum'),
        sum_damage_potential = ('damage_cost_potential', 'sum'),
        sum_damage_min = ('damage_cost_min', 'sum'),
        sum_damage_max = ('damage_cost_max', 'sum'),
        sum_damage_mean = ('damage_cost_mean', 'sum'),
        sum_co2_triang = ('damage_co2_triang', 'sum'),
        sum_co2_min = ('damage_co2_min', 'sum'),
        sum_co2_max = ('damage_co2_max', 'sum'),
        sum_co2_mean = ('damage_co2_mean', 'sum')
    ).reset_index()


    print("Preparing results for plotting...")
    data['damage_pct_triang'] = data['sum_damage_triang'] / data['sum_damage_potential']
    data['damage_pct_rs'] = data['sum_damage_triang'] / data['rs_means_cost']
    data['co2_cost'] = data['sum_co2_triang'] * 0.19
    data['co2_cost_pct'] = data['co2_cost'] / data['rs_means_cost']

    data['occtype'] = "RES1-" + data['num_floors'].astype(str) + "S"

    dd_curves = data.groupby(['occtype', 'flood_depth']).agg(
        mean_dmg_triang = ('sum_damage_triang', 'mean'),
        std_dmg_triang = ('sum_damage_triang', 'std'),
        mean_dmg_pct_triang = ('damage_pct_triang', 'mean'),
        std_dmg_pct_triang = ('damage_pct_triang', 'std'),
        mean_dmg_pct_rs = ('damage_pct_rs', 'mean'),
        std_dmg_pct_rs = ('damage_pct_rs', 'std'),
        mean_co2_triang = ('sum_co2_triang', 'mean'),
        std_co2_triang = ('sum_co2_triang', 'std'),
        mean_co2_cost = ('co2_cost', 'mean'),
        std_co2_cost = ('co2_cost', 'std'),
        mean_co2_cost_pct = ('co2_cost_pct', 'mean'),
        std_co2_cost_pct = ('co2_cost_pct', 'std')
    ).reset_index()

    # test = result.groupby(['component'], observed=True).agg(
    #     mean_damage_triang = ('damage_cost_triang', 'mean'),
    #     mean_co2_triang = ('damage_co2_triang', 'mean'),
    # ).reset_index()


    
    # dd_curves_usace = pd.read_parquet("../data/g2crm_dmg_fns.parquet")

    # dd_curves_usace['source'] = "G2CRM"

    dd_curves['source'] = "Study"
    dd_curves['dmg_mean'] = dd_curves['mean_dmg_pct_rs']
    dd_curves['dmg_low'] = dd_curves['dmg_mean'] - (1.96 * dd_curves['std_dmg_pct_rs'])
    dd_curves['dmg_high'] = dd_curves['dmg_mean'] + (1.96 * dd_curves['std_dmg_pct_rs'])
    dd_curves['co2_mean'] = dd_curves['mean_co2_triang']
    dd_curves['co2_low'] = dd_curves['mean_co2_triang'] - (1.96 * dd_curves['std_co2_triang'])
    dd_curves['co2_high'] = dd_curves['mean_co2_triang'] + (1.96 * dd_curves['std_co2_triang'])
    dd_curves['co2_cost'] = dd_curves['mean_co2_cost']
    dd_curves['co2_cost_pct_mean'] = dd_curves['mean_co2_cost_pct']
    dd_curves['co2_cost_pct_low'] = dd_curves['co2_cost_pct_mean'] - (1.96 * dd_curves['std_co2_cost_pct'])
    dd_curves['co2_cost_pct_high'] = dd_curves['co2_cost_pct_mean'] + (1.96 * dd_curves['std_co2_cost_pct'])
    dd_curves['combined_mean'] = dd_curves['dmg_mean'] + dd_curves['co2_cost_pct_mean']
    dd_curves['combined_low'] = dd_curves['dmg_low'] + dd_curves['co2_cost_pct_low']
    dd_curves['combined_high'] = dd_curves['dmg_high'] + dd_curves['co2_cost_pct_high']

    print("Writing MCS results to file...")
    data.to_parquet("../data/mcs_results.parquet")
    print("Writing damage functions to file...")
    dd_curves.to_parquet("../data/study_dmg_fns.parquet")
    
    return


def save_components():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    path = "../data/component_quantities_and_depth_damage.xlsx"

    print("Loading datasets...")
    # cost = load_cost_data(path)
    cost = load_rs_means_cost_data(path)
    co2 = load_co2_data(path)
    plans = pd.read_excel(path, sheet_name="floor_plans")
    plans['rs_means_cost'] = calc_rs_means_cost(
        plans['num_floors'], 
        plans['sqft'], 
        (plans['n_bath1'] + plans['n_bath2'])
    )
    plan = parse_floorplan(plans.copy(deep=True).iloc[0])

    components = plan.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')
    
    components = components.loc[
        components.component_type == "structure", 
        [
            'component_x', 'unit', 'unit_cost_mean', 'min', 'max', 'mode',
            'unit_cost_min', 'unit_cost_max', 'unit_co2_mean', 'unit_co2_min',
            'unit_co2_max'
        ]
    ]
    # print(components)

    components.to_parquet("../data/components.parquet")

if __name__ == "__main__":
    save_components()
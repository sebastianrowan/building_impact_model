from calculations import *
from utils import *
from visualizations import *
from parse import *

from scipy.stats import triang
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

MIN_DEPTH = -4
MAX_DEPTH = 24
STEP = 0.1
N = 25
SEED = 521871
RNG = np.random.default_rng(seed = SEED)

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # print(os.getcwd())
    path = "../../data/component_quantities_and_depth_damage.xlsx"

    cost = load_cost_data(path)
    
    co2 = load_co2_data(path)

    plans = pd.read_excel(path, sheet_name="floor_plans")

    plans = plans.loc[pd.notna(plans['ridge_height'])]

    plan0 = plans.iloc[0]
    plans = plans.iloc[1:]

    parsed_plans = parse_floorplan(plan0)

    for index, plan in plans.iterrows():
        x = parse_floorplan(plan)
        parsed_plans = pd.concat([parsed_plans, x])

    

    components = parsed_plans.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    components = components[components['component_type'] == "structure"]


    simulations = generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N) 

    check_col = np.where(simulations['max'] <= simulations['min'], True, False)
    simulations['check_col'] = check_col

    result = flood_structure(simulations)

    result['unit_cost_triang'] = calc_unit_cost_co2_triang(
        RNG,
        result['unit_cost_min'],
        result['unit_cost_max'],
        result['unit_cost_mean']
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


    data = result.groupby(['run', 'plan_id', 'sqft', 'num_floors', 'nbed', 'nbath', 'flood_depth'], observed=True).agg(
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

    data['rs_means_cost'] = (data['sqft'] * 2035.37 * data['sqft'].pow(-0.368811) * data['num_floors'].pow(0.047264)) + (8047 * (data['nbath'] -1))

    data['damage_pct_triang'] = data['sum_damage_triang'] / data['sum_damage_potential']
    data['damage_pct_rs'] = data['sum_damage_triang'] / data['rs_means_cost']

    data['occtype'] = "RES1-" + data['num_floors'].astype(str) + "S"

    dd_curves = data.groupby(['occtype', 'flood_depth']).agg(
        mean_dmg_triang = ('sum_damage_triang', 'mean'),
        std_dmg_triang = ('sum_damage_triang', 'std'),
        mean_dmg_pct_triang = ('damage_pct_triang', 'mean'),
        std_dmg_pct_triang = ('damage_pct_triang', 'std'),
        mean_dmg_pct_rs = ('damage_pct_rs', 'mean'),
        std_dmg_pct_rs = ('damage_pct_rs', 'std'),
        mean_co2_triang = ('sum_co2_triang', 'mean'),
        std_co2_triang = ('sum_co2_triang', 'std')
    ).reset_index()


    # data.to_parquet("data.parquet")
    dd_curves_usace = pd.read_parquet("../../data/usace_res1_depth_dmg.parquet")

    dd_curves_usace['source'] = "USACE"
    dd_curves_usace['dmg_std'] = 0

    dd_curves['source'] = "Study"
    dd_curves['dmg'] = dd_curves['mean_dmg_pct_rs']
    dd_curves['dmg_std'] = dd_curves['std_dmg_pct_rs']

    dd_curves_combined = pd.concat([
        dd_curves[['source', 'occtype', 'flood_depth', 'dmg', 'dmg_std']],
        dd_curves_usace[['source', 'occtype', 'flood_depth', 'dmg', 'dmg_std']]
    ])

    dd_curves_combined['ci_95_low'] = dd_curves_combined['dmg'] - (1.96 * dd_curves_combined['dmg_std'])
    dd_curves_combined['ci_95_high'] = dd_curves_combined['dmg'] + (1.96 * dd_curves_combined['dmg_std'])

    sns.set_style("darkgrid")

    # fig, ax = plt.subplots(1,1)
    # sns.scatterplot(
    #     data = data,
    #     x = 'rs_means_cost',
    #     y = 'sum_damage_potential'
    # )
    # plt.show()
    # return

    fig, axes = plt.subplots(1, 2)

    d1 = dd_curves_combined.loc[dd_curves_combined["occtype"] == "RES1-1S"]
    d1a = d1.loc[d1['source'] == "Study"]
    d2 = dd_curves_combined.loc[dd_curves_combined["occtype"] == "RES1-2S"]
    d2a = d2.loc[d2['source'] == "Study"]

    sns.lineplot(
        data = d1,
        x = "flood_depth",
        y = "dmg",
        hue = "source",
        ax = axes[0]
    )

    
    axes[0].fill_between(d1a['flood_depth'], d1a['ci_95_low'], d1a['ci_95_high'], alpha = 0.3)

    sns.lineplot(
        data = d2,
        x = "flood_depth",
        y = "dmg",
        hue = "source",
        ax = axes[1]
    )

    axes[1].fill_between(d2a['flood_depth'], d2a['ci_95_low'], d2a['ci_95_high'], alpha = 0.3)

    axes[0].set_title("RES1-1S")
    axes[1].set_title("RES1-2S")


    for ax in axes.flat:
        ax.set(xlabel = "Flood Depth (ft)", ylabel = "Loss Ratio")
        ax.label_outer()

    plt.show()

if __name__ == "__main__":
    main()
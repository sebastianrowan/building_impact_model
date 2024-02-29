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

MIN_DEPTH = -4
MAX_DEPTH = 32
STEP = 1
N = 1
SEED = 521871
RNG = np.random.default_rng(seed = SEED)

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    path = "../data/component_quantities_and_depth_damage.xlsx"
    cost = load_rs_means_cost_data(path)
    
    co2 = load_co2_data(path)

    plans = pd.read_excel(path, sheet_name="floor_plans")
    plans['rs_means_cost'] = calc_rs_means_cost(
            plans['num_floors'], 
            plans['sqft'], 
            (plans['n_bath1'] + plans['n_bath2'])
        )
    
    plan0 = plans.copy(deep=True).iloc[0]
    parsed_plans = parse_floorplan(plan0)

    components = parsed_plans.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    components = components[components['component_type'] == "structure"]

    simulations = generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N) 
    result = flood_structure2(simulations)

    print(result)
    print(result.columns)

    result = result[[
        'run', 'flood_depth', 'component_x', 'component_type', 'unit',
        'min', 'max', 'mode', 'total_cost_mean', 'total_cost_sd',
        'unit_co2_mean', 'unit_co2_sd', 'fragility'
    ]]

    result.to_parquet("../data/fragility_table.parquet")
    


def plot_triang_cdf(*cdf_params):
    fig, ax = plt.subplots(1, 1)
    x = np.linspace(-4, 20, 100)

    for cdf in cdf_params:
        l = cdf[0]
        s = cdf[1] - cdf[0]
        c = (cdf[2] - cdf[0])/s
        
        y = triang.cdf(x, c, l, s)
        ax.plot(x, y)

    # plt.show()
    plt.savefig("plot_5ft_hist.png")


def plot_depth_damage(result):
    fig, [ax1, ax2] = plt.subplots(2, 1)

    sns.scatterplot(data=result, x = 'flood_depth', y = 'sum_damage_triang', s=1, marker=',', color='#666666', alpha = 0.1, ax=ax1)

    sns.scatterplot(data=result, x = 'flood_depth', y = 'sum_co2_triang', s=1, marker=',', color='#666666', alpha = 0.1, ax=ax2)

    plt.tight_layout()
    # plt.show()



def plot_depth_hist(result, depth):
    data = result[abs(result['flood_depth']-depth)<0.09]

    x = data['flood_depth'].unique()
    print(x)
    fig, [ax1, ax2] = plt.subplots(2, 1)

    sns.histplot(data = data, x = 'sum_damage_triang', ax=ax1)
    ax1.set(
        xlabel = "Damage Cost ($)"
    )

    sns.histplot(data = data, x = 'sum_co2_triang', ax=ax2)
    ax2.set(
        xlabel = "GHG Emissions (kg CO2 equivalents)"
    )

    plt.tight_layout()
    # plt.show()
    plt.savefig("plot_5ft_hist.png")


if __name__ == "__main__":
    main()
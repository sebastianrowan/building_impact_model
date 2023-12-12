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
N = 1
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

    plan0 = plans.iloc[[0]]

    parsed_plans = parse_floorplan(plan0)

    components = parsed_plans.merge(cost, how = 'left', left_on = 'component_join', right_on = 'component')
    components = components.merge(co2, how = 'left', left_on = 'component_join', right_on = 'component')

    components = components[components['component_type'] == "structure"]


    simulations = generate_simulations(components, MIN_DEPTH, MAX_DEPTH, STEP, N) 

    check_col = np.where(simulations['max'] <= simulations['min'], True, False)
    simulations['check_col'] = check_col

    result = flood_structure(simulations)

    x = result.loc[abs(simulations['flood_depth'] - 13.5) < 0.01]
    # print(x[['component_x', 'component_join', 'quantity', 'unit_cost_mean', 'damage_quantity']])
    # print(parsed_plans[['roof_length', 'roof_pitch', 'roof_height', 'ridge_height', 'roof_area']])

if __name__ == "__main__":
    main()
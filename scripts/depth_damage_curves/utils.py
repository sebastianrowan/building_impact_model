import numpy as np
import pandas as pd
import timeit
from parse import *
import os

def generate_simulations(components, min, max, d, i):
    depths = generate_floods(min, max, d, i)
    return(depths.merge(components, how = 'cross'))    


def generate_floods(min, max, d, i):
    # np.random.seed(1234)
    x = np.arange(i)
    y = np.arange(min, max, d)
    z = np.array(np.meshgrid(x, y)).T.reshape(-1, 2)
    floods = pd.DataFrame(z, columns=["run", "flood_depth"])
    return(floods)


def load_cost_data(path):
    cost = pd.read_excel(path, sheet_name="Cost Data")

    cost['total_cost'] = cost['unit_cost'] + cost['labor_unit_cost']
    
    cost = cost.groupby(['component', 'functional_unit'], as_index=False).agg(
        unit_cost_mean = ('total_cost', 'mean'),
        unit_cost_sd = ('total_cost', 'std'),
        unit_cost_min = ('total_cost', 'min'),
        unit_cost_max = ('total_cost', 'max')
    )

    cost['unit_cost_sd'] = cost['unit_cost_sd'].fillna(0)
    cost['unit_cost_max'] = cost['unit_cost_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    return(cost)


def load_co2_data(path):
    co2 = pd.read_excel(path, sheet_name="All LCA Data")

    co2 = co2.groupby(['component', 'functional_unit'], as_index=False).agg(
        unit_co2_mean = ('kg_co2e_fu', 'mean'),
        unit_co2_sd = ('kg_co2e_fu', 'std'),
        unit_co2_min = ('kg_co2e_fu', 'min'),
        unit_co2_max = ('kg_co2e_fu', 'max')
    )

    co2['unit_co2_sd'] = co2['unit_co2_sd'].fillna(0)
    co2['unit_co2_max'] = co2['unit_co2_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    return(co2)


def timer():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    path = "../../data/House Plans/component_quantities_and_depth_damage.xlsx"

    plans = pd.read_excel(path, sheet_name="floor_plans")
    components = parse_floorplan(plans.iloc[0].copy(deep=True))
    components['damage_quantity'] = 0

    x = timeit.timeit(lambda: generate_floods(0, 20, .1, 100000), number = 10)
    y = timeit.timeit(lambda: generate_floods(0, 20, .1, 10), number = 100000)
    
    print(x)
    print(y)


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    timer()


if __name__ == "__main__":
    main()
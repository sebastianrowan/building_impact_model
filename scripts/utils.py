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

    cost['total_cost'] = cost['unit_cost']
    
    cost = cost.groupby(['component', 'functional_unit'], as_index=False).agg(
        unit_cost_mean = ('total_cost', 'mean'),
        unit_cost_sd = ('total_cost', 'std'),
        unit_cost_min = ('total_cost', 'min'),
        unit_cost_max = ('total_cost', 'max')
    )

    cost['unit_cost_sd'] = cost['unit_cost_sd'].fillna(0)
    cost['unit_cost_max'] = cost['unit_cost_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    return(cost)

def load_rs_means_cost_data(path):
    cost = pd.read_excel(path, sheet_name="RS Means Cost Data")

    cost = cost.groupby(['component', 'functional_unit'], as_index=False).agg(
        unit_cost_mean = ('unit_cost', 'mean'),
        unit_cost_sd = ('unit_cost', 'std'),
        unit_cost_min = ('unit_cost', 'min'),
        unit_cost_max = ('unit_cost', 'max'),
        total_cost_mean = ('total_cost', 'mean'),
        total_cost_sd = ('total_cost', 'std'),
        total_cost_min = ('total_cost', 'min'),
        total_cost_max = ('total_cost', 'max'),
        total_cost_inc_op_mean = ('total_cost_inc_op', 'mean'),
        total_cost_inc_op_sd = ('total_cost_inc_op', 'std'),
        total_cost_inc_op_min = ('total_cost_inc_op', 'min'),
        total_cost_inc_op_max = ('total_cost_inc_op', 'max'),
        count = ('total_cost', 'count')
    ).reset_index()

    cost['unit_cost_sd'] = cost['unit_cost_sd'].fillna(0)
    cost['total_cost_sd'] = cost['total_cost_sd'].fillna(0)
    cost['total_cost_inc_op_sd'] = cost['total_cost_inc_op_sd'].fillna(0)

    cost.loc[cost['count'] == 1, 'total_cost_min'] = cost.loc[cost['count'] == 1, 'total_cost_mean']*.9
    cost.loc[cost['count'] == 1, 'total_cost_max'] = cost.loc[cost['count'] == 1, 'total_cost_mean']*1.1

    cost['unit_cost_max'] = cost['unit_cost_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    cost['total_cost_max'] = cost['total_cost_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    cost['total_cost_inc_op_max'] = cost['total_cost_inc_op_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    return(cost)


def load_co2_data(path):
    co2 = pd.read_excel(path, sheet_name="All LCA Data")

    co2 = co2.groupby(['component', 'functional_unit'], as_index=False).agg(
        unit_co2_mean = ('kg_co2e_fu', 'mean'),
        unit_co2_sd = ('kg_co2e_fu', 'std'),
        unit_co2_min = ('kg_co2e_fu', 'min'),
        unit_co2_max = ('kg_co2e_fu', 'max'),
        count = ('kg_co2e_fu', 'count')
    ).reset_index()

    co2['unit_co2_sd'] = co2['unit_co2_sd'].fillna(0)
    co2.loc[co2['count'] == 1, 'unit_co2_min'] = co2.loc[co2['count'] == 1, 'unit_co2_mean']*.9
    co2.loc[co2['count'] == 1, 'unit_co2_max'] = co2.loc[co2['count'] == 1, 'unit_co2_mean']*1.1


    co2['unit_co2_max'] = co2['unit_co2_max'] + 0.000001 # Negligible difference that prevents divide by 0 error in triangular distribution calculations
    return(co2)


def main():
    print("Whoops!")


if __name__ == "__main__":
    main()
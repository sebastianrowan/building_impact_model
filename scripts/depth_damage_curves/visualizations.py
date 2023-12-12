'''
Functions for creating visualizations of results and methods
'''

import numpy as np
import pandas as pd
from scipy.stats import triang
import seaborn as sns
import matplotlib.pyplot as plt
import os

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    
    result = pd.read_parquet("results.parquet")
    plot_depth_hist(result, 5)


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
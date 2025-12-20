import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    res_path = "../results/mcs_res1-all_10iter_specific.parquet"
    results = pd.read_parquet(res_path)
    results['pct_dmg'] = results['sum_damage']/results['rs_means_cost']
    

    run0 = results.loc[results['run'] == 0]
    plan0 = results.loc[results['plan_id']=='11700HZ']

    fig, ax = plt.subplots(1,2)

    sns.scatterplot(run0, x = 'flood_depth', y = 'pct_dmg', hue='plan_id', ax=ax[0])
    sns.scatterplot(plan0, x = 'flood_depth', y = 'pct_dmg', hue='run', ax=ax[1])
    plt.show()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
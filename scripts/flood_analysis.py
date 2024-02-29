import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import seaborn as sns
import pygris as pg

SEED = 521871
RNG = np.random.default_rng(seed = SEED)

def building_counts():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    nsi = gpd.read_parquet("../data/nsi_flood_depths_geo.parquet")
    nsi['occ'] = nsi['occtype'].str[:7]
    nsi = nsi.loc[nsi['occ'].isin(['RES1-1S', 'RES1-2S'])]
    region_occ = nsi.groupby(['region', 'occ']).agg(
        count = ('fid', 'count')
    ).reset_index()

    region_occ['region'] = region_occ['region'].str.replace("burlington_davenport", "Burlington-Davenport")
    region_occ['region'] = region_occ['region'].str.replace("paducah_cairo", "Paducah-Cairo")
    region_occ['occ'] = region_occ['occ'].str.replace("RES1-1S", "One-Story")
    region_occ['occ'] = region_occ['occ'].str.replace("RES1-2S", "Two-Story")
    region_occ.to_parquet("../data/region_bldg_count.parquet")


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    dd_curves = pd.read_parquet("../data/study_dmg_fns.parquet")
    dd_curves["flood_depth"] = dd_curves['flood_depth'].round(1)

    nsi = gpd.read_parquet("../data/nsi_flood_depths_geo.parquet")
    nsi = nsi[['fid', 'bid', 'GEOID', 'region', 'occtype', 'val_struct', 'val_cont', 'height_ffe_avg_current_100year', 'geometry']]

    nsi['height_ffe_avg_current_100year'] = np.maximum(-4, nsi['height_ffe_avg_current_100year'])

    nsi['occ'] = nsi['occtype'].str[:7]

    x = nsi.loc[nsi['occ'].isin(['RES1-1S', 'RES1-2S'])]

    

    x = pd.merge(x, dd_curves, 
                 left_on = ['occ', 'height_ffe_avg_current_100year'], 
                 right_on = ['occtype', 'flood_depth'],
                 how = 'left')

    # x = nsi[nsi['height_ffe_avg_current_100year'] > 1].head(25)
    x['dmg_calc_mean'] = x['val_struct'] * x['dmg_mean']
    x['dmg_calc_low'] = x['val_struct'] * x['dmg_low']
    x['dmg_calc_high'] = x['val_struct'] * x['dmg_high']



    
    # x = x.loc[(x['dmg_calc_low'] > 0)]

    tract_dmg = x.groupby(['GEOID', 'region']).agg(
        dmg_mean_sum = ('dmg_calc_mean', 'sum'),
        dmg_low_sum = ('dmg_calc_low', 'sum'),
        dmg_high_sum = ('dmg_calc_high', 'sum'),
        co2_mean_sum = ('co2_mean', 'sum'),
        co2_low_sum = ('co2_low', 'sum'),
        co2_high_sum = ('co2_high', 'sum')
    ).reset_index()

    tract_dmg['pct_change_low'] = (((tract_dmg['co2_low_sum']*.19) + tract_dmg['dmg_low_sum']) / tract_dmg['dmg_low_sum'])
    tract_dmg['pct_change_high'] = (((tract_dmg['co2_high_sum']*.19) + tract_dmg['dmg_high_sum']) / tract_dmg['dmg_high_sum'])
    tract_dmg['pct_change_mean'] = (((tract_dmg['co2_mean_sum']*.19) + tract_dmg['dmg_mean_sum']) / tract_dmg['dmg_mean_sum'])

    tracts = gpd.read_parquet("../data/region_tracts.parquet")

    tracts = pd.merge(
        tracts, 
        tract_dmg, 
        left_on = 'GEOID', 
        right_on = 'GEOID',
        how = 'left'
    )

    region_occ = x.groupby(['region', 'occ']).agg(
        dmg_mean_sum = ('dmg_calc_mean', 'sum'),
        dmg_low_sum = ('dmg_calc_low', 'sum'),
        dmg_high_sum = ('dmg_calc_high', 'sum'),
        co2_mean_sum = ('co2_mean', 'sum'),
        co2_low_sum = ('co2_low', 'sum'),
        co2_high_sum = ('co2_high', 'sum'),
        count = ('dmg_calc_mean', 'count')
    ).reset_index()

    region = x.groupby(['region']).agg(
        dmg_mean_sum = ('dmg_calc_mean', 'sum'),
        dmg_low_sum = ('dmg_calc_low', 'sum'),
        dmg_high_sum = ('dmg_calc_high', 'sum'),
        co2_mean_sum = ('co2_mean', 'sum'),
        co2_low_sum = ('co2_low', 'sum'),
        co2_high_sum = ('co2_high', 'sum')
    ).reset_index()

    region['pct_change_low'] = (((region['co2_low_sum']*.19) + region['dmg_low_sum']) / region['dmg_low_sum'])
    region['pct_change_high'] = (((region['co2_high_sum']*.19) + region['dmg_high_sum']) / region['dmg_high_sum'])
    region['pct_change_mean'] = (((region['co2_mean_sum']*.19) + region['dmg_mean_sum']) / region['dmg_mean_sum'])

    
    region.to_parquet("../data/region_results.parquet")
    tracts.to_parquet("../data/tract_results.parquet")

    
  
def get_tracts():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    nsi = gpd.read_parquet("../data/nsi_flood_depths_geo.parquet")
    nsi = nsi[['fid', 'bid', 'GEOID', 'region', 'occtype', 'val_struct', 'val_cont', 'height_ffe_avg_current_100year', 'geometry']]

    fips = nsi['GEOID'].unique()
    fips_st = nsi['GEOID'].str[:2].unique()

    tracts = pg.tracts(state = "17", cb = True, cache = True)

    for f in fips_st[1:]:
        t = pg.tracts(state = str(f), cb = True, cache = True)
        tracts = pd.concat([tracts, t])

    print(tracts.shape)
    tracts = tracts.loc[tracts['GEOID'].isin(fips)]
    
    tracts.to_parquet("../data/region_tracts.parquet")
 

if __name__ == "__main__":
    building_counts()
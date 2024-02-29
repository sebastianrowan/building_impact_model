import json
import numpy as np
import pandas as pd
import os
# FEMA PFRA: "Preliminary Flood Risk Assessment"

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    json_path = "../data/occtypes_go_consequences.json"

    with open(json_path, "r") as j:
        df_json = json.loads(j.read())

    print(df_json['occupancytypes'].keys())
    print(df_json['occupancytypes']['SFR1-B']['componentdamagefunctions']['structure']['damagefunctions'].keys())
    return
    
    

    df1 = df_json['occupancytypes']['RES1-1SWB']['componentdamagefunctions']['structure']['damagefunctions']['default']
    df2 = df_json['occupancytypes']['RES1-2SWB']['componentdamagefunctions']['structure']['damagefunctions']['default']

    print(df1)
    return

    means1 = []
    lows1 = []
    highs1 = []
    for y in df1['damagefunction']['ydistributions']:
        mean = y['parameters']['value']
        # low = mean - (1.96 * y['parameters']['standarddeviation'])
        # high = mean + (1.96 * y['parameters']['standarddeviation'])
        low, high = mean, mean
        means1.append(mean * 0.01)
        lows1.append(low * 0.01)
        highs1.append(high * 0.01)

    res1_1s = pd.DataFrame(data = {
        'flood_depth': df1['damagefunction']['xvalues'],
        'dmg_mean': means1,
        'dmg_low': lows1,
        'dmg_high': highs1
    })
    res1_1s['occtype'] = "RES1-1S"
    res1_1s['source'] = "GO Consequences: EGM"

    means2 = []
    lows2 = []
    highs2 = []
    for y in df2['damagefunction']['ydistributions']:
        mean = y['parameters']['value']
        # low = mean - (1.96 * y['parameters']['standarddeviation'])
        # high = mean + (1.96 * y['parameters']['standarddeviation'])
        low, high = mean, mean
        means2.append(mean * 0.01)
        lows2.append(low * 0.01)
        highs2.append(high * 0.01)

    res1_1s = pd.DataFrame(data = {
        'flood_depth': df1['damagefunction']['xvalues'],
        'dmg_mean': means1,
        'dmg_low': lows1,
        'dmg_high': highs1
    })
    res1_1s['occtype'] = "RES1-1S"

    res1_2s = pd.DataFrame(data = {
        'flood_depth': df2['damagefunction']['xvalues'],
        'dmg_mean': means2,
        'dmg_low': lows2,
        'dmg_high': highs2
    })
    res1_2s['occtype'] = "RES1-2S"

    dd_curves = pd.concat([res1_1s, res1_2s])
    dd_curves['source'] = "GO Consequences: FEMA PFRA"
    dd_curves = dd_curves[['occtype', 'flood_depth', 'dmg_low', 'dmg_mean', 'dmg_high', 'source']]
    dd_curves.to_parquet("../data/gcs_dmg_fns2.parquet")





if __name__ == "__main__":
    main()
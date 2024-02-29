'''
Functions used in the main model script to calculate material quantities, component failure counts, etc.
'''

import numpy as np
import pandas as pd
from scipy.stats import triang
import sys
import math

def main():
    print("Hello World")

def calc_unit_cost_co2_normal(rng, mean, sd):
    return(rng.normal(mean, sd))

def calc_unit_cost_co2_triang(rng, min, max, mean):
    return(rng.triangular(min, mean, max))


def fail_count_check(n, min, max, mode, depth):
    l = min
    s = max - min
    c = (mode - min) / s
    return(triang.cdf(depth, c, l, s))

def fail_prob(min, max, mode, depth):
    l = min
    s = max - min
    c = (mode - min) / s
    return(triang.cdf(depth, c, l, s))

def fail_count(n, min, max, mode, depth):
    '''
    Calculates the number of components that will fail at a given flood depth using a random binomial distribution f(n, p) where:
      n = total number of given component in structure
      p = probability that component fails at depth at or below given flood depth based on component's triangular distribution CDF
    '''
    l = min
    s = max - min
    c = (mode - min) / s
    try:
        x = np.random.binomial(n, triang.cdf(depth, c, l, s))
    except:
        x = triang.cdf(depth, c, l, s)
        
    return(np.random.binomial(n, triang.cdf(depth, c, l, s)))

def calc_drywall_insulation(quantity, min, mode, max, depth):
    '''
    Calculates the square feet of wall insulation to be replaced
    max = ceiling height
    '''
    d = np.minimum(depth, max)
    y = d * (d > min)
    return((np.maximum(y, ((y > mode) * max))/max)*quantity)

def calc_drywall_insulation_pct(min, mode, max, depth):
    '''
    Calculates the square feet of wall insulation to be replaced
    max = ceiling height
    '''
    d = np.minimum(depth, max)
    y = d * (d > min)
    return(np.maximum(y, ((y > mode) * max))/max)


def calc_roof_area(len, pitch, roof_height, ridge_height, depth):
    d = np.minimum(depth, ridge_height)
    y = (d - roof_height) * (d > roof_height)
    return(np.sqrt(np.square(y) + np.square(y/pitch)) * len * 1.15)


def calc_facade(quantity, min, max, depth):
    '''
    Calculates square feet of facade or exterior wall sheating to be replaced
    '''
    d = np.minimum(depth, max)
    y = np.maximum(d, min)
    return(((y-min)/(max-min)) * quantity)

def calc_facade_pct(min, max, depth):
    '''
    Calculates percent of facade or exterior wall sheating to be replaced
    '''
    d = np.minimum(depth, max)
    y = np.maximum(d, min)
    return(((y-min)/(max-min)))


def flood_structure2(components):
    fc = components[components['failure_calculation'] == 'fail_count'].copy(deep=True)
    dw = components[components['failure_calculation'] == 'calc_drywall_insulation'].copy(deep=True)
    fd = components[components['failure_calculation'] == 'calc_facade'].copy(deep=True)


    fc['fragility'] = fail_prob(
        fc['min'],
        fc['max'],
        fc['mode'],
        fc['flood_depth']
    )
    dw['fragility'] = calc_drywall_insulation_pct(
        dw['min'],
        dw['max'],
        dw['mode'],
        dw['flood_depth'] 
    )

    fd['fragility'] = calc_facade_pct(
        fd['min'],
        fd['max'],
        fd['flood_depth']
    )

    return(pd.concat([fc, dw, fd]))

def flood_structure(components):
    fc = components[components['failure_calculation'] == 'fail_count'].copy(deep=True)
    dw = components[components['failure_calculation'] == 'calc_drywall_insulation'].copy(deep=True)
    fd = components[components['failure_calculation'] == 'calc_facade'].copy(deep=True)


    fc['damage_quantity'] = fail_count(
        fc['quantity'],
        fc['min'],
        fc['max'],
        fc['mode'],
        fc['flood_depth']
    )
    dw['damage_quantity'] = calc_drywall_insulation(
        dw['quantity'],
        dw['min'],
        dw['max'],
        dw['mode'],
        dw['flood_depth'] 
    )

    fd['damage_quantity'] = calc_facade(
        fd['quantity'],
        fd['min'],
        fd['max'],
        fd['flood_depth']
    )

    return(pd.concat([fc, dw, fd]))

def calc_rs_means_cost(floors: int, sqft: int, baths):
    '''
    Estimate total building construction cost from components using tables
    from "Square Foot Costs with RSMeans Data" (The Gordian Group Inc., 2021).

    ###
    Linear regression performed in R:
    Call:
    lm(formula = log(x$cost) ~ log(x$sqft) + log(x$floors))

    Residuals:
        Min         1Q     Median         3Q        Max 
    -0.0179803 -0.0049245  0.0006848  0.0041219  0.0192348 

    Coefficients:
                Estimate Std. Error t value Pr(>|t|)    
    (Intercept)    7.618432   0.036065 211.244  < 2e-16 ***
    log(x$sqft)   -0.368811   0.004903 -75.214  < 2e-16 ***
    log(x$floors)  0.047264   0.006778   6.973 1.21e-06 ***
    ---
    Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1

    Residual standard error: 0.01054 on 19 degrees of freedom
    Multiple R-squared:  0.9968,	Adjusted R-squared:  0.9965 
    F-statistic:  2950 on 2 and 19 DF,  p-value: < 2.2e-16
    ###

    Additional full bath: $8047
    Additional half bath: $4627

    The Gordian Group Inc. (2021). Square Foot Costs with RSMeans Data: 2022
    (43rd annual edition). Gordian.
    '''

    intercept = math.exp(7.618432)
    sqft_coef = -0.368811
    floor_coef = 0.047264
    bath = 8047

    cost = (sqft * intercept * sqft.pow(sqft_coef) * floors.pow(floor_coef)) + (bath * (baths -1))
    return(cost)



if __name__ == "__main__":
    main()
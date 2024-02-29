'''
Functions to parse data stored in files into dataframes for analysis
'''
import math
import pandas as pd
from calculations import *

def parse_floorplan(plan):
    # component_df rows as tuples:
    # copy and paste from excel
    # (component, type, unit, failure_calculation, quantity, min, max, mode, slab, pier, crawl, basement, mobile, naics_code, ecoinvent_id, ecoinvent_co2e, useeio_co2e),
    columns = ('component', 'component_type', 'unit', 'unit_cost', 'failure_calculation', 'quantity', 'min', 'max', 'mode', 'slab', 'pier', 'crawl', 'basement', 'mobile', 'naics_code', 'ecoinvent_id', 'ecoinvent_co2e', 'useeio_co2e')

    plan['roof_area'] = calc_roof_area(plan['roof_length'], plan['roof_pitch'], plan['roof_height'], plan['ridge_height'], 999)

    #TODO: Consider converting this to yaml for easier reading and editing.
    components = [
        ('Underfloor Insulation', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], -0.5, -0.499, -0.5, 'No', 'Yes', 'Yes', 'No', 'No', 0, 0, 0, 0),

        ('Underfloor Ductwork', 'structure', 'ft', 0, 'fail_count',  plan['floor_area1']/10, -0.5, -0.499, -0.5, 'No', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Heating/Cooling Unit or HVAC', 'structure', 'ea', 0, 'fail_count', 1, -1, 1, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Wood Subfloor', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], 0, 0.01, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Finished Floor Underlayment', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], 0, 0.01, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Finished Floor', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], 0, 0.01, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bottom Cabinets', 'structure', 'ea', 0, 'fail_count', 1, 0, 1, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Top Cabinets', 'structure', 'ea', 0, 'fail_count', 1, 4.5, 5.5, 4.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bathroom Bottom Cabinets', 'structure', 'ea', 0, 'fail_count', plan['n_bath1'], 0, 1, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bathroom Top Cabinets', 'structure', 'ea', 0, 'fail_count', plan['n_bath1'], 4.5, 5.5, 4.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Counter Tops', 'structure', 'ea', 0, 'fail_count', 1, 0, 1, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Water Heater', 'structure', 'ea', 0, 'fail_count', 1, 0, 2, 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Wall Paint - Interior', 'structure', 'sqft', 0, 'fail_count',  plan['int_wall_len1']*plan['ceiling_height1'], 0.5, 0.51, 0.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Wall Paint - Exterior', 'structure', 'sqft', 0, 'fail_count',  plan['ext_wall_len1']*plan['ceiling_height1']*plan['num_floors'], 0, 0.01, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Exterior Doors', 'structure', 'ea', 0, 'fail_count',  plan['n_ext_door1'], 1, 4, 2, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Interior Doors', 'structure', 'ea', 0, 'fail_count',  plan['n_int_door1'], 0, 2, 0.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Sheetrock/drywall', 'structure', 'sqft', 0, 'calc_drywall_insulation',  plan['int_wall_len1']*plan['ceiling_height1'], 0, 4, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 'https://v391.ecoquery.ecoinvent.org/Details/PDF/9cd6e04e-a5d9-4b1e-a1e4-6e21e959b4cf/290c1f85-4cc4-4fa1-b0c8-2cb7f4276dce', 0.29, 0),
        ('Wall Insulation', 'structure', 'sqft', 0, 'calc_drywall_insulation',  plan['ext_wall_len1']*plan['ceiling_height1'], 0, 4, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Baseboard', 'structure', 'ft', 0, 'fail_count',  plan['int_wall_len1'], 0, 0.01, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Refrigerator', 'structure', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Dishwasher', 'structure', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Microwave', 'structure', 'ea', 0, 'fail_count', 1, 3, 5, 3, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Clothes Washer', 'structure', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Clothes Dryer', 'structure', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Oven/stove', 'structure', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Range hood', 'structure', 'ea', 0, 'fail_count', 1, 4.5, 6, 5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bottom Outlets', 'structure', 'ea', 0, 'fail_count',  math.ceil(plan['int_wall_len1']/12), 1, 2, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Top Outlets', 'structure', 'ea', 0, 'fail_count',  plan['n_bath1'] + 3, 3, 4, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Light Switches', 'structure', 'ea', 0, 'fail_count',  2 * (plan['n_int_door1'] + plan['n_ext_door1']), 3, 4, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Electrical Panel', 'structure', 'ea', 0, 'fail_count', 1, 3, 5, 4.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Windows', 'structure', 'ea', 0, 'fail_count',  plan['n_window1'], 2, 20, 5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Ceiling Paint', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], plan['ceiling_height1'], plan['ceiling_height1'] + 0.01, plan['ceiling_height1'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Ceiling', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area1'], plan['ceiling_height1'], plan['ceiling_height1'] + 0.01, plan['ceiling_height1'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Ceiling Insulation', 'structure', 'sqft', 0, 'fail_count',  (plan['floor_area1'] if plan['num_floors'] == 1 else 0), plan['ceiling_height1'], plan['ceiling_height1'] + 0.01, plan['ceiling_height1'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Roof Cover Underlayment', 'structure', 'sqft', 0, 'fail_count',  plan['roof_area'], plan['roof_height'], plan['roof_height']+.01, plan['roof_height'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Roof Cover', 'structure', 'sqft', 0, 'fail_count',  plan['roof_area'], plan['roof_height'], plan['roof_height']+.01, plan['roof_height'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Roof Cover and underlayment combined', 'structure', 'sqft', 0, 'fail_count',  plan['roof_area'], plan['roof_height'], plan['roof_height']+.01, plan['roof_height'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Roof Sheathing', 'structure', 'sqft', 0, 'calc_facade',  plan['roof_area'], plan['roof_height'], plan['ridge_height'], plan['roof_height'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),

        ('Facade', 'structure', 'sqft', 0, 'calc_facade',  plan['ext_wall_len1']*plan['ceiling_height1']*plan['num_floors'], 0, plan['roof_height'], 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Exterior Wall Sheathing', 'structure', 'sqft', 0, 'calc_facade',  plan['ext_wall_len1']*plan['ceiling_height1']*plan['num_floors'], 0, plan['roof_height'], 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bookcase', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'] + 1, 0, 6, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Books', 'contents', 'ea', 0, 'fail_count', 103, 0, 20, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Entertainment Center', 'contents', 'ea', 0, 'fail_count', 1, 0, 2, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Couch/Sofa', 'contents', 'ea', 0, 'fail_count', 1, 0, 0.5, 0.25, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Coffee Table/End Table', 'contents', 'ea', 0, 'fail_count', 3, 0, 2, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Lamps', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'] + 3, 0, 2, 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Blinds', 'contents', 'ea', 0, 'fail_count',  plan['n_window1'], 6, 7, 6.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Curtains/Drapes', 'contents', 'ea', 0, 'fail_count',  plan['n_window1'], 0, 8, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('A/V equipment', 'contents', 'ea', 0, 'fail_count', 4, 2, 4, 3, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Television', 'contents', 'ea', 0, 'fail_count', 1, 2, 6, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Dinner Table', 'contents', 'ea', 0, 'fail_count', 1, 2.33, 4, 2.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Dinner Chair', 'contents', 'ea', 0, 'fail_count', 1, 1.5, 3.33, 2, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('China Cabinet/Buffet', 'contents', 'ea', 0, 'fail_count', 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Small Kitchen Appliances', 'contents', 'ea', 0, 'fail_count', 5, 1, 5, 3, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bed Frame', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 1, 2, 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Box Spring and Mattress', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 1, 2, 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bedding', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 1, 2, 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Chest of Drawers/Dresser', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Night stand', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'] + 1, 0.5, 1.5, 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Bedroom Television', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 3, 5, 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Desk', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'], 0, 3, 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Computer', 'contents', 'ea', 0, 'fail_count', 1, 2, 3, 2.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Clothing', 'contents', 'ea', 0, 'fail_count',  100 * (plan['n_bed1'] + 1), 0, 7, 3.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('Towels/Linens', 'contents', 'ea', 0, 'fail_count',  plan['n_bed1'] * 10, 0, 7, 3.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bed Frame', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Box Spring and Mattress', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bedding', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bedding', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Chest of Drawers/Dresser', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 0.5, plan['ceiling_height1'] + 1 + 1.5, plan['ceiling_height1'] + 1 + 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Night stand', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 0.5, plan['ceiling_height1'] + 1 + 1.5, plan['ceiling_height1'] + 1 + 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bedroom Television', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'],plan['ceiling_height1'] + 1 + 3, plan['ceiling_height1'] + 1 + 5, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Desk', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 3, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Clothing', 'contents', 'ea', 0, 'fail_count',  100 * (plan['n_bed2']), plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 7, plan['ceiling_height1'] + 1 + 3.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Towels/Linens', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'] * 10, plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 7, plan['ceiling_height1'] + 1 + 3.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Lamps', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Blinds', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 6, plan['ceiling_height1'] + 1 + 7, plan['ceiling_height1'] + 1 + 6.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Curtains/Drapes', 'contents', 'ea', 0, 'fail_count',  plan['n_window2'], plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 8, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bookcase', 'contents', 'ea', 0, 'fail_count',  plan['n_bed2'], plan['ceiling_height1'] + 1 + 0, plan['ceiling_height1'] + 1 + 0.5, plan['ceiling_height1'] + 1 + 0, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Windows', 'structure', 'ea', 0, 'fail_count',  plan['n_window2'], plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 20, plan['ceiling_height1'] + 1 + 5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Ceiling', 'structure', 'ea', 0, 'fail_count',  plan['floor_area2'], plan['ceiling_height1'] + 1 + plan['ceiling_height2'], plan['ceiling_height1'] + 1.01 + plan['ceiling_height2'], plan['ceiling_height1'] + 1 + plan['ceiling_height2'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Ceiling Insulation', 'structure', 'ea', 0, 'fail_count',  (plan['floor_area2'] if plan['num_floors'] > 1 else 0), plan['ceiling_height1'] + 1 + plan['ceiling_height2'], plan['ceiling_height1'] + 1.01 + plan['ceiling_height2'], plan['ceiling_height1'] + 1 + plan['ceiling_height2'], 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bottom Outlets', 'structure', 'ea', 0, 'fail_count',  math.ceil(plan['int_wall_len2']/12), plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Top Outlets', 'structure', 'ea', 0, 'fail_count',  plan['n_bath2'], plan['ceiling_height1'] + 1 + 3, plan['ceiling_height1'] + 1 + 4, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Light Switches', 'structure', 'ea', 0, 'fail_count',  2 * (plan['n_int_door2'] + plan['n_ext_door2']), plan['ceiling_height1'] + 1 + 3, plan['ceiling_height1'] + 1 + 4, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Underfloor Ductwork', 'structure', 'ft', 0, 'fail_count',  plan['floor_area2']/10, plan['ceiling_height1'] + 0.5, plan['ceiling_height1'] + 0.51, plan['ceiling_height1'] + 0.5 , 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Wood Subfloor', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1.01, plan['ceiling_height1'] + 1 , 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Finished Floor Underlayment', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1.01, plan['ceiling_height1'] + 1 , 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Finished Floor', 'structure', 'sqft', 0, 'fail_count',  plan['floor_area2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1.01, plan['ceiling_height1'] + 1 , 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bathroom Bottom Cabinets', 'structure', 'ea', 0, 'fail_count',  plan['n_bath2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 2, plan['ceiling_height1'] + 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Bathroom Top Cabinets', 'structure', 'ea', 0, 'fail_count',  plan['n_bath2'], plan['ceiling_height1'] + 1+4.5, plan['ceiling_height1'] + 1 + 5.5, plan['ceiling_height1'] + 1 + 4.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Wall Paint - Interior', 'structure', 'sqft', 0, 'fail_count',  plan['int_wall_len2'] * plan['ceiling_height2'], plan['ceiling_height1'] + 1.5, plan['ceiling_height1'] + 1.51, plan['ceiling_height1'] + 1.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Exterior Doors', 'structure', 'ea', 0, 'fail_count',  plan['n_ext_door2'], plan['ceiling_height1'] + 1 + 1, plan['ceiling_height1'] + 1 + 4, plan['ceiling_height1'] + 1 + 2, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Interior Doors', 'structure', 'ea', 0, 'fail_count',  plan['n_int_door2'] , plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1 + 2, plan['ceiling_height1'] + 1 + 0.5, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Sheetrock/drywall', 'structure', 'sqft', 0, 'calc_drywall_insulation',  plan['int_wall_len2'] * plan['ceiling_height2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1 + 4, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Wall Insulation', 'structure', 'sqft', 0, 'calc_drywall_insulation',  plan['int_wall_len2'] * plan['ceiling_height2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1 + 4, plan['ceiling_height1'] + 1 + 4, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0),
        ('2nd Floor Baseboard', 'structure', 'ft', 0, 'fail_count',  plan['int_wall_len2'], plan['ceiling_height1'] + 1, plan['ceiling_height1'] + 1 + .01, plan['ceiling_height1'] + 1, 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 0, 0, 0, 0)
    ]
    df = pd.DataFrame(components, columns = columns)
    df['damage_quantity'] = 0
    df['plan_id'] = plan['plan_id']
    df['sqft'] = plan['sqft']
    df['num_floors'] = plan['num_floors']
    df['nbed'] = plan['n_bed1'] + plan['n_bed2']
    df['nbath'] = plan['n_bath1'] + plan['n_bath2']
    df['rs_means_cost'] = plan['rs_means_cost']

    df['component_join'] = df['component'].str.replace("2nd Floor ", "")
    # df[['roof_length', 'roof_pitch', 'roof_height', 'ridge_height', 'roof_area']] = plan[['roof_length', 'roof_pitch', 'roof_height', 'ridge_height', 'roof_area']]

    for col in ['component_type', 'unit', 'failure_calculation', 'slab', 'pier', 'crawl', 'basement', 'mobile']:
        df[col] = df[col].astype('category')
    return(df)

if __name__ == "__main__":
    print("Whoops")
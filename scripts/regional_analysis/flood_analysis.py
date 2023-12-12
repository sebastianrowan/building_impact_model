from datetime import datetime
import pandas as pd
import pyarrow
import geopandas as gpd
import fiona
import rasterio
import requests
from zipfile import ZipFile
import logging
import sys
logging.basicConfig(level=logging.INFO)

# write intermediate datasets to file
WRITE = True
GPKG = "../data/data.GPKG"

def main():
    regions = ["burlington_davenport", "paducah_cairo"]

    for region in regions:
        nsi = download_nsi(region)
        nsi = flood_join(nsi, region)


def download_nsi(region):
    logging.info(f"{datetime.now()}: Begin {region} NSI data download")


    # Check if nsi data already in GPKG
    if(f"{region}_nsi_data" in fiona.listlayers(GPKG)):
        logging.info(f"{region} NSI data already in geopackage. Returning existing layer.")
        return(gpd.read_file(GPKG, layer = f"{region}_nsi_data"))

    extent = gpd.read_file(GPKG, layer = f"{region}_study_region_extent")
    w, s, e, n = extent.geometry.total_bounds

    url = "https://nsi.sec.usace.army.mil/nsiapi/structures"

    logging.info(f"{datetime.now()}: Calling NSI API")
    response = requests.get(url, params = {
        "bbox": f"{w},{s},{w},{n},{e},{n},{e},{s},{w},{s}",
        "fmt": "fc"
    })

    if response.status_code == 200:
        x = response.text

        logging.info(f"{datetime.now()}: Loading API response as geodataframe")
        nsi = gpd.read_file(x, driver = "GeoJSON")
        nsi = nsi[(nsi['st_damcat'] == "RES")]
        out_cols = [
        "fd_id", "bid", "occtype", "sqft", "cbfips","val_struct", "val_cont",
        "ground_elv", "found_type", "found_ht", "pop2amu65", "pop2amo65", "geometry"
        ]

        nsi = nsi[out_cols] # limit columns to speed up write to disk. 

        logging.info(f"{datetime.now()}: Reprojecting NSI data to project crs")
        nsi = nsi.to_crs(4269)
        if WRITE:
            logging.info(f"{datetime.now()}: Writing NSI data to GPKG")
            nsi.to_file(
                GPKG,
                layer=f"{region}_nsi_data",
                driver="GPKG"
            )
        logging.info(f"{datetime.now()}: {region} NSI data download complete")
        return(nsi)
    else:
        msg = f"get_nsi_data({region}: Request returned with status code {response.status_code}."
        logging.error(msg)
        sys.exit()
    
def flood_join(nsi, region):
    logging.info(f"{datetime.now()}: Begin {region} flood depth join")

    times = ["current", "future"]
    levels = ["min", "max", "avg"]
    rps = ["100"]

    if(region == "burlington_davenport"): # This is needed to navigate folder structure of flood tiffs
        domain = 1
    else:
        domain = 2

    tiff_dir = "tiffs" # Flood rasters generated from Autoroute/Floodspreader

    #### Values for test run ####
    tiff_dir = "S:/mrv_future_flooding/mrv_ff_flood_rasters"
    #############################
 
    output_layer = f"{region}_nsi_data_flood_depths"

    nsi["ffe"] = nsi["ground_elv"] + nsi["found_ht"]

    sample_pts = [
        (x, y) for x, y in zip(nsi["geometry"].x, nsi["geometry"].y)
    ]
    
    # Load each flood raster and get depth
    for t in times:
        for level in levels:
            for rp in rps:                
                ### uncomment appropriate line below depending if tifs are in separate folders ###
                #tiff_path = f"{tiff_dir}/D{domain}_{level}_{t}_{rp}yr/D{domain}_{level}_{t}_{rp}yr.tif"
                tiff_path = f"{tiff_dir}/D{domain}_{level}_{t}_{rp}yr.tif"

                flood = rasterio.open(tiff_path)

                logging.info(f"{datetime.now()}: Getting D{domain}_{level}_{t}_{rp}yr flood depths...")
                nsi[f"{level}_{t}_{rp}year_depth"] = [
                    x[0] for x in flood.sample(sample_pts)
                ]
                logging.info(f"{datetime.now()}: Getting D{domain}_{level}_{t}_{rp}yr flood depths complete")
                
                nsi[f"{level}_{t}_{rp}year_elev"] = (
                    nsi["ground_elv"] + nsi[f"{level}_{t}_{rp}year_depth"]
                )

                # set 0ft flood depths and missing data to -999
                nsi[f"{level}_{t}_{rp}year_elev"] = nsi.apply(
                    lambda x: -999 if (
                        x[f"{level}_{t}_{rp}year_depth"] == 0 or\
                        x[f"{level}_{t}_{rp}year_depth"] > 100
                    ) else x[f"{level}_{t}_{rp}year_elev"],
                    axis = 1
                )

                nsi[f"height_ffe_{level}_{t}_{rp}year"] = (
                    nsi[f"{level}_{t}_{rp}year_elev"] - nsi["ffe"]
                )

    logging.info(f"{datetime.now()}: Writing {region} results to GPKG...")
    nsi.to_file(
        GPKG,
        layer = output_layer,
        driver="GPKG"
    )                               
    logging.info(f"{datetime.now()}: {region} flood depth join complete")
    return(nsi)


if __name__ == "__main__":
    main()
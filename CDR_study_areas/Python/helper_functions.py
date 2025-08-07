import geopandas as gpd
import rasterio
import pandas as pd

import zipfile
from rasterio.mask import mask
# import merge
from rasterio.merge import merge
from rasterstats import zonal_stats
import numpy as np
import os
import re
from glob import glob
from shapely.geometry import mapping
from tqdm import tqdm
import matplotlib.pyplot as plt

## Read vector file
main_path = r"C:\Users\Khizer Zakir\OneDrive - Universität Salzburg (1)\phd\CLIMB\Data\dataset\CDR_study_areas"

def read_vector(vector_path, crs = True , drop_columns= True):
    """
    Takes the path of the file, crs, columns to drop to read and print the vector file

    Args:

    vector_path: The path to the 
    """
    vector_path = os.path.join(main_path, vector_path)
    gdf = gpd.read_file(vector_path)
    if crs:
        gdf = gdf.to_crs("EPSG:4326")
    else:
        gdf

    if drop_columns:
        gdf = gdf.drop(columns=["Shape_Leng", "Shape_Area"])

    else:
        gdf

    return gdf

### function to combine csvs

def combine_csvs(directory, output_file):
    """
    Combine multiple CSV files in a directory into a single CSV file.
    
    Args:
        directory: Path to directory containing CSV files or reference path
        output_file: Name of the output combined CSV file
    """
    # Determine the base folder
    if os.path.isfile(directory):
        base_folder = os.path.dirname(directory)
        print(f"Input is a file. Looking for CSVs in parent directory: {base_folder}")
    else:
        base_folder = directory
        print(f"Looking for CSV files in directory: {base_folder}")
    
    # Check if directory exists
    if not os.path.exists(base_folder):
        print(f"Error: Directory {base_folder} does not exist")
        return
    
    # Find CSV files
    csv_files = glob(os.path.join(base_folder, "*.csv"))
    print(f"Found {len(csv_files)} CSV files")
    
    if not csv_files:
        print(f"No CSV files found in {base_folder}")
        print("Available files:")
        all_files = os.listdir(base_folder)
        for f in all_files[:10]:  # Show first 10 files
            print(f"  {f}")
        return
    
    # Read and combine CSV files
    combined_data = []
    successful_reads = 0
    
    for file in tqdm(csv_files, desc="Combining CSVs"):
        try:
            print(f"Reading: {os.path.basename(file)}")
            data = pd.read_csv(file)
            
            if data.empty:
                print(f"  Warning: {file} is empty")
                continue
                
            combined_data.append(data)
            successful_reads += 1
            print(f"  Success: {len(data)} rows, {len(data.columns)} columns")
            
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue
    
    print(f"\nSuccessfully read {successful_reads} out of {len(csv_files)} CSV files")
    
    if not combined_data:
        print("No valid CSV files could be read. Cannot create combined file.")
        return
        
    # Combine dataframes
    try:
        combined_df = pd.concat(combined_data, ignore_index=True)
        output_path = os.path.join(base_folder, output_file)
        combined_df.to_csv(output_path, index=False)
        print(f"Combined {len(csv_files)} CSV files into {output_path}")
        print(f"Final combined file: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        
    except Exception as e:
        print(f"Error combining dataframes: {e}")
        return


    ## function to check flood density

def check_flood_density(flood_dir, gdf, class_vals=[1], region_col='region'):
    """
    For each commune, calculate the density of flood pixels as a percentage.
    Returns flood density for each commune and average density by region.
    
    Args:
        flood_dir: Directory containing flood TIF files
        gdf: GeoDataFrame with communes
        class_vals: Values in raster that indicate flooding (default [1])
        region_col: Column name containing region information or list of specific regions to filter
    
    Returns:
        GeoDataFrame with added 'flood_density' column (percentage)
    """
    flood_files = glob(os.path.join(flood_dir, "**", "*.tif"), recursive=True)
    flood_densities = np.zeros(len(gdf))

    for tif in tqdm(flood_files, desc="Processing flood TIFFs"):
        with rasterio.open(tif) as src:
            for i, row in gdf.iterrows():
                try:
                    geom = [mapping(row.geometry)]
                    out_image, _ = mask(src, geom, crop=True)
                    data = out_image[0]
                    valid_pixels = np.isfinite(data).sum()
                    if valid_pixels == 0:
                        continue
                    flood_pixels = np.isin(data, class_vals).sum()
                    density = (flood_pixels / valid_pixels) * 100
                    # Take maximum density across all flood files for each commune
                    flood_densities[i] = max(flood_densities[i], density)
                except Exception as e:
                    print(f"Error processing {tif} for commune {i}: {e}")

    gdf["flood_density"] = flood_densities
    
    # Handle region filtering and averaging
    if isinstance(region_col, list):
        # Filter to specific regions if list provided
        filtered_gdf = gdf[gdf['region'].isin(region_col)]
        if len(filtered_gdf) > 0:
            regional_avg = filtered_gdf.groupby('region')['flood_density'].mean()
            print(f"\nFlood density for selected regions:")
            for region, avg_density in regional_avg.items():
                print(f"{region}: {avg_density:.2f}%")
        else:
            print("No communes found for the specified regions")
    elif region_col in gdf.columns:
        # Calculate averages for all regions
        regional_avg = gdf.groupby(region_col)['flood_density'].mean()
        print(f"\nFlood density by {region_col}:")
        for region, avg_density in regional_avg.items():
            print(f"{region}: {avg_density:.2f}%")
    
    return gdf

## to check the cell tower density

def cell_tower_zonal(gdf, cell_towers_fp):
    """
    Compute the total number of cell towers within each commune from a raster.
    Each pixel value in the raster should represent the number of towers at that location.
    """
    cell_tower_counts = []
    with rasterio.open(cell_towers_fp) as src:
        # Ensure CRS match
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)
        for _, row in gdf.iterrows():
            geom = [mapping(row.geometry)]
            try:
                out_image, _ = mask(src, geom, crop=True)
                data = out_image[0]
                # Only sum valid pixels (ignore nodata)
                valid_mask = np.isfinite(data)
                count = data[valid_mask].sum()
                cell_tower_counts.append(int(count))
            except Exception as e:
                print(f"Error on polygon: {e}")
                cell_tower_counts.append(0)
    gdf["cell_tower_count"] = cell_tower_counts
    return gdf

### Plotting functions

def plot_communes_categorical(gdf, flag_col):
    """Plot communes with categorical/binary flags"""
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(column=flag_col, ax=ax, legend=True, cmap='RdYlBu_r', edgecolor='black')
    plt.title(f"Communes with {flag_col} Flags")
    plt.show()

def plot_communes_quantiles(gdf, var_col):
    """Plot communes with continuous variable classified into 5 quantile classes"""
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(column=var_col, ax=ax, legend=True, cmap='viridis', 
             scheme='quantiles', k=5, edgecolor='black')
    plt.title(f"Communes - {var_col} (5 Quantile Classes)")
    plt.show()





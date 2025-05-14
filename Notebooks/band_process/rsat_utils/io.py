import os
import glob
import rasterio

def load_band(data_path, suffix):
    """
    Load a single band from a directory.
    Args:
        data_path (str): Path to the directory containing the band files.
        suffix (str): Suffix of the band file to load.
        Returns:
        band_array (numpy.ndarray): The loaded band array.
        band_meta (dict): Metadata of the loaded band.
    """
    if not os.path.isdir(data_path):
        raise NotADirectoryError(f"Provided path {data_path} is not a directory.")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Directory {data_path} does not exist.")
    pattern = os.path.join(data_path, f"*{suffix}.tif")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No file ending with {suffix} found in {data_path}.")
    with rasterio.open(files[0]) as src:
        band_array = src.read(1)
        band_meta = src.meta
        #band_array = scale_to_reflectance(band_array)
    return band_array, band_meta

def scale_to_reflectance(band_array, scale=0.0000275, offset=-0.2):
    return (band_array * scale) + offset

# make a band map dictionary
band_map = {
        "BLUE": "B1",
        "GREEN": "B2",
        "RED": "B3",
        "NIR": "B4",
        "SWIR1": "B5",
        "Thermal": "B6",
        "SWIR2": "B7"}

def load_bands(data_path, band_map=band_map):
    """
    Load multiple bands from a directory.
    Args:
        data_path (str): Path to the directory containing the band files.
        band_map (dict): Dictionary mapping band names to their suffixes.
    Returns:
        bands (dict): Dictionary of loaded band arrays.
        meta (dict): Dictionary of metadata for each band.
    """
    bands = {}
    meta = {}
    for name, suffix in band_map.items():
        bands[name], meta[name] = load_band(data_path, suffix)
        #bands[name] = scale_to_reflectance(bands[name])# scale to reflectance
    return bands, meta

def parse_mtl(mtl_path):
    """
    Parses Landsat MTL file to extract useful constants.
    Returns a dict with keys like RADIANCE_MULT_BAND_10, K1_CONSTANT_BAND_10, etc.
    """
    constants = {}
    with open(mtl_path, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')
                try:
                    value = float(value)
                except ValueError:
                    pass
                constants[key] = value
    return constants

def find_mtl_file(folder):
    """Locate the MTL.txt file in a folder."""
    mtl_files = glob.glob(os.path.join(folder, "*_MTL.txt"))
    if not mtl_files:
        raise FileNotFoundError("MTL.txt file not found in folder.")
    return mtl_files[0]

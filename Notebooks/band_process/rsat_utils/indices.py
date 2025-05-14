import numpy as np
import rasterio
import os
#     Parse the MTL file to extract metadata

def safe_divide(numerator, denominator, eps=1e-10):
    """ Avoid division by zero """
    return numerator / (denominator + eps)

def toa_radiance(thermal_band, ml=0.0003342, al=0.1):
    """
    Convert thermal band DN to TOA radiance.
    Default ml, al values from Landsat 8 metadata (can be overridden).
    """
    return ml * thermal_band + al
import numpy as np

def compute_index(band1, band2=None, index_type="NDVI", extra_bands=None, **kwargs):
    """
    Compute spectral index based on bands.

    Parameters:
    - band1 (ndarray): Primary band.
    - band2 (ndarray): Secondary band, optional for some indices.
    - index_type (str): Type of index to compute.
    - extra_bands (dict): Additional bands required for specific indices.
    - kwargs: Extra arguments like L for SAVI.
    
    Returns:
    - ndarray: Computed index array.
    """
    band1 = band1
    if band2 is not None:
        band2 = band2

    if index_type.upper() == "NDVI":
        return (band1 - band2) / (band1 + band2)
    
    elif index_type.upper() == "SAVI":
        L = kwargs.get("L", 0.5)
        return ((band1 - band2)/ (band1 + band2 + L + 1e-10)) * (1 + L)
    
    elif index_type.upper() == "NDWI":
        return (band1 - band2) / (band1 + band2 + 1e-10)

    elif index_type.upper() == "NDMI":
        return (band1 - band2) / (band1 + band2 + 1e-10)

    elif index_type.upper() == "VCI":
        ndvi = band1
        ndvi_min = kwargs.get("NDVI_min", np.nanmin(ndvi))
        ndvi_max = kwargs.get("NDVI_max", np.nanmax(ndvi))
        return ((ndvi - ndvi_min) / (ndvi_max - ndvi_min + 1e-10)) * 100

    elif index_type.upper() == "NVWI":  # NIR / (NIR + GREEN)
        green = extra_bands.get("GREEN")
        return band1 / (band1 + green + 1e-10)

    elif index_type.upper() == "VSWI":  # NDVI / SWIR
        return band1 / (band2 + 1e-10)

    elif index_type.upper() == "NVSWSI":  # (NIR - SWIR2) / (NIR + SWIR2)
        return (band1 - band2) / (band1 + band2 + 1e-10)

    else:
        raise ValueError(f"Unsupported index type: {index_type}")
    # Add more indices as needed
    
def compute_lst(data_folder, band_map, mtl_dict, ndvi=None, eps=None):
    """
    Compute LST using Landsat thermal band and metadata.

    Parameters:
    - data_folder (str): Path to the folder containing the imagery.
    - band_map (dict): Dictionary mapping band names to filenames.
    - mtl_dict (dict): Parsed metadata dictionary from MTL file.
    - ndvi (ndarray): Optional NDVI array for emissivity calculation.
    - eps (float): Optional emissivity override.

    Returns:
    - ndarray: Land Surface Temperature in Celsius.
    """
    # Find thermal band filename
    thermal_filename = band_map.get("Thermal")
    if thermal_filename is None:
        raise ValueError("Thermal band not found in band_map.")

    # Extract band number (e.g., 'B6.TIF' → 6)
    band_number = ''.join(filter(str.isdigit, thermal_filename))

    # Load thermal band
    thermal_path = os.path.join(data_folder, thermal_filename)
    with rasterio.open(thermal_path) as src:
        thermal_dn = src.read(1).astype(float)

    # Get radiometric and thermal constants from MTL
    ml = float(mtl_dict.get(f"RADIANCE_MULT_BAND_{band_number}", 0.0003342))
    al = float(mtl_dict.get(f"RADIANCE_ADD_BAND_{band_number}", 0.1))
    k1 = float(mtl_dict.get(f"K1_CONSTANT_BAND_{band_number}", 774.89))
    k2 = float(mtl_dict.get(f"K2_CONSTANT_BAND_{band_number}", 1321.08))

    # Convert to TOA Radiance
    rad = toa_radiance(thermal_dn, ml, al)

    # Estimate or use given emissivity
    if eps is None and ndvi is not None:
        pv = ((ndvi - ndvi.min()) / (ndvi.max() - ndvi.min())) ** 2
        eps = 0.004 * pv + 0.986
    elif eps is None:
        eps = 0.98

    # Compute LST
    temp_kelvin = k2 / (np.log((k1 / rad) + 1))
    lst_celsius = temp_kelvin / (1 + (10.8 * temp_kelvin / 14388) * np.log(eps)) - 273.15
    return lst_celsius
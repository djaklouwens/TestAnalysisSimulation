import numpy as np
from matplotlib import pyplot as plt
from pykrige.ok import OrdinaryKriging
import netCDF4 as nc
from datetime import datetime
import os
import re
from gim_tools import get_GIM, split_time_date


def tec(gim_matrix, x:int, y:int)->float:
    ''' Function to calculate Total Electron Content (TEC) given longitude (x) and latitude (y). '''
    x = x % 360
    if x == 360: x = 0
    return gim_matrix[y, x]

def geo_to_index(lon: float, lat: float, rounding: bool = False) -> tuple:
    ''' 
    Function to convert geographic coordinates to index coordinates.
    
    Parameters
    ----------
    lon : float
        Longitude coordinate.
    lat : float
        Latitude coordinate.
    rounding : bool, optional
        If True, the output index coordinates are rounded to integers. Default is False.
    
    Returns
    -------
    x, y : tuple
        A tuple containing the index coordinates (x, y):
        x : float or int
            Index coordinate along the x-axis.
        y : float or int
            Index coordinate along the y-axis.
    
    Notes
    -----
    - Index [0,0] corresponds to the top left corner of the grid, with geographic coordinates [180.5, 89.5].
    - For longitude (lon):
        - If lon is in the range [180.5, 360], it's converted to index by subtracting 180.5.
        - If lon is in the range [0, 180.5), it's converted by adding 179.5.
        - Any other value of lon is considered out of range, and an error is printed.
    - For latitude (lat):
        - If lat is in the range [-90, 90], it's converted to index by subtracting from 89.5 and taking the absolute value.
        - Any other value of lat is considered out of range, and an error is printed.
    - If rounding is True, the output index coordinates are rounded to the nearest integer.
    '''
    if lon >= 180.5 and lon <= 360:
        x = lon - 180.5
    elif lon >= 0 and lon < 180.5:
        x = lon + 179.5
    else:
        print("Error: longitude (", lon, ") out of range")
        return
    
    if lat >= -90 and lat <= 90:
        y = abs(lat - 89.5)
    else:
        print("Error: latitude (", lat, ") out of range")
        return
       
    if rounding:                                                       
        x = int(x)
        y = int(y)
    
    return x, y

def index_to_geo(x: np.ndarray, y: np.ndarray) -> tuple:
    ''' 
    Function to convert index coordinates to geographic (spherical) coordinates.
    
    Parameters
    ----------
    x : numpy.ndarray
        Array of x index coordinates.
    y : numpy.ndarray
        Array of y index coordinates.
    
    Returns
    -------
    lon, lat : tuple
        A tuple containing two numpy arrays:
        lon : numpy.ndarray
            Array of longitude coordinates.
        lat : numpy.ndarray
            Array of latitude coordinates.
    
    Notes
    -----
    - Index [0,0] corresponds to the top left corner of the grid, with geographic coordinates [180.5, 89.5].
    - For x coordinates:
        - If x is in the range [-180, 179.5], it's directly converted to longitude by adding 180.5.
        - If x is in the range (179.5, 539], it's converted by subtracting 179.5.
        - Any other value of x is considered out of range, and an error is printed.
    - For y coordinates:
        - If y is in the range [0, 180], it's converted to latitude by subtracting from 89.5 and negating.
        - Any other value of y is considered out of range, and an error is printed.
    '''
    lon = np.array([])
    lat = np.array([])
    
    for xi in x:
        if xi >= -180 and xi <= 179.5:
            lon = np.append(lon, xi + 180.5)
        elif xi > 179.5 and xi <= 539:
            lon = np.append(lon, xi - 179.5)
        else:
            print("Error: x (", xi, ") out of range")
            return
        
    for yi in y:
        if yi >= 0 and yi <= 180:
            lat = np.append(lat, -yi + 89.5)
        else:
            print("Error: y (", yi, ") out of range")
            return
    
    return lon, lat

def tec_kriging(gim_matrix, lon: float, lat: float, lon_halfrange: int = 45, lat_halfrange: int = 22, image: bool = False, plot_variogram: bool = False) -> float:
    ''' 
    Function to perform kriging interpolation of Total Electron Content (TEC) data.
    
    Parameters
    ----------
    lon : float
        Longitude coordinate for the center of the interpolation window.
    lat : float
        Latitude coordinate for the center of the interpolation window.
    lon_halfrange : int, optional
        Half-range in the x-direction (longitude) for the interpolation window. Default is 45.
    lat_halfrange : int, optional
        Half-range in the y-direction (latitude) for the interpolation window. Default is 22.
    image : bool, optional
        If True, displays an image of the interpolated TEC values. Default is False.
    plot_variogram : bool, optional
        If True, plots the variogram. Default is False.
    
    Returns
    -------
    z1 : float
        Interpolated TEC value at the specified longitude and latitude coordinates.
    
    Notes
    -----
    - Uses Ordinary Kriging interpolation technique to estimate TEC values.
    - The interpolation window is centered at the specified longitude and latitude coordinates.
    - The half-ranges specify the extent of the interpolation window in both longitude and latitude directions.
    - If `image` is True, it displays the interpolated TEC values as an image plot.
    - If `plot_variogram` is True, it plots the variogram.
    '''
    x, y = geo_to_index(lon, lat, rounding=True)
    x_array = np.linspace(x - lon_halfrange, x + lon_halfrange, 2 * lon_halfrange + 1).astype(int)
    y_array = np.linspace(y - lat_halfrange, y + lat_halfrange, 2 * lat_halfrange + 1).astype(int)
    
    y_array = y_array[(159 >= y_array)]
    y_array = y_array[(y_array > 0)]
    
    z_array = np.array([])
    
    for i in range(len(x_array)):
        for j in range(len(y_array)):           
            z_array = np.append(z_array, tec(gim_matrix, x_array[i], y_array[j]))
    
    lon_array, lat_array = index_to_geo(x_array, y_array)
    
    lon_dims = np.repeat(lon_array, len(lat_array))
    lat_dims = np.tile(lat_array, len(lon_array))
    
    if(lon_dims.size != lat_dims.size or lon_dims.size != z_array.size or lat_dims.size != z_array.size):
        print("error: array sizes do not match")
        print("lon_dims: ", lon_dims.size, "lat_dims: ", lat_dims.size, "z_array: ", z_array.size)
        return

    OK = OrdinaryKriging(
        lon_dims,
        lat_dims,
        z_array,

        variogram_model="spherical",
        verbose=False,
        enable_plotting=plot_variogram,
        nlags=75,
        coordinates_type="geographic",
    )

    if image:
        z_results, ss_results = OK.execute("grid", lon_array + 0.5, lat_array + 0.5)
        plt.imshow(z_results, extent=[min(lon_array), max(lon_array), min(lat_array), max(lat_array)], origin="upper")
        plt.colorbar()
        plt.show()
        print(z_results)
    
    z1, ss1 = OK.execute("points", [lat], [lon])
    return z1


#print(tec_kriging(180,0, lon_halfrange=45, lat_halfrange=22, image=True, plot_variogram=True))


def time_interpolation(lon:float, lat:float, sat_date:float, time_res:int=0)->float:
    '''
    Function to linearly interpolate between two TEC maps,
    before and after the satellite's time, in order to stimate
    the TEC at the satellite's time.

    Parameters
    ----------
    lon: float
        The satellite's longitude.
    lat: float
        The satellite's latitude.
    sat_date: float
        The date of the satellite's measurement.
    time_res: float
        The time difference between the two TEC maps (15min/2h).

    Returns
    -------
    tec: float
        The estimated altitude after TEC interpolation in time and position.

    
    '''
    start = datetime.now()
    if time_res == 0: t = 15
    elif time_res == 1: t = 120

    getGIM = get_GIM(sat_date, time_res)
   
    gim1, gim2 = getGIM[0]


    sat_time = split_time_date(sat_date)[0]


    gim1_time = [int(i) for i in re.split(r'[:.,]', getGIM[1][0])]
    gim2_time = [int(i) for i in re.split(r'[:.,]', getGIM[1][1])]
    print("sat_time: ", sat_time, "gim1_time: ", gim1_time, "gim2_time: ", gim2_time)
    sat_rel_time = sat_time[0]*60 + sat_time[1] - gim1_time[0]*60 - gim1_time[1]
    print("relative time difference between sat and gim1: ", sat_rel_time)

    tec1 = tec_kriging(gim1, lon, lat)
    tec2 = tec_kriging(gim2, lon, lat)
    tec = tec1 + (tec2 - tec1) * sat_rel_time / t
    end = datetime.now()
    print("Runtime: ", end - start)
    print("tec1: ", tec1, "tec2: ", tec2, "tec: ", tec)
    return tec


print(time_interpolation(180,0, "00:07 16/03/2017"))


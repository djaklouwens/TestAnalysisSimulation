import shutil
from time import sleep
from directory_paths import project_dir, temp_dir, plot_dir, illegal_char
import numpy as np
from matplotlib import pyplot as plt
from pykrige.ok import OrdinaryKriging
import netCDF4 as nc
from datetime import datetime
import os
import re
from gim_tools import get_GIM, split_time_date, get_coord_around_pt, save_GIMs
import multiprocessing

def tec(gim_matrix, x:int, y:int)->float:
    ''' Function to calculate Total Electron Content (TEC) given longitude (x) and latitude (y). '''
    x = x % 360
    if x == 360: x = 0
    return gim_matrix[y, x]

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
    - Index [0,0] corresponds to the top left corner of the grid, with geographic coordinates [180.5, -89.5].
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

def tec_kriging(gim_matrix, lon: float, lat: float, nlags: int = 75, radius: int = 500, max_points: int = 300, image: bool = False, plot_variogram: bool = False) -> float:
    ''' 
    Function to perform kriging interpolation of Total Electron Content (TEC) data.
    
    Parameters
    ----------
    gim_matrix : numpy.ndarray
        Matrix containing the TEC data.
    lon : float
        Longitude coordinate for the center of the interpolation window.
    lat : float
        Latitude coordinate for the center of the interpolation window.
    nlags : int, optional
        Number of lags to be used in the variogram model. Default is 75.
    radius : int, optional
        Radius of the interpolation window in kilometers. Default is 500.
    max_points : int, optional
        Maximum number of surrounding points to be used for interpolation. Default is 300.
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
    - If `image` is True, it displays the interpolated TEC values as an image plot.
    - If `plot_variogram` is True, it plots the variogram.
    '''
 
    
    lat_if_array, lon_if_array = get_coord_around_pt(lat, lon, R_tspot=radius, max_size=max_points)
    
    x_array = (179.5+lon_if_array).astype(int)
    y_array = abs(lat_if_array - 89.5).astype(int)
    z_array = np.array([])

    for i in range(len(x_array)):         
            z_array = np.append(z_array, tec(gim_matrix, x_array[i], y_array[i]))
    
    lon_array, lat_array = index_to_geo(x_array, y_array)

    if(lon_array.size != lat_array.size or lon_array.size != z_array.size or lat_array.size != z_array.size):
        print("error: array sizes do not match")
        print("lon_dims: ", lon_array.size, "lat_dims: ", lat_array.size, "z_array: ", z_array.size)
        return

    OK = OrdinaryKriging(
        lon_array,
        lat_array,
        z_array,

        variogram_model="exponential",
        verbose=False,
        enable_plotting=plot_variogram,
        nlags=nlags,
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




def time_interpolation(lon: float, lat: float, sat_date: float, nlags: int = 75, radius: int = 500, max_points: int = 300, time_res: int = 1, del_temp=False)->float:
    '''
    Function to linearly interpolate between two TEC maps,
    before and after the satellite's time, in order to estimate
    the TEC at the satellite's time.

    Parameters
    ----------
    lon: float
        The satellite's longitude.
    lat: float
        The satellite's latitude.
    sat_date: float
        The date of the satellite's measurement.
    nlags: int, optional
        Number of lags to be used in the variogram model. Default is 75.
    radius: int, optional
        Radius of the interpolation window in kilometers. Default is 500.
    max_points: int, optional
        Maximum number of surrounding points to be used for interpolation. Default is 300.
        time_res: INT
        Selected time resolution. 0 if jpli, 1 jpld. By default, jpli dataset is chosen.
    del_temp: bool, optional
        If True, deletes temporary files after use. Default is False.

    Returns
    -------
    tec: float
        The estimated Total Electron Content (TEC) at the specified longitude, latitude, and time.
    
    '''
    t = 15
    getGIM = get_GIM(sat_date, time_res, del_temp = del_temp)

    if getGIM[0].ndim == 3:
        gim1, gim2 = getGIM[0]

        sat_time = split_time_date(sat_date)[0]
        gim1_time = [int(i) for i in re.split(r'[:.,]', getGIM[1][0])]
        gim2_time = [int(i) for i in re.split(r'[:.,]', getGIM[1][1])]

        sat_rel_time = sat_time[0]*60 + sat_time[1] - gim1_time[0]*60 - gim1_time[1]

        tec1 = tec_kriging(gim1, lon, lat, nlags = nlags, radius = radius, max_points = max_points)
        tec2 = tec_kriging(gim2, lon, lat, nlags = nlags, radius = radius, max_points = max_points)
        tec = tec1 + (tec2 - tec1) * sat_rel_time / t

    elif getGIM[0].ndim == 2:
        gim1 = getGIM[0]
        tec = tec_kriging(gim1, lon, lat, nlags = nlags, radius = radius, max_points = max_points)

    else:
        print("Error: GIM dimension not recognized")
        return

    return tec

def mass_interpolate(lon_list, lat_list, sat_date_list, nlags: int = 75, radius: int = 500, max_points: int = 300, time_res: int = 1, del_temp: bool = True):
    '''
    Perform mass interpolation of Total Electron Content (TEC) data for multiple points.

    Parameters
    ----------
    lon_list: list
        List of longitude coordinates for the points.
    lat_list: list
        List of latitude coordinates for the points.
    sat_date_list: list
        List of dates for the satellite measurements corresponding to each point.
    nlags: int, optional
        Number of lags to be used in the variogram model. Default is 75.
    radius: int, optional
        Radius of the interpolation window in kilometers. Default is 500.
    max_points: int, optional
        Maximum number of surrounding points to be used for interpolation. Default is 300.
    del_temp: bool, optional
        If True, deletes temporary files after use. Default is True.
    time_res: int, optional
        Selected time resolution. 0 if jpli, 1 jpld. By default, jpld dataset is chosen.

    Returns
    -------
    tec_results: numpy.ndarray
        Array containing the interpolated TEC values for each point.
    failed_indices: list
        List of indices corresponding to points where interpolation failed.
    '''
    
    print("Checking availability of source GIMs...")
    save_GIMs(sat_date_list)
    print("Staring mass interpolation...")
    starts = datetime.now()
    tec_results = np.array([])
    failed_indices = []
    size = len(lon_list)
    for i in range(size):
        try:
            tec_results = np.append(tec_results, time_interpolation(lon_list[i], lat_list[i], sat_date_list[i], nlags = nlags, radius = radius, max_points = max_points, time_res = time_res))
            print("Progress: " , i+1  , "/" , size)
        except ValueError:
            print("Error: interpolation failed for point: ", i)
            failed_indices.append(i)
            
        
    if del_temp:
        shutil.rmtree(temp_dir)
        print("gim files deleted")
        
    ends = datetime.now()
    print("Interpolated: ", len(tec_results) ,"TEC points in Series Runtime: ", ends - starts ," s")
    return tec_results, failed_indices


def delete_failed_indices(failed_indices, time_list, lat_array, lon_array, sla_array):
    '''
    TODO: add docstring (copied straight from full_integration.py)
    '''
    failed_indices.reverse()
    for index in failed_indices:
        del time_list[index]
        lat_array = np.delete(lat_array, index, axis=0)
        lon_array = np.delete(lon_array, index, axis=0)
        sla_array = np.delete(sla_array, index, axis=0)
    return time_list, lat_array, lon_array, sla_array

if __name__ == '__main__':

   #random lists
    lon_list = [np.random.uniform(0,360) for _ in range(36)]
    lat_list = [np.random.uniform(-90,90) for _ in range(36)]
    sat_date_list = ["23:54 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2016", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2017", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2016", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 15/03/2017", "00:08 16/03/2017", "00:34 16/03/2017", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2014","00:16 16/03/2017"]
    
    mi = mass_interpolate(lon_list, lat_list, sat_date_list)
    print(mi)

import os
import re
import shutil
import datetime as dt
import multiprocessing

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import netCDF4 as nc
from pykrige.ok import OrdinaryKriging

import gim_tools
from directory_paths import temp_dir
import datetime_tools as dt_extra

def tec(gim_matrix, x:int, y:int)->float:
    ''' Function to calculate Total Electron Content (TEC) given longitude (x) and latitude (y). '''
    x = x % 360
    if x == 360: x = 0
    return gim_matrix[y, x]


def index_to_geo(x: np.ndarray, y: np.ndarray) -> tuple:
    ''' 
    Function to convert index (associated with RADS data) coordinates to 
    geographic (spherical) coordinates.
    
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


def geo_to_cartesian_vec(lat, lon, rad=False):
    '''
    Function to convert latitude and longitude coordinates into cartesian coordinate.
    
    Parameters
    ----------
    lat: float or ndarray
        Latitude angle(s)
    lon: float or ndarray
        Longitude angle(s)
    rad: bool (default: False)
        Indicate whether the specified angles are in radians.
    
    Returns
    -------
    (float, float, float) or (ndarray, ndarray, ndarray)
        Returns the x, y and z components of a unit vector in the direction of the latitude
        and longitude coordinate.
    
    '''
    if not rad:
        lat = np.deg2rad(lat)
        lon = np.deg2rad(lon)
    return np.cos(lat)*np.cos(lon), np.cos(lat)*np.sin(lon), np.sin(lat)

def get_coord_around_pt(c_lat:float, c_lon:float,
                        R_tspot:float, max_size=300, lat_array:np.ndarray = np.arange(-89.5, 89.5+1, 1), lon_array:np.ndarray = np.arange(-179.5, 179.5+1, 1),  R_earth:float=6378, plot:bool=False, ax=None):
    '''
    Function that, for a given array of existing latitude and longitude coordinates, 
    determines the subset of coordinates that are within a particular ditance from 
    a central coordinate.
    
    Parameters
    ----------
    lat_array: np.ndarray
        Numpy array (1D) of existing latitude coordinates.
    lon_array: np.ndarray
        Numpy array (1D) of existing longitude coordinates.
    c_lat: float
        Latitude coordinate of centre coordinate.
    c_lon: float
        Longitude coordinate of centre coordinate.
    R_tspot: float
        Largest acceptable distance from centre point, in Km. Translates to radius 
        of target spot.
    R_earth: float (assumed 6378 Km)
        Radius of the Earth, assumed constant.
    plot: bool (False by default)
        Determine whether to plot the target spot in a world map.
    ax: matplotlib axes object (None by default)
        Pass the axes on which to plot the target spot. Only useful if
        bool is set to True. If not provided, a new axes is generated.
    
    Returns
    -------
    tlat, tlon : np.ndarray
        Existing latitude and longitude coordinates that are within R_tspot 
        distance from the centre coordinate. Both are one-dimensional arrarys.    
    '''
    gamma = R_tspot / R_earth # characteristic angle of cone, in radians

    lon, lat = np.meshgrid(lon_array, lat_array)

    c_vec = np.array(geo_to_cartesian_vec(c_lat, c_lon))
    u = np.array(geo_to_cartesian_vec(lat, lon))
    u = np.rollaxis(u, 0, 3)

    angles = np.arccos(np.inner(u, c_vec))
    condition = angles < gamma
    tlat = lat[condition]
    tlon = lon[condition]
 
    #remove elements if array is too big
    if tlon.size > max_size:
        remove_indeces = sorted(np.random.choice(len(tlon), tlon.size-max_size, replace=False), reverse=True)
        for i in remove_indeces:
            tlon = np.delete(tlon, i)
            tlat = np.delete(tlat, i)
    #print(tlon.size)
    if plot:
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 8))
            earth = Basemap()
    
        grid_style = {'linewidth': 0.2, 'dashes':[1,0], 'labels':[1, 1, 1, 1], 'labelstyle':'+/-'}
        earth.drawcoastlines(color='#555566', linewidth=1, ax=ax)
        #earth.plot(lon.reshape(-1), lat.reshape(-1), 'k.', alpha=0.5 ,latlon=True, ax=ax)
        arg_order = np.argsort(tlon)

        earth.plot(tlon[arg_order], tlat[arg_order], 'g.', latlon=True, ax=ax, alpha=0.6)
        earth.plot(c_lon, c_lat, 'ro', latlon=True, ax=ax)
                
        earth.drawmeridians(np.arange(-180, 181, 20), **grid_style, ax=ax)
        earth.drawparallels(np.arange(-90, 91, 30), **grid_style, ax=ax)
        plt.show()
  
    return tlat, tlon


def tec_kriging(gim_matrix, lon: float, lat: float, nlags: int = 75, radius: int = 500, max_points: int = 300,
                 image: bool = False, plot_variogram: bool = False) -> float:
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




def time_interpolation(lon:float, lat:float, sat_date:float, nlags:int=75, 
                       radius:int=500, max_points:int=300, del_temp=False)->float:
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

    del_temp: bool, optional
        If True, deletes temporary files after use. Default is False.

    Returns
    -------
    tec: float
        The estimated Total Electron Content (TEC) at the specified longitude, latitude, and time.
    
    '''
    t = 15
    getGIM = gim_tools.get_GIM(sat_date, del_temp=del_temp)

    if getGIM[0].ndim == 3:
        gim1, gim2 = getGIM[0]

        sat_time = dt_extra.split_time_date(sat_date)[0]
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

def mass_interpolate(lon_list, lat_list, sat_date_list, nlags:int=75, 
                     radius:int=500, max_points:int=300, del_temp:bool=True):
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

    Returns
    -------
    tec_results: numpy.ndarray
        Array containing the interpolated TEC values for each point.
    failed_indices: list
        List of indices corresponding to points where interpolation failed.
    '''
    
    print("Checking availability of source GIMs...")
    gim_tools.fetch_GIM_files(sat_date_list)
    print("All neccessary source GIMs availible for interpolation!")
    print("Staring mass interpolation...")
    starts = dt.datetime.now()
    tec_results = np.array([])
    failed_indices = []
    size = len(lon_list)
    for i in range(size):
        try:
            tec_results = np.append(tec_results, time_interpolation(lon_list[i], lat_list[i], sat_date_list[i], 
                                                                    nlags=nlags, radius=radius, max_points=max_points))
            print("Progress: " , i+1  , "/" , size)
        except ValueError:
            print("Error: interpolation failed for point: ", i)
            failed_indices.append(i)
        
    if del_temp:
        shutil.rmtree(temp_dir)
        print("Gim files deleted")
        
    ends = dt.datetime.now()
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
    # lon_list = [np.random.uniform(0,360) for _ in range(36)]
    # lat_list = [np.random.uniform(-90,90) for _ in range(36)]
    # sat_date_list = ["23:54 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2016", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2017", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 16/03/2017", "00:08 16/03/2017", "00:09 16/03/2016", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2017","00:16 16/03/2017","00:07 15/03/2017", "00:08 16/03/2017", "00:34 16/03/2017", "00:10 16/03/2017", "00:11 16/03/2017", "00:12 16/03/2017", "00:13 16/03/2017","00:14 16/03/2014","00:16 16/03/2017"]
    
    # mi = mass_interpolate(lon_list, lat_list, sat_date_list)
    # print(mi)

    get_coord_around_pt(91, 0, 1200, plot=True)

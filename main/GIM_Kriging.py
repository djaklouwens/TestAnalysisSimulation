import numpy as np
from matplotlib import pyplot as plt
from pykrige.ok import OrdinaryKriging
import netCDF4 as nc
from datetime import datetime
import os
from gim_tools import *

time = 0    #must be smaller than 96
# get the netcdf filepath
fd = os.path.dirname(os.path.realpath('__file__'))
fn = os.path.join(fd,'main\GIMs\jpli0750.17i.nc')

# read the tecmap from the netcdf file
ds = nc.Dataset(fn)
tecmatrix =  ds['tecmap'][time,:]

def tec(x, y):
   # y = y % 180
    x = x % 360
   #  if y == 180:
   #     y = 0
    if x == 360:
        x = 0
    return tecmatrix[y, x]

def geo_to_index(lon, lat, rounding=False):
    # index [0,0] is the top left corner of the grid, corresponding to geo [-179.5, 89.5]
    # convert from geocoordinates to indexcoordinates
    if rounding:                                                       
        x = round(lon + 179.5)
        y = round(abs(lat - 89.5))
        return x,y
    if not rounding:
        x = lon + 179.5
        y = abs(lat - 89.5)
        return x,y


def tec_kriging(lon, lat, lon_halfrange=45, lat_halfrange=22, image=False, plot=True):
    x,y = geo_to_index(lon, lat, rounding=True)
    x_array = np.linspace(x-lon_halfrange, x+lon_halfrange, 2*lon_halfrange+1).astype(int)
    y_array = np.linspace(y-lat_halfrange, y+lat_halfrange, 2*lat_halfrange+1).astype(int)
    #mask = y_array >= 0 | y_array <= 159
    #y_array = y_array[mask]
    y_array = y_array[(159 >= y_array)]
    y_array = y_array[(y_array > 0)]
    # print(y_array)
    # print(y_array.max(), y_array.min())
    z_array = np.array([])
    
    for i in range(len(x_array)):
        for j in range(len(y_array)):
            if y_array[j] > 159:
                y_array = np.delete(y_array, j)
            
            if y_array[j] < 0:
                # print(y_array[j])
                y_array = np.delete(y_array, j)
               
            else: z_array = np.append(z_array, tec(x_array[i], y_array[j]))
            
    x_dims = np.repeat(x_array, len(y_array))
    y_dims = np.tile(y_array, len(x_array))
    
    if(x_dims.size != y_dims.size or x_dims.size != z_array.size or y_dims.size != z_array.size):
        print("Error: Array sizes do not match")
        print("x_dims: ", x_dims.size, "y_dims: ", y_dims.size, "z_array: ", z_array.size)
        return

    OK = OrdinaryKriging(
        x_dims,
        y_dims,
        z_array,
        variogram_model="exponential",
        verbose=False,
        enable_plotting=plot,
        nlags=100,
        coordinates_type="geographic",
    )

    if image:
        z_results, ss_results = OK.execute("grid", x_array, y_array)
        plt.imshow(z_results, extent=[lon-lon_halfrange, lon+lon_halfrange, lat+lat_halfrange, lat-lat_halfrange], origin="upper") #the extent is not correct yet
        plt.colorbar()
        plt.show()

    x,y = geo_to_index(lon, lat)
    z1, ss1 = OK.execute("points", [x], [y])
    return z1



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

    if time_res == 0: t = 15
    elif time_res == 1: t = 120

    gim1, gim2 = get_TEC(sat_date, time_res)[0]
    
    t_gim1 = split_time_date(get_TEC(sat_date, time_res)[1][0])[0]
    sat_time = split_time_date(sat_date)[0]
    sat_rel_time = sat_time[0]*60 + sat_time[1] - t_gim1[0]*60 - t_gim1[1]


    tec = tec_kriging(lon, lat, gim1) + (tec_kriging(lon, lat, gim2) - tec_kriging(lon, lat, gim1)) * sat_rel_time / t

    return tec
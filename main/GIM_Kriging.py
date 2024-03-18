import numpy as np
from matplotlib import pyplot as plt
from pykrige.ok import OrdinaryKriging
import netCDF4 as nc
from datetime import datetime
import os

time = 0    #must be smaller than 96
# get the netcdf filepath
fd = os.path.dirname(os.path.realpath('__file__'))
fn = os.path.join(fd,'main\GIMs\jpli0750.17i.nc')

# read the tecmap from the netcdf file
ds = nc.Dataset(fn)
tecmatrix =  ds['tecmap'][time,:]

def tec(x, y):

    x = x % 360

    if x == 360:
        x = 0
    return tecmatrix[y, x]

def geo_to_index(lon, lat, rounding=False):
    # index [0,0] is the top left corner of the grid, corresponding to geo [180.5, 89.5]
    # convert from geocoordinates to indexcoordinates
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
    
    return x,y

def index_to_geo(x, y): 
    # index [0,0] is the top left corner of the grid, corresponding to geo [180.5, 89.5]
    # convert from indexcoordinates to geocoordinates
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



def tec_kriging(lon, lat, lon_halfrange=45, lat_halfrange=22, image=False, plot_variogram=False):   
    x,y = geo_to_index(lon, lat, rounding=True)
    x_array = np.linspace(x-lon_halfrange, x+lon_halfrange, 2*lon_halfrange+1).astype(int)
    y_array = np.linspace(y-lat_halfrange, y+lat_halfrange, 2*lat_halfrange+1).astype(int)
    
    y_array = y_array[(159 >= y_array)]
    y_array = y_array[(y_array > 0)]
    
    z_array = np.array([])
    
    for i in range(len(x_array)):
        for j in range(len(y_array)):           
            z_array = np.append(z_array, tec(x_array[i], y_array[j]))
    
    print(x_array)
    lon_array, lat_array = index_to_geo(x_array, y_array)        
    
    lon_dims = np.repeat(lon_array, len(lat_array))
    lat_dims = np.tile(lat_array, len(lon_array))
    
    if(lon_dims.size != lat_dims.size or lon_dims.size != z_array.size or lat_dims.size != z_array.size):
        print("error: array sizes do not match")
        print("lon_dims: ", lon_dims.size, "lat_dims: ", lat_dims.size, "z_array: ", z_array.size)
        return

    print(lon_array)
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
        z_results, ss_results = OK.execute("grid", lon_array+0.5, lat_array+0.5)
        plt.imshow(z_results, extent=[min(lon_array), max(lon_array), min(lat_array), max(lat_array)] , origin="upper") #the extent is not correct yet
        plt.colorbar()
        plt.show()
        print(z_results)
    
    z1, ss1 = OK.execute("points", [lat], [lon])
    return z1

print(tec_kriging(180,0, lon_halfrange=45, lat_halfrange=22, image=True, plot_variogram=True))

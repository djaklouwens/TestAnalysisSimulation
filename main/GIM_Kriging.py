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
   # y = y % 180
    x = x % 360
   #  if y == 180:
   #     y = 0
    if x == 360:
        x = 0
    return tecmatrix[y, x]

def geo_to_index(lon, lat, rounding=False):
    # index [0,0] is the top left corner of the grid, corresponding to geo [181.5, 89.5]
    # convert from geocoordinates to indexcoordinates
    if rounding:                                                       
        x = round(lon - 181.5)
        y = round(abs(lat - 89.5))
        return x,y
    if not rounding:
        x = lon - 181.5
        y = abs(lat - 89.5)
        return x,y
    
def index_to_geo(x, y): 
    # index [0,0] is the top left corner of the grid, corresponding to geo [-179.5, 89.5] and sphere [180.5, 89.5]
    # convert from indexcoordinates to geocoordinates
    lon = x - 179.5 #implement wrap around
    lat = 89.5 - y
    return lon, lat


def tec_kriging(lon, lat, lon_halfrange=45, lat_halfrange=22, image=False):   
    x,y = geo_to_index(lon, lat, rounding=True)
    x_array = np.linspace(x-lon_halfrange, x+lon_halfrange, 2*lon_halfrange+1).astype(int)
    y_array = np.linspace(y-lat_halfrange, y+lat_halfrange, 2*lat_halfrange+1).astype(int)
    #mask = y_array >= 0 | y_array <= 159
    #y_array = y_array[mask]
    y_array = y_array[(159 >= y_array)]
    y_array = y_array[(y_array > 0)]
    print(y_array)
    print(y_array.max(), y_array.min())
    z_array = np.array([])
    
    for i in range(len(x_array)):
        for j in range(len(y_array)):           
            z_array = np.append(z_array, tec(x_array[i], y_array[j]))
    
    lon_array, lat_array = index_to_geo(x_array, y_array)        
    
    lon_dims = np.repeat(lon_array, len(lat_array))
    lat_dims = np.tile(lat_array, len(lon_array))

    # x_dims = np.repeat(x_array, len(y_array))
    # y_dims = np.tile(y_array, len(x_array))
    
    # if(x_dims.size != y_dims.size or x_dims.size != z_array.size or y_dims.size != z_array.size):
    #     print("Error: Array sizes do not match")
    #     print("x_dims: ", x_dims.size, "y_dims: ", y_dims.size, "z_array: ", z_array.size)
    #     return
    OK = OrdinaryKriging(
        lon_dims,
        lat_dims,
        z_array,
        variogram_model="gaussian",
        verbose=False,
        enable_plotting=True,
        nlags=10,
        coordinates_type="geographic",
    )

    # OK = OrdinaryKriging(
    #     x_dims,
    #     y_dims,
    #     z_array,
    #     variogram_model="gaussian",
    #     verbose=False,
    #     enable_plotting=True,
    #     nlags=10,
    #     coordinates_type="geographic",
    # )
    # if image:
    #     z_results, ss_results = OK.execute("grid", x_array, y_array)
    #     plt.imshow(z_results, extent=[lon-lon_halfrange, lon+lon_halfrange, lat+lat_halfrange, lat-lat_halfrange], origin="upper") #the extent is not correct yet
    #     plt.colorbar()
    #     plt.show()
    z1, ss1 = OK.execute("points", [lat], [lon])
    return z1
    # x,y = geo_to_index(lon, lat)
    # z1, ss1 = OK.execute("points", [x], [y])
    # return z1
print(tec_kriging(0,0, lon_halfrange=45, lat_halfrange=22, image=False))

import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc
from datetime import datetime
import os

time = 0    #must be smaller than 96


# get the netcdf filepath
fd = os.path.dirname(os.path.realpath('__file__'))
fn = os.path.join(fd,'GIMs\jpli0750.17i.nc')

# read the tecmap from the netcdf file
ds = nc.Dataset(fn)
tecmatrix =  ds['tecmap'][time,:]

def tec(lat, lon):
    return tecmatrix[lat, lon]

"""
x_star = np.array([5, 5])

Y = np.array([])
for i in range(0, 10):
    for j in range(0, 10):
        Y = np.append(Y, tec(i, j))




   


def v(r): #TODO
    return 1



# calculate the semivariance
def semivariance(tec1, tec2):
    var = (tec1 - tec2)**2/2
    #print(tec1, tec2, var)
    return var

# calculate the distance between two points
def get_distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# define the depth of the grid
depth = 10
start = datetime.now()

# intialize the arrays to store the semivariance and distances
vars = np.array([])
distances = np.array([])

# loop through all the points and calculate the semivariance
for lat in range(0, depth):
    for lon in range(0, depth):
        for lat2 in range(0, depth):
            for lon2 in range(0, depth):
                if(lat != lat2 and lon != lon2):
                    distances = np.append(distances, get_distance(lat, lon, lat2, lon2))
                    vars = np.append(vars, semivariance(tec(lat, lon), tec(lat2, lon2)))

# find difference loop start and end time and display
end = datetime.now()
td = (end - start).total_seconds() * 10**3
print(f"The time of execution of above program is : {td:.03f}ms")

#print("dist: " , distances)
#print("vars: " , vars)
plt.scatter(distances, vars)
plt.show()
"""
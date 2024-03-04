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

# calculate the semivariance
def semivariance(tec1, tec2):
    var = (tec1 - tec2)**2/2
    #print(tec1, tec2, var)
    return var
  
def get_distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

depth = 22
start = datetime.now()

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

end = datetime.now()
# find difference loop start and end time and display
td = (end - start).total_seconds() * 10**3
print(f"The time of execution of above program is : {td:.03f}ms")

#print("dist: " , distances)
#print("vars: " , vars)
plt.scatter(distances, vars)
plt.show()

"""
Below is the time taken for the above program to execute for different depths
# 10: 550 ms
# 11: 800 ms 
# 12: 1200 ms
# 13: 1600 ms
# 14: 2600 ms
# 15: 3400 ms
# 16: 5800 ms

depth = [10, 11, 12, 13, 14, 15, 16, 20, 22]
time = [550, 800, 1200, 1600, 2600, 3400, 5800, 49000, 189000]
fit = np.polyfit(depth, time, 4)
print(fit)
def fit(d):
    return 1.20562580e+01*d**4 -5.92043594e+02*d**3 +  1.09153932e+04*d**2 -8.90304452e+04*d**1 + 2.70813388e+05
plt.plot(np.linspace(0,180,180), fit(np.linspace(0,180,180)))
plt.plot(depth,time)
plt.show()
"""
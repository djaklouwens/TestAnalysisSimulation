# -*- coding: utf-8 -*-
"""
Geometric example
=================

A small example script showing the usage of the 'geographic' coordinates type
for ordinary kriging on a sphere.
"""

import numpy as np
from matplotlib import pyplot as plt

from pykrige.ok import OrdinaryKriging
from TEC_Kriging import tec


maxlon = 90 #+30
maxlat = 45 #+15

N = 7
lon = np.linspace(0.0, maxlon-1, maxlon)
lat = np.linspace(0, maxlat-1, maxlat)
print("lat array: ", lat)
z = np.array([])
for i in range(0, maxlon):
    for j in range(0,maxlat):
        z = np.append(z, tec(j, i))
        
print(z.mean)
        
print("tec array: ", z)

lon = np.repeat(lon, maxlat)
lat = np.tile(lat, maxlon)

print("sizes: ", lon.size, lat.size, z.size)
print("tiled lat: ", lat)

# Generate a regular grid with 60° longitude and 30° latitude steps:
#grid_lon = np.linspace(-180, -90, 100)
#grid_lat = np.linspace(90.0, 45, 100)

grid_lon = np.linspace(0, 180, 100)
grid_lat = np.linspace(0, 90, 100)


# Create ordinary kriging object:
OK = OrdinaryKriging(
    lon,
    lat,
    z,
    variogram_model="linear",
    verbose=False,
    enable_plotting=False,
    coordinates_type="geographic",
)

# Execute on grid:
z1, ss1 = OK.execute("grid", grid_lon, grid_lat)

# # Create ordinary kriging object ignoring curvature:
# OK = OrdinaryKriging(
#     lon, lat, z, variogram_model="linear", verbose=False, enable_plotting=False
# )

# # Execute on grid:
# z2, ss2 = OK.execute("grid", grid_lon, grid_lat)

###############################################################################
# Print data at equator (last longitude index will show periodicity):

print("Original data:")
print("Longitude:", lon.astype(int))
print("Latitude: ", lat.astype(int))
print("z:        ", np.array_str(z, precision=2))
print("\nKrige at 60° latitude:\n======================")
print("Longitude:", grid_lon)
print("Value:    ", np.array_str(z1[5, :], precision=2))
print("Sigma²:   ", np.array_str(ss1[5, :], precision=2))

###############################################################################

print(z1)
plt.imshow(z1, extent=[-180, -90, 90, 45], origin="upper")
#plt.set_title("geo-coordinates")
plt.colorbar()
plt.show()

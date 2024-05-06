import os
import netCDF4 as nc
from datetime import datetime, timedelta
import numpy as np

def convert_time(seconds_since_1985):
    base_date = datetime(1985, 1, 1, 0, 0, 0)
    target_date = base_date + timedelta(seconds=seconds_since_1985)
    formatted_date = target_date.strftime('%H:%M %d/%m/%Y')
    return formatted_date

def convert_longitude_to_0_360(longitude):
    while longitude < -180:
        longitude += 360
    if longitude < 0:
        longitude += 360
    return longitude

def extract_rads(file_name):
    file_directory = os.path.dirname(os.path.realpath('__file__'))
    file_path = os.path.join(file_directory, 'RADS', file_name) # notita: add the 'main'
    print(file_path)
    try:
        ds = nc.Dataset(file_path)
        secs_array = np.array(ds['time'][:])
        lat_array = np.array(ds['lat'][:])
        lon_array = np.array(ds['lon'][:])
        sla_array = np.array(ds['sla'][:])
    finally:
        ds.close()

    time_list = [convert_time(t) for t in secs_array]
    lon_array = np.array([convert_longitude_to_0_360(lon) for lon in lon_array])

    return time_list, lat_array, lon_array, sla_array
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

def extract_rads(file_name, max_lat=None):
    file_directory = os.path.dirname(os.path.realpath('__file__'))
    file_path = os.path.join(file_directory, r'RADS', file_name) # notita: add the 'main'
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
    
    # Apply latitude filter if provided
    if max_lat is not None:
        indices = abs(lat_array) <= max_lat
        lat_array = lat_array[indices]
        lon_array = lon_array[indices]
        sla_array = sla_array[indices]
        time_list = [time_list[i] for i in range(len(time_list)) if indices[i]]

    return [time_list, lat_array, lon_array, sla_array]

def del_indices(extractions: list, indices): #works for 1 or more extraction(s) and 1 or more indices
    results = []
    for extraction in extractions:
        for index in sorted(indices, reverse=True):
            del extraction[0][index]
            extraction[1] = np.delete(extraction[1], index, axis=0)
            extraction[2] = np.delete(extraction[2], index, axis=0)
            extraction[3] = np.delete(extraction[3], index, axis=0)
        results.append(extraction)
    return results

def check_extractions(extraction1, extraction2):
    if extraction1[0] != extraction2[0]:
        print("Error: Time lists do not match")
        exit()

    if extraction1[1].any() != extraction2[1].any():
        print("Error: Latitude lists do not match")
        exit()

    if extraction1[2].any() != extraction2[2].any():
        print("Error: Longitude lists do not match")
        exit()
    else:
        return True

def match_extractions(corrected_extraction, uncorrected_extraction): #match extraction2 to extraction1
    # extraction consists of [0] time_list, [1] lat_array, [2] lon_array, [3] sla_array    
    indices_to_delete = []

    # Iterate through time stamps in uncorrected_extraction
    indices_to_delete = []
    for i, time in enumerate(uncorrected_extraction[0]):
        # If the time stamp doesn't exist in corrected_extraction, mark it for deletion
        if time not in corrected_extraction[0]:
            indices_to_delete.append(i)

    # Delete the corresponding data from datafile2 arrays
    uncorrected_extraction = del_indices([uncorrected_extraction], indices_to_delete)
  
    return uncorrected_extraction[0]

def extract_rads_duo(corrected_file, uncorrected_file, max_lat=None, max_size=None):
   corrected_extraction = extract_rads(corrected_file, max_lat)
   uncorrected_extraction = match_extractions(corrected_extraction, extract_rads(uncorrected_file, max_lat))

   check_extractions(corrected_extraction, uncorrected_extraction)

   # Randomly select points if max_size is provided
   if max_size is not None:
        if len(corrected_extraction[0]) > max_size:     
            indices = np.random.choice(len(corrected_extraction[0]), len(corrected_extraction[0])-max_size, replace=False)
            extractions = del_indices([corrected_extraction, uncorrected_extraction], indices)
            corrected_extraction = extractions[0]
            uncorrected_extraction = extractions[1]
   check_extractions(corrected_extraction, uncorrected_extraction)       
    
   return corrected_extraction, uncorrected_extraction
            


   

   

  
  
    
    
    
    
    
    
    
    
    
   ''' 
    time_list1, lat_array1, lon_array1, sla_array1 = extract_rads(file_name1, max_lat)
    time_list2, lat_array2, lon_array2, sla_array2 = extract_rads(file_name2, max_lat)
    
    indices_to_delete = []

    # Iterate through time stamps in datafile2
    for i, time in enumerate(time_list2):
        # If the time stamp doesn't exist in datafile1, mark it for deletion
        if time not in time_list1:
            indices_to_delete.append(i)

    # Delete the corresponding data from datafile2 arrays
    for index in sorted(indices_to_delete, reverse=True):
        del time_list2[index]
        lat_array2 = np.delete(lat_array2, index, axis=0)
        lon_array2 = np.delete(lon_array2, index, axis=0)
        sla_array2 = np.delete(sla_array2, index, axis=0)

    if(time_list1 != time_list2):
        print("Error: Time lists do not match")
        exit()

    if(lat_array1.any() != lat_array2.any()):
        print("Error: Latitude lists do not match")
        exit()

    if(lon_array1.any() != lon_array2.any()):
        print("Error: Longitude lists do not match")
        exit()
        
    return time_list2, lat_array2, lon_array2, sla_array2)

'''        
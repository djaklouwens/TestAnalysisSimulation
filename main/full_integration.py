from rads_extraction import extract_rads
from tec_interpolation import mass_interpolate
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

from gim_tools import save_GIMs

# Extract the RADS data

#corrected_file_name = 'j3_2016_summer.nc'
#uncorrected_file_name = 'j3_2016_summer_no_iono.nc'

#unsmoothed_file_name = 'j3_2016_summer_unsmoothed.nc'
#corrected_file_name = 'j3_2016_summer.nc'
#uncorrected_file_name = 'j3_2016_summer_no_iono.nc'

#corrected_file_name = 'j3_2017_23000.nc'
#uncorrected_file_name = 'j3_2017_23000_noiono.nc'

corrected_file_name = 's3a_2017_1500.nc'
uncorrected_file_name = 's3a_2017_1500_noiono.nc'
print("Selected SLA files: ", corrected_file_name," and " , uncorrected_file_name)
print("Extracting RADS data")




def match_rads(datafile1, datafile2):
    time_list1, lat_array1, lon_array1, sla_array1 = extract_rads(datafile1)
    time_list2, lat_array2, lon_array2, sla_array2 = extract_rads(datafile2)
    
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
        
    return time_list2, lat_array2, lon_array2, sla_array2

def delete_failed_indices(failed_indices, time_list, lat_array, lon_array, sla_array):
    failed_indices.reverse()
    for index in failed_indices:
        del time_list[index]
        lat_array = np.delete(lat_array, index, axis=0)
        lon_array = np.delete(lon_array, index, axis=0)
        sla_array = np.delete(sla_array, index, axis=0)
    return time_list, lat_array, lon_array, sla_array


        
corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array = extract_rads(corrected_file_name)
uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array = match_rads(corrected_file_name, uncorrected_file_name)
print(corrected_sla_array, uncorrected_sla_array)

print("Data files match")

#delta_sla_unsmoothed_array = unsmoothed_sla_array - uncorrected_sla_array
print("RADS Extraction successful!")
# Interpolate the TEC data
TEC_GIM, failed_indices = mass_interpolate(corrected_lon_array, corrected_lat_array, corrected_time_list)

corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array = delete_failed_indices(failed_indices, corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array)
uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array = delete_failed_indices(failed_indices, uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array)


delta_sla_array = corrected_sla_array - uncorrected_sla_array
print ("delta_sla_array: ", delta_sla_array)
print("TEC_GIM results; " , TEC_GIM)


freq = 13.575*10**9
TEC_Jason = delta_sla_array/(40.3/freq**2)/ 10**16

def loss_function(factor, TEC_GIM, TEC_Jason):
    adjusted_TEC_GIM_array = TEC_GIM * factor
    return np.sum(np.abs(adjusted_TEC_GIM_array - TEC_Jason))

initial_guess = 0.8  # Initial guess for the constant factor

result = minimize(loss_function, initial_guess, args=(TEC_GIM, TEC_Jason), bounds=[(0.4, 1)])
best_factor = result.x[0]
print("Best factor: ", best_factor)
TEC_GIM_constf = TEC_GIM*best_factor
#resultsfile = open("results2.txt", "w").write("delta iono: \n" + str(delta_iono_array) + "\n delta sla: \n" + str(delta_sla_array) + "\n difference: \n" + str(delta_iono_array-delta_sla_array))
#resultsfile.close()


plt.plot(TEC_GIM, label = "GPS TEC")
plt.plot(TEC_Jason, label = "JASON TEC")
plt.plot(TEC_GIM_constf, label = "GPS TEC corrected to JASON altitude")

plt.legend()
plt.show()



'''
unsmoothed= 'j3_2016_summer_unsmoothed_test.nc'
smoothed = 'j3_2016_summer_test.nc'

unsmoothed_time_list, unsmoothed_lat_array, unsmoothed_lon_array, unsmoothed_sla_array = extract_rads(unsmoothed)
smoothed_time_list, smoothed_lat_array, smoothed_lon_array, smoothed_sla_array = extract_rads(smoothed)

if(smoothed_time_list != unsmoothed_time_list):
    print("Error: Time lists do not match")
    exit()

if(corrected_lat_array.any() != uncorrected_lat_array.any()):
    print("Error: Latitude lists do not match")
    exit()

if(corrected_lon_array.any() != uncorrected_lon_array.any()):
    print("Error: Longitude lists do not match")
    exit()


plt.plot(extract_rads(unsmoothed)[3], label = "unsmoothed")
plt.plot(extract_rads(smoothed)[3], label = "smoothed")
plt.legend()
plt.show()
'''
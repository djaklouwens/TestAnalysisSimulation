import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import linregress

from directory_paths import project_dir as pj
from tec_interpolation import mass_interpolate, delete_failed_indices
from rads_extraction import extract_rads_pro

print(f"starting {__name__}.py")

# Parameters
nlags: int = 50
radius: int = 500
max_points: int = 300
del_temp: bool = False
max_size: int = None
max_lat: float = None

# Extract the RADS data

corrected_file_name = os.path.join(pj, r'RADS\\03_22_01_data\\j3_240122.asc')
uncorrected_file_name = os.path.join(pj, r'RADS\\03_22_01_data\\j3_240122_noiono.asc')

print("Selected SLA files: ", corrected_file_name," and " , uncorrected_file_name)
print("Extracting RADS data")

corrected_extraction, uncorrected_extraction = extract_rads_pro(corrected_file_name, uncorrected_file_name, max_lat=max_lat, max_size=max_size)
corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array = corrected_extraction
uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array = uncorrected_extraction

print("Data files match")
print("RADS Extraction successful!")
# Interpolate the TEC data
TEC_GIM, failed_indices = mass_interpolate(corrected_lon_array, corrected_lat_array, corrected_time_list, nlags = nlags, radius = radius, max_points = max_points, del_temp = del_temp)
corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array = delete_failed_indices(failed_indices, corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array)
uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array = delete_failed_indices(failed_indices, uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array)

print(f'Number of failed indices: {len(failed_indices)}')

delta_sla_array = corrected_sla_array - uncorrected_sla_array
print (f"delta_sla_array (size: {delta_sla_array.size}): {delta_sla_array}")
print (f"TEC_GIM results: (size: {TEC_GIM.size}): {TEC_GIM}")

freq = 13.575*10**9
TEC_Jason = delta_sla_array/(40.3/freq**2)/ 10**16

# Find factor by minimizing sum of absolute differences
def loss_function(factor, TEC_GIM, TEC_Jason):
    adjusted_TEC_GIM_array = TEC_GIM * factor
    return np.sum(np.abs(adjusted_TEC_GIM_array - TEC_Jason))

initial_guess = 0.8  # Initial guess for the constant factor

result = minimize(loss_function, initial_guess, args=(TEC_GIM, TEC_Jason), bounds=[(0.4, 1)])
factor_minimizing = result.x[0]
TEC_GIM_constf_minimizing = TEC_GIM*factor_minimizing
print("Factor minimizing: ", factor_minimizing)

# Find factor by linear regression

slope, intercept, r_value, p_value, std_err = linregress(TEC_GIM, TEC_Jason)
print("Factor regression: ", slope, " intercept: ", intercept)
TEC_GIM_constf_regression = TEC_GIM*slope + intercept

plt.scatter(TEC_GIM, TEC_Jason, label='Raw GIM TEC')
plt.plot(TEC_GIM, TEC_GIM_constf_regression, color = 'red', label = "Corrected GIM TEC (reg.)")
plt.plot(TEC_GIM, TEC_GIM_constf_minimizing, color = 'green', label = "Corrected GIM TEC (min.)")
plt.xlabel('GIM TEC')
plt.ylabel('Jason 3 TEC')
plt.legend()
plt.show()

plt.plot(TEC_GIM, label = "RAW GIM TEC")
plt.plot(TEC_Jason, label = "JASON TEC")
plt.plot(TEC_GIM_constf_regression, color = 'red', label = "Corrected GIM TEC (reg.)")
plt.plot(TEC_GIM_constf_minimizing, color = 'green', label = "Corrected GIM TEC (min.)")
plt.ylabel('TEC')
plt.xlabel('Index')
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
from rads_extraction import extract_rads
from tec_interpolation import mass_interpolate
import matplotlib.pyplot as plt

from gim_tools import save_GIMs

# Extract the RADS data

#corrected_file_name = 'c2_2016_summer.nc'
#uncorrected_file_name = 'c2_2016_summer_no_iono.nc'

unsmoothed_file_name = 'j3_2016_summer_unsmoothed.nc'
corrected_file_name = 'j3_2016_summer.nc'
uncorrected_file_name = 'j3_2016_summer_no_iono.nc'
print("Selected SLA files: ", corrected_file_name," and " , uncorrected_file_name)
print("Extracting RADS data")
corrected_time_list, corrected_lat_array, corrected_lon_array, corrected_sla_array = extract_rads(corrected_file_name)
uncorrected_time_list, uncorrected_lat_array, uncorrected_lon_array, uncorrected_sla_array = extract_rads(uncorrected_file_name)
unsmoothed_time_list, unsmoothed_lat_array, unsmoothed_lon_array, unsmoothed_sla_array = extract_rads(unsmoothed_file_name)


def checkdatafilematch(datafile1, datafile2):
    time_list1, lat_array1, lon_array1, sla_array1 = extract_rads(datafile1)
    time_list2, lat_array2, lon_array2, sla_array2 = extract_rads(datafile2)

    if(time_list1 != time_list2):
        print("Error: Time lists do not match")
        exit()

    if(lat_array1.any() != lat_array2.any()):
        print("Error: Latitude lists do not match")
        exit()

    if(lon_array1.any() != lon_array2.any()):
        print("Error: Longitude lists do not match")
        exit()

checkdatafilematch(unsmoothed_file_name, uncorrected_file_name)
checkdatafilematch(corrected_file_name, uncorrected_file_name)
print("Data files match")
delta_sla_array = corrected_sla_array - uncorrected_sla_array
delta_sla_unsmoothed_array = unsmoothed_sla_array - uncorrected_sla_array
print("RADS Extraction successful!")
# Interpolate the TEC data
TEC_results = mass_interpolate(corrected_lon_array, corrected_lat_array, corrected_time_list)
print("TEC_results; " , TEC_results)

freq = 13.575*10**9
delta_iono_array = (40.3/freq**2) * ((TEC_results*10**16)) #0.881 jason, 0.84 c2
delta_iono_array_constf = delta_iono_array*0.73

#resultsfile = open("results2.txt", "w").write("delta iono: \n" + str(delta_iono_array) + "\n delta sla: \n" + str(delta_sla_array) + "\n difference: \n" + str(delta_iono_array-delta_sla_array))
#resultsfile.close()
print("delta_iono; " ,delta_iono_array)
print("delta_sla; " , delta_sla_array)
print("difference; " , delta_iono_array-delta_sla_array)

plt.plot(delta_iono_array, label = "delta iono")
plt.plot(delta_sla_array, label = "delta sla")
#plt.plot(delta_iono_array_constf, label = "delta iono constf")
#plt.plot(delta_iono_array-delta_sla_array, label = "difference")
#plt.plot(delta_iono_array_constf-delta_sla_array, label = "difference constf")
plt.plot(delta_sla_unsmoothed_array, label = "delta sla unsmoothed")
plt.legend()
plt.show()


unsmoothed= 'j3_2016_summer_unsmoothed_test.nc'
smoothed = 'j3_2016_summer_test.nc'

unsmoothed_time_list, unsmoothed_lat_array, unsmoothed_lon_array, unsmoothed_sla_array = extract_rads(unsmoothed)
smoothed_time_list, smoothed_lat_array, smoothed_lon_array, smoothed_sla_array = extract_rads(smoothed)
'''
if(smoothed_time_list != unsmoothed_time_list):
    print("Error: Time lists do not match")
    exit()

if(corrected_lat_array.any() != uncorrected_lat_array.any()):
    print("Error: Latitude lists do not match")
    exit()

if(corrected_lon_array.any() != uncorrected_lon_array.any()):
    print("Error: Longitude lists do not match")
    exit()

'''
plt.plot(extract_rads(unsmoothed)[3], label = "unsmoothed")
plt.plot(extract_rads(smoothed)[3], label = "smoothed")
plt.legend()
plt.show()
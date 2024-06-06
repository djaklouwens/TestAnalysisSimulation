import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

import alert
import rads_extraction
import tec_interpolation
import integration_tools
import datetime_tools as dt_extra
from directory_paths import res_dir


# the beta is particular to the sentinel-3a!
alpha, beta =  integration_tools.alpha, integration_tools.beta_S3

# fetching the data
alert.print_status('Start Extracting RADS Files')
data = rads_extraction.extract_rads_pro(corrected_file=r'RADS\\final_data\\s3a_2016_1500.nc',
                                        uncorrected_file=r'RADS\\final_data\\s3a_2016_1500_noiono.nc',
                                        gimfile=r'RADS\\final_data\\s3a_2016_1500_gim.nc',
                                        max_lat=55)

time, lat, lon, sla_true        = data[0] 
time, lat, lon, sla_uncorrected = data[1]
time, lat, lon, sla_RADS_gim    = data[2]
time, lat, lon, (sla_MIC_gim, sla_unscaled), failed_indices = integration_tools.mic(alpha=(alpha, 1), beta=(beta, 1), time=time, lat=lat, lon=lon, sla_uncorrected=sla_uncorrected)
alert.print_status('Finish Extracting RADS Files')

# remove failed entries in interpolation, to make comparison fair
time, lat, lon, sla_uncorrected = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_uncorrected)
time, lat, lon, sla_true        = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_true       )
time, lat, lon, sla_RADS_gim    = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_RADS_gim   )

# post-processing
alert.print_status('Start Processing')
diff_unscaled = sla_unscaled - sla_true
diff_MIC      = sla_MIC_gim - sla_true
diff_RADS_gim = sla_RADS_gim - sla_true

diff_arr = np.array([diff_unscaled, diff_MIC, diff_RADS_gim])

unit_change = 100 # convert from m to cm

mean_arr = np.mean(unit_change*diff_arr, axis=-1)
std_arr  = np.std (unit_change*diff_arr, axis=-1)

# printing the results
print(f'       | Unscaled | MIC | RADS GIM')
print(f'Mean   | {mean_arr}')
print(f'STD    | {std_arr}')

alert.print_status('Finish Processing')

# ----------- saving the data ----------------------------

# setting up the filenames
basefname = f'{dt.datetime.now():%Y-%m-%d %H.%M} - S3A - a={alpha} b={beta}'
datafile = os.path.join(res_dir, basefname+'.txt')
rawdatafile = os.path.join(res_dir, basefname+'_raw.csv')

# changing the times array
dates = [dt_extra.get_datetime_obj(time_i) for time_i in time]

# storing data
cols = ['Time', 'Lat', 'Lon', 'MIC Unscaled', 'MIC', 'RADS GIM']

# raw data
export_arr = np.append(np.array([dates, lat, lon], dtype='O'), diff_arr, axis=0).T
print(export_arr.shape)
df_raw = pd.DataFrame(export_arr, columns=cols)
with open(rawdatafile, 'a') as f:
    df_raw.to_csv(path_or_buf=f, sep=',', lineterminator='\n')

# summary data
df_tab = pd.DataFrame([mean_arr, std_arr], ['Mean (cm)', 'Std (cm)'], cols[3:])
with open(datafile, 'a') as f:
    df_tab.to_string(buf=f)


alert.print_status('Program Complete')
alert.play_sound()

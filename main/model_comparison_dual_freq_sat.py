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
from directory_paths import project_dir, res_dir

# the beta is particular to the sentinel-3a!
alpha, beta =  integration_tools.alpha, integration_tools.beta_S3

# fetching the data
alert.print_status('Start Extracting RADS Files')
corrected_file   = r'RADS\\03_22_01_data\\s3a_240122.asc'
uncorrected_file = r'RADS\\03_22_01_data\\s3a_240122_noiono.asc'
gim_file = r'RADS\\03_22_01_data\\s3a_240122_gim.asc'
pass_n = 30

data = rads_extraction.extract_rads_pro(corrected_file=os.path.join(project_dir,corrected_file),
                                        uncorrected_file=os.path.join(project_dir,uncorrected_file),
                                        gimfile=os.path.join(project_dir,gim_file),
                                        max_lat=55,
                                        pass_n=pass_n)

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
basefname = f'{dt.datetime.now():%Y-%m-%d %H.%M} - S3A (pass {pass_n:>02}) - a={alpha:.4f} b={beta:.4f}'
datafile = os.path.join(res_dir, basefname+'.txt')
rawdatafile = os.path.join(res_dir, basefname+'_raw.csv')

# changing the times array
dates = [dt_extra.get_datetime_obj(time_i) for time_i in time]

# storing data
cols = ['Time', 'Lat', 'Lon', 'MIC Unscaled', 'MIC', 'RADS GIM']

# raw data
export_arr = np.append(np.array([dates, lat, lon], dtype='O'), diff_arr, axis=0).T
df_raw = pd.DataFrame(export_arr, columns=cols)
with open(rawdatafile, 'a') as f:
    df_raw.to_csv(path_or_buf=f, sep=',', lineterminator='\n')

# summary data
df_tab = pd.DataFrame([mean_arr, std_arr], ['Mean (cm)', 'Std (cm)'], cols[3:])
with open(datafile, 'a') as f:
    df_tab.to_string(buf=f)


alert.print_status('Program Complete')
alert.play_sound()

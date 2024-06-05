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
from directory_paths import res_dir


# the beta is particular to the sentinel-3a!
alpha, beta =  integration_tools.alpha, integration_tools.beta_S3

# fetching the data
alert.print_status('Start Extracting RADS Files')
data = rads_extraction.extract_rads_pro(corrected_file=r'final_data\\s3a_2016_1500.nc',
                                        uncorrected_file=r'final_data\\s3a_2016_1500_noiono.nc',
                                        gimfile=r'final_data\\s3a_2016_1500_gim.nc',
                                        max_lat=55)

time, lat, lon, sla_true        = data[0] 
time, lat, lon, sla_uncorrected = data[1]
time, lat, lon, sla_RADS_gim    = data[2]
time, lat, lon, (sla_IMIC_gim, sla_unscaled), failed_indices = integration_tools.imic(alpha=(alpha, 1), beta=(beta, 1), time=time, lat=lat, lon=lon, sla_uncorrected=sla_uncorrected)
alert.print_status('Finish Extracting RADS Files')

# remove failed entries in interpolation, to make comparison fair
time, lat, lon, sla_uncorrected = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_uncorrected)
time, lat, lon, sla_true        = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_true       )
time, lat, lon, sla_RADS_gim    = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_RADS_gim   )

# post-processing
alert.print_status('Start Processing')
diff_unscaled = sla_unscaled - sla_true
diff_IMIC     = sla_IMIC_gim - sla_true
diff_RADS_gim = sla_RADS_gim - sla_true

diff_arr = np.array([diff_unscaled, diff_IMIC, diff_RADS_gim])

unit_change = 100 # convert from m to cm

mean_arr = np.mean(unit_change*diff_arr, axis=-1)
std_arr  = np.std (unit_change*diff_arr, axis=-1)

# printing the results
print(f'       | Unscaled | IMIC | RADS GIM')
print(f'Mean   | {mean_arr}')
print(f'STD    | {std_arr}')

alert.print_status('Finish Processing')
# ----------- plotting and saving ------------------------

# setting up the filenames
basefname = f'{dt.datetime.now():%Y-%m-%d %H.%M} - S3A - a={alpha} b={beta}'
datafile = os.path.join(res_dir, basefname+'.txt')
rawdatafile = os.path.join(res_dir, basefname+'_raw.csv')
plotfile = os.path.join(res_dir, basefname+'.png') 

# changing the times array
dates = [dt.datetime.fromisoformat(integration_tools.time_convert(date)) for date in time]

# storing data
cols = ['Time', 'Lat', 'Lon', 'Unscaled', 'IMIC', 'RADS GIM']

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


# plotting data

# setting the x-axis appropriately
dates = [dt.datetime.fromisoformat(integration_tools.time_convert(date)) for date in time]
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=50))
plt.gcf().autofmt_xdate()

# actual plotting
plt.plot(dates, unit_change*diff_unscaled, color='orange', alpha=0.6, label=r'unscaled MIC')
plt.plot(dates, unit_change*diff_IMIC    , color='green' , alpha=0.6, label='scaled MIC')
plt.plot(dates, unit_change*diff_RADS_gim, color='blue'  , alpha=0.6, label='RADS GIM')

# making the figure pretty
plt.grid(True, alpha=0.6)
plt.legend()
plt.xlabel('Time')
plt.ylabel('diff wrt. dual-frequency measurement [cm]')

# saving and showing
plt.savefig(plotfile, dpi=400)

alert.print_status('Program Complete')
alert.play_sound()

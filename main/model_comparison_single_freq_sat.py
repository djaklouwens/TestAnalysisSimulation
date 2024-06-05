import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

import alert
import rads_extraction
import tec_interpolation
from directory_paths import res_dir
import integration_tools
import datetime_tools as dt_extra

# the beta is particular to the cryosat-2!
alpha, beta = integration_tools.alpha, integration_tools.beta_CS

# fetching the data
alert.print_status('Start Extracting RADS Files')
data = rads_extraction.extract_rads_pro(corrected_file=r'final_data\\c2_2016_18000.nc',
                                        uncorrected_file=r'final_data\\c2_2016_18000_noiono.nc')

time, lat, lon, sla_RADS_gim        = data[0] 
time, lat, lon, sla_uncorrected = data[1]

time, lat, lon, (sla_IMIC_gim, sla_unscaled), failed_indices = integration_tools.imic(alpha=(alpha, 1), beta=(beta, 1), time=time, lat=lat, lon=lon, sla_uncorrected=sla_uncorrected)
alert.print_status('Finish Extracting RADS Files')

# remove failed entries in interpolation, to make comparison fair
time, lat, lon, sla_uncorrected = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_uncorrected)
time, lat, lon, sla_RADS_gim    = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_RADS_gim   )

# post-processing
alert.print_status('Start Processing')

sla_arr = diff_arr = np.array([sla_unscaled, sla_IMIC_gim, sla_RADS_gim, sla_uncorrected])

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
basefname = f'{dt.datetime.now():%Y-%m-%d %H.%M} - CS2 - a={alpha} b={beta}'
datafile = os.path.join(res_dir, basefname+'.txt')
plotfile = os.path.join(res_dir, basefname+'.png')

## storing data
df = pd.DataFrame([mean_arr, std_arr], ['Mean (cm)', 'Std (cm)'], ['IMIC Unscaled', 'IMIC', 'RADS GIM','Uncorrected'])

with open(datafile, 'a') as f:
    df.to_string(buf=f)

#plotting data

# setting the x-axis appropriately
dates = [dt.datetime.fromisoformat(dt_extra.convert_time_date_for_plotting(date)) for date in time]
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=50))
plt.gcf().autofmt_xdate()

# actual plotting
plt.plot(dates, unit_change*sla_unscaled, color='orange'   , label=r'unscaled IMIC model ($\alpha=\beta=1$)')
plt.plot(dates, unit_change*sla_IMIC_gim, color='green'    , label='scaling with IMIC model')
plt.plot(dates, unit_change*sla_RADS_gim, color='blue'     , label='scaling with RADS GIM model')
plt.plot(dates, unit_change*sla_uncorrected, color='black' , label='uncorrected data')

# making the figure pretty
plt.grid(True, alpha=0.6)
plt.legend()
plt.xlabel('Time')
plt.ylabel('sea level anomaly [cm]')

# saving and showing
plt.savefig(plotfile, dpi=300)

alert.print_status('Program Complete')
alert.play_sound()
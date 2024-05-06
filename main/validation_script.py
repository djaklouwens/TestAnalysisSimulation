import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

import rads_extraction
import tec_interpolation
from directory_paths import plot_dir


def time_convert(date:str):
    '''
    Function that converts a date string from "HH:MM DD/MM/YYYY" to "YYYY-MM-DDTHH:MM:SS"
    '''
    date = date.split(' ')
    time = date[0].split(':')
    date = date[1].split('/')
    return f'{date[2]}-{date[1]}-{date[0]}T{time[0]}:{time[1]}:00'


def imic(alpha, beta, f=13.575e9, filename=None):
    '''docstring TODO'''
    tecu = 1e16
        
    time, lat, lon, sla_uncorrected = rads_extraction.extract_rads(filename) #TODO check filenames
    tec_GPS = tec_interpolation.mass_interpolate(lon, lat, time)
    
    if isinstance(alpha, float) or isinstance(alpha, int):
        return time, lat, lon, (40.3/f**2)*alpha*beta*(tec_GPS*tecu) + sla_uncorrected
    else:
        sla = [(40.3/f**2)*alpha[i]*beta[i]*(tec_GPS*tecu) + sla_uncorrected for i in range(len(alpha))]
        return time, lat, lon, tuple(sla)


# the beta is particular to the sentinel-3a!
alpha, beta = 0.8452, 0.936

# fetching the data
time_1, lat, lon, sla_uncorrected = rads_extraction.extract_rads(r'final_data\\s3a_2016_1500_noiono.nc') #TODO check filenames
time_2, lat, lon, sla_true        = rads_extraction.extract_rads(r'final_data\\s3a_2016_1500.nc')        #TODO check filenames
time_3, lat, lon, sla_RADS_gim    = rads_extraction.extract_rads(r'final_data\\s3a_2016_1500_noiono.nc') #TODO check filenames
time_4, lat, lon, (sla_IMIC_gim, sla_unscaled) = imic(alpha=(alpha, 1), beta=(beta, 1), filename=r'final_data\\s3a_2016_1500_noiono.nc')

time_lst = [time_1, time_2, time_3, time_4]
check = [all(x == y for y in time_lst) for x in time_lst] # ensure that data is consistent

# post-processing
diff_unscaled = sla_unscaled - sla_true
diff_IMIC     = sla_IMIC_gim - sla_true
diff_RADS_gim = sla_unscaled - sla_true

diff_arr = np.array([diff_unscaled, diff_IMIC, diff_RADS_gim])

unit_change = 100 # convert from m to cm

mean_arr = np.mean(unit_change*diff_arr, axis=-1)
std_arr  = np.std( unit_change*diff_arr, axis=-1)
# printing the results
print(f'       | Unscaled | IMIC | RADS GIM')
print(f'Mean   | {mean_arr}')
print(f'STD    | {std_arr}')

# ----------- plotting ----------------

# setting the x-axis appropriately
dates = [dt.datetime.fromisoformat(time_convert(date)) for date in time_1]
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=50))
plt.gcf().autofmt_xdate()

# actual plotting
plt.plot(dates, unit_change*diff_unscaled, color='orange', label=r'unscaled IMIC model ($\alpha=\beta=1$)')
plt.plot(dates, unit_change*diff_IMIC    , color='green' , label='scaling with IMIC model')
plt.plot(dates, unit_change*diff_RADS_gim, color='blue'  , label='scaling with RADS GIM model')

# making the figure pretty
plt.grid(True, alpha=0.6)
plt.legend()
plt.xlabel('Time')
plt.ylabel('diff wrt. dual-frequency measurement [cm]')

# saving and showing
plt.savefig(os.path.join(plot_dir, 'sentinel3a validation.png'), dpi=300)
plt.show()
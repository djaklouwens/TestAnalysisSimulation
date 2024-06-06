import os
import re
import gzip
import shutil
import requests
from typing import List

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import netCDF4 as nc

from directory_paths import project_dir, temp_dir, plot_dir, illegal_char
import datetime_tools as dt_extra


def get_timeslot(time:List):
    ''' 
    Function to return the nearest time slot (of TEC map) for a given time.
    If the time matches exactly with the time slot, only that timeslot is returned. 
    If the time is in between 2 time slots, those 2 time slots are returned.
    
    Recall that GIM maps have time resolution of 15 minutes.
    
    Parameters
    ----------
    time: List (in the form [hh, mm, ss])
    
    Returns
    -------
    timeslot: INT or np.ndarray([INT, INT])
    '''

    tim1 = 4*time[0] + time[1]//15 
    tim2 = tim1 +1

    if time[1]%15 == 0:
        return tim1
    else:
        return np.array([tim1, tim2])
    

def get_time(timeslot:int, rtype='str'):
    '''
    Function that obtains the time for a given timeslot, and handles 
    both strings and arrays.
    '''

    tot_minutes = 15 * timeslot
    hours = tot_minutes//60
    minutes = tot_minutes - hours*60        

    if rtype=='str':
        if not isinstance(timeslot, int):
            return [f'{hours[i]:>02}:{minutes[i]:>02}:00' for i in range(len(timeslot))]
        else:
            return f'{hours:>02}:{minutes:>02}:00'
    elif rtype=='array':
        if not isinstance(timeslot, int):
            return [[hours[i], minutes[i], 00] for i in range(len(timeslot))]
        else:
            return [hours, minutes, 00]

def construct_url(time_date:str, 
                  url_base:str=r'https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/')->str:
    '''
    Function to build the url to download file. URL is in the form:
    https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/jpld/YYYY/jpldDOY0.YYi.nc.gz
    where:
    - YYYY: year
    - DOY: day of year
    - YY: last two digits of year

    Notice that by default jpld files are fetched, in preference of jpli or jplg, as there is 
    more availability of data.

    Parameters:
    -----------
    time_date: STR
        Time and date in the format 'hh:mm DD/MM/YYYY'. This date must be one that 
        exists on the database.
    url_base: STR 
        Base url, by default set to: 'https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/'
    
    Returns
    -------
    url: STR
    '''

    jpl_type = 'jpld'

    url_base += f'{jpl_type}/'

    date = dt_extra.split_time_date(time_date)[1]
 
    fname = f'{jpl_type}{dt_extra.get_day_num(date):>03}0.{str(date[2])[-2:]:>02}i.nc.gz'

    return f'{url_base}/{date[2]}/{fname}'

def download_file(url:str, save_dir:str=temp_dir, unzip:bool=False)->None:
    ''' 
    Function to download a file from a url. Adapted from :
    https://realpython.com/python-download-file-from-url/#saving-downloaded-content-to-a-file
    
    Parameters
    ----------
    url: STR 
        Specify url in a string
    save_dir : STR
        Specify path for the downloaded file

    Returns
    -------
    None
    '''
   
    response = requests.get(url)
    
    if "content-disposition" in response.headers:
        content_disposition = response.headers["content-disposition"]
        filename = content_disposition.split("filename=")[1]
    else:
        filename = url.split("/")[-1]
    
    with open(os.path.join(save_dir, filename), mode="wb") as file:
        file.write(response.content)


    if unzip:
        decompress(os.path.join(save_dir, filename), os.path.join(save_dir, os.path.splitext(filename)[0]))
        
def decompress(infile:str, outfile:str)->None:
    ''' 
    Function to decompress a .gz file. Copied from:
    https://docs.python.org/2/library/gzip.html#examples-of-usage
    
    Parameters
    ----------
    infile: STR
        Path of .gz file
    outfile: STR
        Path of extracted file
    
    Returns
    -------
    None
    '''
    with gzip.open(infile, 'rb') as f_in, open(outfile, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        print("Downloaded and decompressed: " + re.split(r'\\', infile)[-1])


def fetch_GIM_files(times_dates, save_dir:str=temp_dir):
    '''
    Function to fetch the GIM file(s) associated with times_dates.

    Parameters
    ----------
    times_dates: STR or LIST[STR]
        STR must be in the format : 'hh:mm DD/MM/YYYY'
    save_dir: STR
        Specify path for the downloaded file
    
    Returns
    -------
    fpath_lst: STR or LIST[STR]
        (List of) filepaths of downloaded .netCDF4 files.
    '''
    # accept single dates passed as strings
    if isinstance(times_dates, str):
        times_dates = [times_dates]

    fpath_lst = []

    for time_date in times_dates:
    # construct url and extract filename and filepath of .netCDF4 file
        url = construct_url(time_date)
        fname = re.split(r'/', url)[-1]
        file_path = os.path.join(save_dir, os.path.splitext(fname)[0])
        fpath_lst.append(file_path)

    # download the file if it does not exist yet
        if not os.path.isfile(file_path):
            # print(f"Downloading {fname}...")
            download_file(url, save_dir=save_dir, unzip=True)
            assert os.path.isfile(file_path), 'File incorrectly downloaded'
    
    # return string if single date was passed
    if len(fpath_lst) == 1:
        return fpath_lst[0]
    else:
        return fpath_lst

def get_GIM(time_date:str, plot:bool=False, 
            del_temp:bool=True, save_dir:str=temp_dir)->tuple:
    '''
    Function to extract the worldwide JPL GIM TEC maps for a given day/time and 
    time resolution. If the exact time is not found, the nearest times 
    are returned.

    Parameters
    ----------
    time_date: STR
        Specify date and time in the format 'hh:mm DD/MM/YYYY'
    plot : BOOL
        Decide if the TEC maps will be plotted (by default False)
    del_temp : BOOL
        Decide if the temp directory will be deleted after execution 
        (by default True)
    save_dir : STR
        Specify the save directory of the downloaded and netCDF4 files.
        By default, a temporary directory.

    Returns
    -------
    (tec_maps, time_str)
        tec_maps: NDARRAY
            One (or two) 180x360 arrays with TEC content
        times_str: STR
            One (or two) strings indicating the time associated with
            TEC map
    '''

    # jpld map doesn't have the TEC map associated with time 00.00 of the 
    # next day in the NetCDF file (epoch 97). The following lines of code
    # address this issue by downloading and storing the map of the next day 
    
    # initialise a flag for later use (function return)
    next_day_map = False
    time = dt_extra.split_time_date(time_date)[0]
    date = dt_extra.split_time_date(time_date)[1]

    # the issue only occurs when the time is between 23.45 and 24.00
    if (time[0]==23 and time[1]>45): 
        new_date = dt_extra.get_next_day(date)
        
        # construct the next time date to fetch the map
        next_time_date = f'00:00:00 {new_date[0]}/{new_date[1]}/{new_date[2]}'

        # recover the map recursively
        next_GIM_map, next_time_str = get_GIM(next_time_date, del_temp=False)

        # reset the original time_date 
        time_date = f'23:45:00 {date[0]}/{date[1]}/{date[2]}'
        next_day_map = True

    # fetch GIM file
    file_path = fetch_GIM_files(time_date, save_dir=save_dir)

    # identify nearest timeslots (and associated times)
    og_time   = dt_extra.split_time_date(time_date)[0]
    timeslots = get_timeslot(og_time)
    times_str = get_time(timeslots)

    # open file, read file and close the file
    try:
        ds = nc.Dataset(file_path)
        GIM_maps = ds['tecmap'][timeslots, :].data
    finally:
        ds.close()

    if next_day_map:
        assert isinstance(times_str, str)
        GIM_maps = np.array([GIM_maps, next_GIM_map])
        times_str = [times_str, next_time_str]

    # plotting
    if plot:
        if isinstance(times_str, str):
            plot_TEC(GIM_maps, times_str)
        else:
            plot_TEC(GIM_maps[0], times_str[0])
    
    # delete temporary directory if desired
    if del_temp:
        shutil.rmtree(save_dir)

    return GIM_maps, times_str

def no_iplot(func):
    '''Decorator to turn off and on the interactive mode in matplotlib'''
    def wrapper(*args, **kwargs):
        plt.ioff()
        func(*args, **kwargs)
        plt.ion()
    return wrapper

@no_iplot 
def plot_TEC(tec_map:np.ndarray, time_date:str, grid=True, save_fig=False, fpath=plot_dir, 
             fname='default'):
    '''Function to plot a filled contour plot of TEC on a worldwide map.'''
    lat_ = np.arange(-89.5, 89.6)
    lon_ = np.arange(-179.5, 179.6)
    lat, lon = np.meshgrid(lat_, lon_)
    title_pad = 6
    cbar_pad = '2%'

    fig, ax = plt.subplots(figsize=(14, 8))
    earth = Basemap()
    cntr = earth.contourf(lon, lat, tec_map.T, levels=100, cmap="RdBu_r", 
                          latlon=True, vmin=0, vmax=27)
    earth.drawcoastlines(color='#555566', linewidth=0.5)

    if grid:
        title_pad = 30
        cbar_pad = '8%'
        grid_style = {'linewidth': 0.2, 'dashes':[1,0], 
                      'labels':[1, 1, 1, 1], 'labelstyle':'+/-'}
        earth.drawmeridians(np.arange(-180, 181, 20), **grid_style)
        earth.drawparallels(np.arange(-90, 91, 30), **grid_style)
    
    ax.set_title(f'TEC Map {time_date}', pad=title_pad)
    earth.colorbar(cntr, ax=ax, label=f'TEC (TECU)', pad=cbar_pad, size='2%')

    if save_fig:
        if fname == 'default':
            fname = f'TEC Map {time_date}.png'
            fname = re.sub(illegal_char, '-', fname)
        
        plt.savefig(os.path.join(fpath, fname), dpi=200)
    plt.show()

if __name__=='__main__':
    time_date = '13.20.00 04/03/2015'
    print(project_dir)


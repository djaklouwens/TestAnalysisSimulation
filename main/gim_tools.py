import os
import re
import gzip
from typing import List
import shutil
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import netCDF4 as nc
import requests

from directory_paths import project_dir, temp_dir, plot_dir, illegal_char

def isleap(year:int)->bool:
    ''' Function to check if a year is a leap year '''    
    
    if year > 1582: # Gregorian Calendar
        return (year % 4 == 0 and year % 100 != 0 or year % 400 == 0)
    else:           # Julian Calendar
        return (year % 4 == 0)

def get_day_num(date:List)->int:
    ''' Function to get the number of days since the first of January of that year '''

    # initialise days of month
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if isleap(date[-1]):
        months[1] = 29

    day = 0
    for i in range(date[1]-1):
        day += months[i]
    day += date[0]

    return day

def get_timeslot(time:List, time_res:int=0):
    ''' 
    Function to return the nearest time slot (of TEC map) for a given time.
    If the time matches exactly with the time slot, only that timeslot is returned. 
    If the time is in between 2 time slots, those 2 time slots are returned.
    
    time_res: INT
        Selected time resolution. 0 if 15 minute, 1 if 2 hour. By default, 
        the 15min dataset is chosen.
    
    '''
    if time_res == 0:
        tim1 = 4*time[0] + time[1]//15 
        tim2 = tim1 +1
        if time[1]%15 == 0:
            return tim1

        if time[1]%15 != 0:
            return np.array([tim1, tim2])
    
    if time_res == 1:
        tim1 = time[0]//2
        tim2 = tim1 +1
        if time[0]%2 == 0:
            return tim1

        if time[0]%2 != 0:
            return np.array([tim1, tim2])

   

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
   
    # download file
    response = requests.get(url)
    
    if "content-disposition" in response.headers:
        content_disposition = response.headers["content-disposition"]
        filename = content_disposition.split("filename=")[1]
    else:
        filename = url.split("/")[-1]
    
    with open(os.path.join(save_dir, filename), mode="wb") as file:
        file.write(response.content)

    print(f"Downloaded {filename}!")

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
        print('Decompressed ' + re.split(r"\\", infile)[-1] + '!')


def construct_url(time_date:str, time_res:int=0, 
                  url_base:str=r'https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/')->str:
    '''
    Function to build the url to download file. URL is in the form:
    https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/jplX/YYYY/jplXDOY0.YYi.nc.gz
    where:
    - X: 'i' if 15min time resolution, or 'd' if 2h time resolution
    - YYYY: year
    - DOY: day of year
    - YY: last two digits of year

    Parameters:
    -----------
    time_date: STR
        Time and date in the format 'hh:mm DD/MM/YYYY'. This date must be one that 
        exists on the database.
    time_res: INT
        Selected time resolution. 0 if 15 minute, 1 if 2 hour. By default, 
        the 15min dataset is chosen.
    url_base: STR 
        Base url, by default set to: 'https://sideshow.jpl.nasa.gov/pub/iono_daily/gim_for_research/'
    
    Returns
    -------
    url: STR
    '''

    if time_res == 0:   jpl_type = 'jpli'
    elif time_res == 1: jpl_type = 'jpld'

    url_base += f'{jpl_type}/'

    date = split_time_date(time_date)[1]
 
    fname = f'{jpl_type}{get_day_num(date):>03}0.{str(date[2])[-2:]:>02}i.nc.gz'

    return f'{url_base}/{date[2]}/{fname}'

def split_time_date(time_date):
    ''' 
    Function that splits time_date in the following way
    from   'hh:mm DD/MM/YYYY'    to    ([hh, mm], [DD, MM, YYYY]) 
    '''
    time, date = time_date.split()
    time = [int(i) for i in re.split(r'[:.,]', time)]
    date = [int(i) for i in re.split(r'[-.,/]', date)]
    return time, date

def array_coord(lat, lon):
    row = -lat + 89.5
    column = lon + 179.5
    return (row, column)

def get_time(timeslot:int, rtype='str', time_res:int=0):
    '''
    Function that fetches the time for a given timeslot, and handles 
    both strings and arrays
    TODO: improve doc
    '''
    if time_res == 0:
        tot_minutes = 15 * timeslot
        hours = tot_minutes//60
        minutes = tot_minutes - hours*60
    
    if time_res == 1:
        hours = 2 * timeslot
        minutes = 0 
        

    if rtype=='str':
        if not isinstance(timeslot, int):
            return [f'{hours[i]:>02}:{minutes[i]:>02}' for i in range(len(timeslot))]
        else:
            return f'{hours:>02}:{minutes:>02}'
    elif rtype=='array':
        if not isinstance(timeslot, int):
            return [[hours[i], minutes[i]] for i in range(len(timeslot))]
        else:
            return [hours, minutes]

def no_iplot(func):
    '''Decorator to turn off and on the interactive mode in matplotlib'''
    def wrapper(*args, **kwargs):
        plt.ioff()
        func(*args, **kwargs)
        plt.ion()
    return wrapper

@no_iplot
def plot_TEC(tec_map, time_date, grid=True, save_fig=False, fpath=plot_dir, 
             fname='default'):
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

def get_TEC(time_date:str, time_res:int=0, plot:bool=False, save_dir:str=temp_dir)->tuple:
    '''
    Function to extract the worldwide TEC maps for a given day/time and 
    time resolution. If the exact time is not found, the nearest times 
    are returned.

    Parameters
    ----------
    time_date: STR
        Specify date and time in the format 'hh:mm DD/MM/YYYY'
    time_res: INT
        Selected time resolution. 0 if 15 minute, 1 if 2 hour. By default, 
        the 15min dataset is chosen.
    plot : BOOL
        Decide if the TEC maps will be plotted (by default False)
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

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    # download the file
    url = construct_url(time_date, time_res)
    # determine filename and filepath of .netCDF4 file
    fname = re.split(r'/', url)[-1]
    file_path = os.path.join(save_dir, os.path.splitext(fname)[0])

    attempts = 0
    while not os.path.isfile(file_path) and attempts < 5:
        download_file(url, save_dir=save_dir, unzip=True)
        attempts += 1

    assert attempts <= 5, 'File incorrectly downloaded'

    # identify nearest timeslots (and associated times)
    og_time = split_time_date(time_date)[0]
    timeslots = get_timeslot(og_time)
    times_str = get_time(timeslots)

    # open file, read file and close the file
    try:
        ds = nc.Dataset(file_path)
        tec_maps = ds['tecmap'][timeslots, :].data
    finally:
        ds.close()

    # plotting
    if plot:
        if isinstance(timeslots, int):
            plot_TEC(tec_maps, times_str)
        else:
            plot_TEC(tec_maps[0], times_str[0])
    
    # delete temporary directory if desired
    # if del_temp: #TODO PABLO GUAPO CAMBIA ESTO <3
    #     shutil.rmtree(save_dir)

    return tec_maps, times_str


if __name__=='__main__':
    time_date = '13.20 04/03/2015'
    # TODO finish these few lines and test the code
import os
import warnings

import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import datetime_tools as dt_extra
import alert

warnings.filterwarnings('ignore', category=UserWarning)

def convert_longitude_to_0_360(longitude):
    while longitude < -180:
        longitude += 360
    if longitude < 0:
        longitude += 360
    return longitude

def find_start_passes(file_path, verbose=True):
    '''
    This function reads an .asc data file from RADS and determine the starting
    line of each pass (orbital period).

    Parameters
    ----------
    file_path: STR
        Filepath in question. Must be .asc file!
    verbose: BOOL (default: True)
        Set to True to print the number of passes in the file

    Returns
    -------
    start_pass_lines: List[INT]
        List containing the indexes associated with the line number in the file where
        each pass start.
    
    '''

    if os.path.splitext(file_path)[-1] != '.asc':
        raise TypeError('Searching for distinct passes is only developed for .asc files.')

    with open(file_path, 'r') as f: lines = f.readlines()
    hashtag_lines = np.array([i for i, line in enumerate(lines) if '#' in line])
    diff = np.concatenate((np.array([30]), hashtag_lines[1:] - hashtag_lines[:-1]))
    start_pass_lines = hashtag_lines[diff > 1]

    if verbose:
        print(f'There are {len(start_pass_lines)} passes in ({file_path})')
    
    return start_pass_lines

def set_color(secs, cmap='Spectral'):
    cmap = plt.get_cmap(cmap)
    time_date = dt_extra.get_time_date(secs)
    
    date0 = dt_extra.split_time_date(time_date)[1]
    datef = dt_extra.get_next_day(date0)

    s0 = dt_extra.get_sec_since_1985(date0)
    sf = dt_extra.get_sec_since_1985(datef)

    return cmap((secs-s0)/(sf-s0))

def extract_rads(file_path, pass_n=None, start_pass_lines=None, max_lat=None, 
                 plot=False, earth=Basemap(), recursive=False):

    if os.path.splitext(file_path)[-1].lower() == '.nc':
        try:
            ds = nc.Dataset(file_path)
            secs_array = np.array(ds['time'][:])
            lat_array = np.array(ds['lat'][:])
            lon_array = np.array(ds['lon'][:])
            sla_array = np.array(ds['sla'][:])
        finally:
            ds.close()

        pass_n = 0
    elif os.path.splitext(file_path)[-1].lower() == '.asc':
        if start_pass_lines is None:
            start_pass_lines = find_start_passes(file_path, verbose=False)

        if pass_n is None: # extract all passes
            skiprows = 0
            max_rows = None
            data = extract_rads(file_path, np.arange(1, len(start_pass_lines)+1, 1), 
                                start_pass_lines, plot=plot, earth=earth, recursive=True)

            secs_array = data[0]
            lat_array  = data[1]
            lon_array  = data[2]
            sla_array  = data[3]
               
        elif isinstance(pass_n, (list, np.ndarray)): # extract multiple passes
            assert len(set(pass_n)) == len(pass_n), 'There are repeated pass numbers!'

            secs_array = np.array([])
            lat_array  = np.array([])
            lon_array  = np.array([])
            sla_array  = np.array([])

            for i, n in enumerate(pass_n):
                data_i = extract_rads(file_path, int(n), start_pass_lines, plot=plot, 
                                      earth=earth, recursive=True)

                secs_array = np.append(secs_array, data_i[0])
                lat_array  = np.append(lat_array , data_i[1])
                lon_array  = np.append(lon_array , data_i[2])
                sla_array  = np.append(sla_array , data_i[3])
            
        else: # extract only one pass
            assert pass_n <= len(start_pass_lines), 'There are not that many passes in this file!'
            assert pass_n >= 1

            if pass_n == len(start_pass_lines):
                skiprows = start_pass_lines[pass_n-1]
                max_rows  = None
            else:
                skiprows = start_pass_lines[pass_n-1]
                max_rows = start_pass_lines[pass_n] - start_pass_lines[pass_n-1]

            data = np.loadtxt(file_path, skiprows=skiprows, max_rows=max_rows)

            secs_array = data[:, 0]
            lat_array  = data[:, 1]
            lon_array  = data[:, 2]
            sla_array  = data[:, 3]
               
    else:
        raise TypeError(f'Unaccepted filetype for: {file_path}')
    

    # Apply latitude filter if provided
    if max_lat is not None:
        indices = abs(lat_array) <= max_lat
        secs_array = secs_array[indices]
        lat_array  = lat_array[indices]
        lon_array  = lon_array[indices]
        sla_array  = sla_array[indices]

    # Plot the pass if needed
    if plot and isinstance(pass_n, int):
        color = set_color(np.average(secs_array))

        earth.scatter(lon_array, lat_array, s=20, c=color, marker='X', 
                    linewidths=0.01, label=f'avg. {dt_extra.get_time_date(np.average(secs_array))}', zorder=1)
        ax = plt.gca()
        ax.legend(bbox_to_anchor=(1.06, 0.99), loc='upper left')
    
    if not recursive:
        time_list = [dt_extra.get_time_date(t) for t in secs_array]
        lon_array = np.array([convert_longitude_to_0_360(lon) for lon in lon_array])
        
        return [time_list, lat_array, lon_array, sla_array]

    else:
        return [secs_array, lat_array, lon_array, sla_array]

def del_indices(extractions:list, indices): #works for 1 or more extraction(s) and 1 or more indices
    results = []
    for extraction in extractions:
        for index in sorted(indices, reverse=True):
            del extraction[0][index]
            extraction[1] = np.delete(extraction[1], index, axis=0)
            extraction[2] = np.delete(extraction[2], index, axis=0)
            extraction[3] = np.delete(extraction[3], index, axis=0)
        results.append(extraction)
    return results

def check_extractions(extraction1, extraction2):
    if extraction1[0] != extraction2[0]:
        print("Error: Time lists do not match")
        exit()

    if extraction1[1].any() != extraction2[1].any():
        print("Error: Latitude lists do not match")
        exit()

    if extraction1[2].any() != extraction2[2].any():
        print("Error: Longitude lists do not match")
        exit()
    else:
        return True

def match_extractions(corrected_extraction, uncorrected_extraction, gim_extraction = None): #match extraction2 to extraction1
    # extraction consists of [0] time_list, [1] lat_array, [2] lon_array, [3] sla_array    
    indices_to_delete = []

    # Iterate through time stamps in uncorrected_extraction
    indices_to_delete = []
    for i, time in enumerate(uncorrected_extraction[0]):
        # If the time stamp doesn't exist in corrected_extraction, mark it for deletion
        if time not in corrected_extraction[0]:
            indices_to_delete.append(i)
    
    # Delete the corresponding data from datafile2 arrays
    if gim_extraction is None:
        uncorrected_extraction = del_indices([uncorrected_extraction], indices_to_delete)[0]
        return uncorrected_extraction
    else:
        gim_extraction = del_indices([gim_extraction], indices_to_delete)[0]
        uncorrected_extraction = del_indices([uncorrected_extraction], indices_to_delete)[0]
        return uncorrected_extraction, gim_extraction
  

def simplify_extraction(extraction): # deletes all double entries in the extraction
    indices_to_delete = []

    for i, time in enumerate(extraction[0]):
        if time in extraction[0][:i]:
            indices_to_delete.append(i)            
    extraction = del_indices([extraction], indices_to_delete)[0]

    print(len(indices_to_delete))
    return extraction

def extract_rads_pro(corrected_file, uncorrected_file, gimfile=None, max_lat=None, max_size=None, pass_n=None):
   
    if gimfile is None:
        alert.print_status(f'Start extraction of corrected file: {os.path.split(corrected_file)[-1]}')
        corrected_extraction = simplify_extraction(extract_rads(corrected_file, pass_n=pass_n, max_lat=max_lat))
        alert.print_status(f'Finish extraction of corrected file: {os.path.split(corrected_file)[-1]}')

        alert.print_status(f'Start extraction of uncorrected file: {os.path.split(uncorrected_file)[-1]}')
        uncorrected_extraction = match_extractions(corrected_extraction, simplify_extraction(extract_rads(uncorrected_file, pass_n=pass_n, max_lat=max_lat)))
        alert.print_status(f'Finish extraction of uncorrected file: {os.path.split(uncorrected_file)[-1]}')

        check_extractions(corrected_extraction, uncorrected_extraction)

   # Randomly select points if max_size is provided
        if max_size is not None:
            if len(corrected_extraction[0]) > max_size:     
                indices = np.random.choice(len(corrected_extraction[0]), len(corrected_extraction[0])-max_size, replace=False)
                extractions = del_indices([corrected_extraction, uncorrected_extraction], indices)
                corrected_extraction = extractions[0]
                uncorrected_extraction = extractions[1]
        check_extractions(corrected_extraction, uncorrected_extraction)       
        return corrected_extraction, uncorrected_extraction
    
    else:
        alert.print_status(f'Start extraction of corrected file: {os.path.split(corrected_file)[-1]}')
        corrected_extraction = simplify_extraction(extract_rads(corrected_file, pass_n=pass_n, max_lat=max_lat))
        alert.print_status(f'Finish extraction of corrected file: {os.path.split(corrected_file)[-1]}')

        alert.print_status(f'Start extraction of uncorrected file: {os.path.split(uncorrected_file)[-1]}')
        uncorrected_extraction, gim_extraction = match_extractions(corrected_extraction, simplify_extraction(extract_rads(uncorrected_file, pass_n=pass_n, max_lat=max_lat)), simplify_extraction(extract_rads(gimfile, pass_n=pass_n, max_lat=max_lat)))
        alert.print_status(f'Finish extraction of uncorrected file: {os.path.split(uncorrected_file)[-1]}')

        alert.print_status(f'Start extraction of gim_corrected file: {os.path.split(gimfile)[-1]}')
        gim_extraction = match_extractions(corrected_extraction, simplify_extraction(extract_rads(gimfile, pass_n=pass_n, max_lat=max_lat)))
        alert.print_status(f'Finish extraction of gim_corrected file: {os.path.split(gimfile)[-1]}')

        check_extractions(corrected_extraction, uncorrected_extraction)
        check_extractions(corrected_extraction, gim_extraction)
        check_extractions(uncorrected_extraction, gim_extraction)

   # Randomly select points if max_size is provided
        if max_size is not None:
            if len(corrected_extraction[0]) > max_size:     
                indices = np.random.choice(len(corrected_extraction[0]), len(corrected_extraction[0])-max_size, replace=False)
                extractions = del_indices([corrected_extraction, uncorrected_extraction, gim_extraction], indices)
                corrected_extraction = extractions[0]
                uncorrected_extraction = extractions[1]
                gim_extraction = extractions[2]
                check_extractions(corrected_extraction, uncorrected_extraction)
                check_extractions(corrected_extraction, gim_extraction)
                check_extractions(uncorrected_extraction, gim_extraction)
        
        return corrected_extraction, uncorrected_extraction, gim_extraction
          
import re
from typing import List
import datetime as dt

import numpy as np
    
# initialise days of month
months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def get_time_date(seconds_since_1985:float)->str:
    '''
    Function to get the time date, in the form 'hh:mm:ss DD/MM/YYYY'
    from seconds since 00:00:00 01/01/1985.
    '''
    base_date = dt.datetime(1985, 1, 1, 0, 0, 0)
    target_date = base_date + dt.timedelta(seconds=seconds_since_1985)
    formatted_date = target_date.strftime('%H:%M:%S %d/%m/%Y')
    return formatted_date

def split_time_date(time_date:str, inverse:bool=False):
    ''' 
    Function that splits time_date in the following way:
    (inverse=True)  'YYYY/MM/DD hh:mm:ss'  to  ([hh, mm, ss], [DD, MM, YYYY])
    (inverse=False) 'hh:mm:ss DD/MM/YYYY'  to  ([hh, mm, ss], [DD, MM, YYYY])
    '''
    if inverse: date, time = time_date.split()
    else:       time, date = time_date.split()
    time = [int(i) for i in re.split(r'[:.,-/]', time)]
    date = [int(i) for i in re.split(r'[:.,-/]', date)]

    # swap the year and day
    if inverse: 
        x = date[2]
        date[2] = date[0]
        date[0] = x
    
    return time, date

def get_datetime_obj(time_date:str, inverse:bool=False)->str:
    '''
    Function that converts a date string from 
    (inverse=True ) 'YYYY/MM/DD hh:mm:ss' to a datetime object.
    (inverse=False) 'hh:mm:ss DD/MM/YYYY' to a datetime object.
    '''
    time, date = split_time_date(time_date, inverse=inverse)

    if time[0] == 24:
        date = get_next_day(date)
        time = [0,0,0]

    return dt.datetime(year=date[2], month=date[1], day=date[0],
                       hour=time[0], minute=time[1], second=time[2])

def get_sec_since_1985(date:list)->float:
    '''
    Function to get the number of seconds since 00:00:00 01/01/1985 from
    the date, either as a list in the form [DD, MM, YYYY], or as a datetime 
    object
    '''
    init_date = dt.datetime(1985, 1, 1)

    if type(date) is list:
        date.reverse()
        date = dt.datetime(*date)

    time_since = date - init_date
    seconds = int(time_since.total_seconds())
    return seconds


def isleap(year:int)->bool:
    '''
    Function to check if a year is a leap year
    '''        
    if year > 1582: # Gregorian Calendar
        return (year % 4 == 0 and year % 100 != 0 or year % 400 == 0)
    else:           # Julian Calendar
        return (year % 4 == 0)

def get_day_num(date:list)->int:
    '''
    Function to get the number of days since the first of January of that year
    ''' 

    if isleap(date[-1]):
        months[1] = 29

    day = 0
    for i in range(date[1]-1):
        day += months[i]
    day += date[0]

    return day

def inv_day_number(day:int, year:int):
    '''
    Function to get the date from the day number of the year
    '''

    if isleap(year): months[1] = 29

    for i in range(len(months)):
        if day > 0:
            day -= months[i]
        else:
            break
    
    date = [day + months[i-1], i, year]
    return date

def get_next_day(date:list)->list:
    '''
    Find the next day of the year, taking into account leap years
    and months
    '''
    day_num = get_day_num(date)
    if (day_num == 365 and not isleap(date[2]) or 
        day_num == 366 and     isleap(date[2])):
        new_date = [1, 1, date[2]+1]
    else:
        new_date = inv_day_number(day_num+1, date[2])
    
    return new_date


if __name__ == '__main__':
    test = '2024-01-22 02:11:21'
    
    x = get_datetime_obj(test, inverse=True)
    print(x)


        
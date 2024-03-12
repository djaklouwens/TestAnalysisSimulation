# TestAnalysisSimulation
This is the repository of Group A06 in the Test Analsys and Simulation course of 2024. The aim is to verify that the ionopheric correction in RADS (Radar Altimeter Database System of the TU Delft) is correctly implemented in the Cryosat-2.

## Requirements for Code Repository
Install required dependencies from `requirements.txt`, running the following line in `cmd`:

`pip install -r requirements.txt`

(Maybe create a conda environment?)

## Convention
Functions should be documented like the following example code.

```python
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
        print(f'Decompressed {re.split(r'\\', infile)[-1]}!')
```

If the funciton is very simple, it is okay to document its use, inputs and outputs in single line, for example:

```python
def isleap(year:int)->bool:
    ''' Function to check if a year is a leap year '''    
    
    if year > 1582: # Gregorian Calendar
        return (year % 4 == 0 and year % 100 != 0 or year % 400 == 0)
    else:           # Julian Calendar
        return (year % 4 == 0)
```

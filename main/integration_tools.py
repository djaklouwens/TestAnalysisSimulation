import numpy as np

import tec_interpolation
import rads_extraction
import alert

alpha = 0.9173138576965778
beta_CS = 0.817 
beta_S3 = 0.877

'''
history of beta values
----------------------------
   | 12/02 | 06/02 | 22/01 |
---|-------|-------|-------|
CS | 0.858 | 0.907 | 0.817 |
S3 | 0.903 | 0.938 | 0.877 |
----------------------------
'''


def mic(alpha, beta, f=13.575e9, filepath=None, time=None, lat=None, lon=None, sla_uncorrected=None, **kwargs):
    '''docstring TODO'''
    tecu = 1e16
    
    if filepath is not None:
        time, lat, lon, sla_uncorrected = rads_extraction.extract_rads(filepath, **kwargs) #TODO check filenames
        print("shouldn't be here")
    else:
        assert (time is not None and lat is not None and lon is not None and sla_uncorrected is not None), 'Specify the correct data'
    
    alert.print_status('Start Interpolating')
    tec_GPS, failed_indices = tec_interpolation.mass_interpolate(lon, lat, time, del_temp=False)
    alert.print_status('Finish Interpolating')

    # remove failed entries
    time, lat, lon, sla_uncorrected = tec_interpolation.delete_failed_indices(failed_indices, time, lat, lon, sla_uncorrected)
       
    if isinstance(alpha, float) or isinstance(alpha, int):
        return time, lat, lon, (40.3/f**2)*alpha*beta*(tec_GPS*tecu) + sla_uncorrected
    else:
        sla = [(40.3/f**2)*(alpha[i]*beta[i]*(tec_GPS))*tecu + sla_uncorrected for i in range(len(alpha))]
        return time, lat, lon, tuple(sla), failed_indices
    

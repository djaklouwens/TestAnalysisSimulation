
import numpy as np

import tec_interpolation
import rads_extraction
import alert

alpha = 0.83435
beta_CS = 0.858 # 12 May (6 May - 0.907)
beta_S3 = 0.903 # 12 May (6 May - 0.938)


def imic(alpha, beta, f=13.575e9, filename=None, time=None, lat=None, lon=None, sla_uncorrected=None):
    '''docstring TODO'''
    tecu = 1e16
    
    if filename is not None:
        time, lat, lon, sla_uncorrected = rads_extraction.extract_rads(filename) #TODO check filenames
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
        for i in range(len(alpha)):
            print(alpha[i]*beta[i])
        return time, lat, lon, tuple(sla), failed_indices
    

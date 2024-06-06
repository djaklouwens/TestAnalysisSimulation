import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pmdarima as pm
import pickle
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt
from sklearn.metrics import mean_squared_error
from netCDF4 import Dataset

def smoothing(nc_file, arima_order=(1, 1, 1), simpl_exp_params={'smoothing_level': [0.2, 0.3, 0.5]}, holts_lin_params={'smoothing_level': [0.2, 0.3, 0.5], 'smoothing_trend': [0.05, 0.1, 0.2]}):
    # Load NetCDF data
    nc_data = Dataset(nc_file, 'r')

    # Read variables from the NetCDF file
    time = nc_data.variables['time'][:]
    lon = nc_data.variables['lon'][:]
    lat = nc_data.variables['lat'][:]
    value = nc_data.variables['sla'][:]

    # Close the NetCDF file
    nc_data.close()

    # Convert to DataFrame
    df = pd.DataFrame({'Time': time, 'Lon': lon, 'Lat': lat, 'sla': value})

    # Filter the DataFrame based on the specified interval

    # Convert 'Date Time' column to datetime format
    df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    def ARIMA_model(df, p=1, q=1, d=1):
        model = ARIMA(df, order=(p, d, q))  
        results_ARIMA = model.fit(disp=-1)
        rmse = np.sqrt(mean_squared_error(df[1:], results_ARIMA.fittedvalues))
        return results_ARIMA, rmse

    def exponential_smoothing(df, smoothing_level=0.2):
        model = SimpleExpSmoothing(np.asarray(df))
        model._index = pd.to_datetime(df.index)
        fit = model.fit(smoothing_level=smoothing_level, optimized=False)
        return fit

    def holts_linear_smoothing(df, smoothing_level=0.3, smoothing_slope=0.05):
        model = Holt(np.asarray(df))
        model._index = pd.to_datetime(df.index)
        fit = model.fit(smoothing_level=smoothing_level, smoothing_trend=smoothing_slope, optimized=False)
        return fit

    def get_best_model(rmse):
        if rmse:
            min_rmse = min(rmse.values())
            best = [key for key in rmse if rmse[key] == min_rmse]
            return best[0]
        else:
            return None

    if 'Time' in df.columns:
        time = df['Time'][::10]
        df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        if 'sla' in df.columns:
            series = df['sla'][::100]
            train = series[:-int(len(series) / 10)]
            test = series[-int(len(series) / 10):]
            model = pm.auto_arima(train.values,
                                  start_p=1,
                                  start_q=1,
                                  test='adf',
                                  max_p=3,
                                  max_q=3,
                                  m=12,
                                  d=None,
                                  seasonal=True,
                                  start_P=0,
                                  D=1,
                                  trace=True,
                                  suppress_warnings=True,
                                  stepwise=True)
            print(model.summary())
            with open('seasonal_o.pkl', 'wb') as f:
                pickle.dump(model, f)
            all_vals = model.predict(n_periods=len(series), return_conf_int=False)
            all_vals = pd.Series(all_vals, index=series.index)
            plt.plot(series)
            plt.plot(all_vals, color='darkgreen')
            plt.title('Forecast values for the entire series')
            plt.xlabel('Year')
            plt.ylabel('Temp (Celcius)')
            plt.legend(['True', 'Predicted'])
            plt.show()

            preds, conf_vals = model.predict(n_periods=len(test), return_conf_int=True)
            preds = pd.Series(preds, index=test.index)

            lower_bounds = pd.Series(conf_vals[:, 0], index=list(test.index))
            upper_bounds = pd.Series(conf_vals[:, 1], index=list(test.index))

            plt.plot(series)
            plt.plot(preds, color='darkgreen')
            plt.fill_between(lower_bounds.index,
                             lower_bounds,
                             upper_bounds,
                             color='k', alpha=.15)

            plt.title("Forecast for test values")
            plt.xlabel('Year')
            plt.ylabel('Temp (Celcius)')
            plt.legend(['True', 'Predicted'])
            plt.show()

            simpl_exp_preds = {}
            holts_lin_preds = {}
            simpl_exp_rmse = {}
            holts_lin_rmse = {}

            for s in simpl_exp_params['smoothing_level']:
                model = exponential_smoothing(train, smoothing_level=s)
                preds = model.predict(start=1, end=len(test))
                preds -= preds[0]
                preds += train.values[-1]
                simpl_exp_preds[s] = preds
                rmse_s = np.sqrt(mean_squared_error(test, preds))
                simpl_exp_rmse[s] = rmse_s

            for sl in holts_lin_params['smoothing_level']:
                for ss in holts_lin_params['smoothing_trend']:
                    model = holts_linear_smoothing(train, smoothing_level=sl, smoothing_slope=ss)
                    preds = model.predict(start=1, end=len(test))
                    preds -= preds[0]
                    preds += train.values[-1]
                    holts_lin_preds[(sl, ss)] = preds
                    rmse_hl = np.sqrt(mean_squared_error(test, preds))
                    holts_lin_rmse[(sl, ss)] = rmse_hl

            best1 = get_best_model(simpl_exp_rmse)
            best2 = get_best_model(holts_lin_rmse)

            plt.figure(figsize=(12, 6))
            plt.plot(train.index, train.values, color='gray')
            plt.plot(test.index, test.values, color='gray')
            plt.title('Simple and Holt Smoothing Forecast')

            preds = simpl_exp_preds[best1]
            rmse = np.sqrt(mean_squared_error(test, preds))
            plt.plot(test.index[:len(preds)], preds, color='red',
                     label='preds - simple exponential smoothing - RMSE - {}'.format(rmse))
            plt.legend()

            preds = holts_lin_preds[best2]
            rmse = np.sqrt(mean_squared_error(test, preds))
            plt.plot(test.index[:len(preds)], preds, color='green',
                     label='preds - holts linear smoothing - RMSE - {}'.format(rmse))
            plt.legend()

            plt.show()

            plt.figure(figsize=(12, 6))
            plt.plot(train.index, train.values, color='gray')
            plt.plot(test.index, test.values, color='gray')
            plt.title('Best Model Forecast ')

            preds = simpl_exp_preds[best1]
            rmse = np.sqrt(mean_squared_error(test, preds))
            plt.plot(test.index[:len(preds)], preds, color='red',
                     label='preds - simple exponential smoothing - RMSE - {}'.format(rmse))
            plt.legend()
            plt.show()

            plt.figure(figsize=(12, 6))
            plt.plot(train.index, train.values, color='gray')
            plt.plot(test.index, test.values, color='gray')
            plt.title('Best Model Forecast ')

            preds = holts_lin_preds[best2]
            rmse = np.sqrt(mean_squared_error(test, preds))
            plt.plot(test.index[:len(preds)], preds, color='green',
                     label='preds - holts linear smoothing - RMSE - {}'.format(rmse))
            plt.legend()
            plt.show()
        else:
            print("Column 'sla' does not exist in the DataFrame.")
    else:
        print("Column 'Time' does not exist in the DataFrame.")


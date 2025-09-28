import pandas as pd
import numpy as np

def ema_forecast(history: pd.Series, span:int=7, horizon:int=7):
    """Simple EMA + weekly seasonality factor.
    history: daily quantity series with DatetimeIndex.
    """
    if history.empty:
        return np.array([0]*horizon)
    # seasonality factor by weekday
    by_wd = history.groupby(history.index.dayofweek).mean()
    wd_factor = by_wd / by_wd.mean()
    ema = history.ewm(span=span, adjust=False).mean().iloc[-1]
    future = []
    last = ema
    for h in range(horizon):
        wd = (history.index[-1].dayofweek + h + 1) % 7
        factor = wd_factor.get(wd, 1.0)
        yhat = max(0.0, last * factor)
        future.append(yhat)
        last = 0.7*last + 0.3*yhat  # smooth drift
    return np.array(future)

def compute_forecast(df_hist: pd.DataFrame, center_id:str, drug:str, horizon:int=7):
    """df_hist columns: date, center_id, drug, qty"""
    sub = df_hist[(df_hist.center_id==center_id)&(df_hist.drug==drug)].copy()
    if sub.empty:
        return np.zeros(horizon)
    s = sub.set_index(pd.to_datetime(sub['date']))['qty'].asfreq('D').fillna(0)
    return ema_forecast(s, span=7, horizon=horizon)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd

app = FastAPI()

def get_db():
    return sqlite3.connect('rail.db')

# 取得所有車站清單
@app.get("/api/stations")
def get_stations():
    conn = get_db()
    df = pd.read_sql('''
        SELECT s.staCode, s.name_zh, s.lat, s.lon, s.city,
               SUM(p.total) as total
        FROM stations s
        JOIN passengers p ON s.staCode = p.staCode
        GROUP BY s.staCode
    ''', conn)
    conn.close()
    return df.to_dict(orient='records')

# 取得單一車站人流
@app.get("/api/station/{sta_code}")
def get_station(sta_code: str):
    conn = get_db()
    df = pd.read_sql('''
        SELECT p.date, p.boarding, p.alighting, p.total
        FROM passengers p
        WHERE p.staCode = ?
        ORDER BY p.date
    ''', conn, params=[sta_code])
    conn.close()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df.to_dict(orient='records')

# 前端頁面
@app.get("/")
def index():
    return FileResponse('index.html')

from prophet import Prophet

@app.get("/api/forecast/{sta_code}")
def get_forecast(sta_code: str):
    conn = get_db()
    df = pd.read_sql('''
        SELECT date as ds, total as y
        FROM passengers
        WHERE staCode = ?
        ORDER BY date
    ''', conn, params=[sta_code])
    conn.close()

    df['ds'] = pd.to_datetime(df['ds'])

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    model.fit(df)

    from datetime import datetime
    last_date = df['ds'].max()
    target_date = pd.Timestamp('2026-07-03')
    periods = (target_date - last_date).days
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    result = result = forecast[forecast['ds'] > last_date][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7)
    result['ds'] = result['ds'].dt.strftime('%Y-%m-%d')
    result['yhat'] = result['yhat'].astype(int)
    result['yhat_lower'] = result['yhat_lower'].astype(int)
    result['yhat_upper'] = result['yhat_upper'].astype(int)

    return result.to_dict(orient='records')

@app.get("/api/crowding/{sta_code}")
def get_crowding(sta_code: str):
    conn = get_db()
    df = pd.read_sql('''
        SELECT date, total FROM passengers
        WHERE staCode = ?
        ORDER BY date
    ''', conn, params=[sta_code])
    conn.close()

    avg = df['total'].mean()

    def level(val):
        if val < avg * 0.8:
            return {'label': '低峰', 'color': '#22c55e', 'emoji': '🟢'}
        elif val < avg * 1.2:
            return {'label': '普通', 'color': '#eab308', 'emoji': '🟡'}
        elif val < avg * 1.5:
            return {'label': '擁擠', 'color': '#ef4444', 'emoji': '🔴'}
        else:
            return {'label': '非常擁擠', 'color': '#a855f7', 'emoji': '🟣'}

    df['date'] = df['date'].astype(str)
    df['level'] = df['total'].apply(level)
    df['label'] = df['level'].apply(lambda x: x['label'])
    df['color'] = df['level'].apply(lambda x: x['color'])
    df['emoji'] = df['level'].apply(lambda x: x['emoji'])

    # 最近 7 天的等級
    recent = df.tail(7)[['date', 'total', 'label', 'color', 'emoji']]
    return {
        'average': int(avg),
        'recent': recent.to_dict(orient='records')
    }

@app.get("/api/custom-forecast/{sta_code}")
def get_custom_forecast(sta_code: str, start_date: str = "2026-06-27", end_date: str = "2026-07-03"):
    conn = get_db()
    df = pd.read_sql('''
        SELECT date as ds, total as y
        FROM passengers
        WHERE staCode = ?
        ORDER BY date
    ''', conn, params=[sta_code])
    conn.close()

    df['ds'] = pd.to_datetime(df['ds'])
    last_date = df['ds'].max()
    target_date = pd.Timestamp(end_date)
    periods = (target_date - last_date).days + 7

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    mask = (forecast['ds'] >= pd.Timestamp(start_date)) & (forecast['ds'] <= target_date)
    result = forecast[mask][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    result['ds'] = result['ds'].dt.strftime('%Y-%m-%d')
    result['yhat'] = result['yhat'].astype(int)
    result['yhat_lower'] = result['yhat_lower'].astype(int)
    result['yhat_upper'] = result['yhat_upper'].astype(int)

    return result.to_dict(orient='records')

@app.get("/api/weekday-analysis/{sta_code}")
def get_weekday_analysis(sta_code: str):
    conn = get_db()
    df = pd.read_sql('''
        SELECT date, total FROM passengers
        WHERE staCode = ?
        ORDER BY date
    ''', conn, params=[sta_code])
    conn.close()

    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].dt.dayofweek  # 0=週一 6=週日

    # 平日 vs 假日
    weekday_avg = int(df[df['weekday'] < 5]['total'].mean())
    weekend_avg = int(df[df['weekday'] >= 5]['total'].mean())

    # 每天平均（週一到週日）
    daily = df.groupby('weekday')['total'].mean().round(0).astype(int)
    days = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    daily_avg = [int(daily.get(i, 0)) for i in range(7)]

    return {
        'weekday_avg': weekday_avg,
        'weekend_avg': weekend_avg,
        'daily_avg': daily_avg,
        'days': days
    }
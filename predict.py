import sqlite3
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Microsoft JhengHei'

conn = sqlite3.connect('rail.db')

# 抓台北車站資料
df = pd.read_sql('''
    SELECT p.date, p.total
    FROM passengers p
    JOIN stations s ON p.staCode = s.staCode
    WHERE s.name_zh = '臺北'
    ORDER BY p.date
''', conn)
conn.close()

# Prophet 要求欄位名稱是 ds 和 y
df = df.rename(columns={'date': 'ds', 'total': 'y'})
df['ds'] = pd.to_datetime(df['ds'])

# 建立模型
model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False
)
model.fit(df)

# 預測未來 7 天
future = model.make_future_dataframe(periods=7)
forecast = model.predict(future)

# 印出未來 7 天預測
print("未來 7 天預測：")
result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7)
result.columns = ['日期', '預測人流', '最低估計', '最高估計']
result['預測人流'] = result['預測人流'].astype(int)
result['最低估計'] = result['最低估計'].astype(int)
result['最高估計'] = result['最高估計'].astype(int)
print(result.to_string(index=False))

# 畫預測圖
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df['ds'], df['y'], label='實際人流', color='steelblue', alpha=0.7)
ax.plot(forecast['ds'], forecast['yhat'], label='預測人流', color='tomato')
ax.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                alpha=0.2, color='tomato', label='預測區間')
ax.axvline(x=df['ds'].max(), color='gray', linestyle='--', alpha=0.5, label='預測起點')
ax.set_title('臺北車站人流預測', fontsize=16)
ax.set_xlabel('日期')
ax.set_ylabel('人次')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('taipei_forecast.png', dpi=150)
print("\n✓ 預測圖已儲存為 taipei_forecast.png")
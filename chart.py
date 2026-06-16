import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 解決中文顯示問題（Windows）
plt.rcParams['font.family'] = 'Microsoft JhengHei'

conn = sqlite3.connect('rail.db')

# 抓台北車站每日人流
df = pd.read_sql('''
    SELECT p.date, p.boarding, p.alighting, p.total
    FROM passengers p
    JOIN stations s ON p.staCode = s.staCode
    WHERE s.name_zh = '臺北'
    ORDER BY p.date
''', conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])

# 畫圖
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df['date'], df['boarding'], label='進站', color='steelblue')
ax.plot(df['date'], df['alighting'], label='出站', color='tomato')
ax.plot(df['date'], df['total'], label='總人流', color='gray', linestyle='--', alpha=0.6)

ax.set_title('臺北車站 2026 年每日人流', fontsize=16)
ax.set_xlabel('日期')
ax.set_ylabel('人次')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('taipei_station.png', dpi=150)
print("✓ 圖表已儲存為 taipei_station.png")
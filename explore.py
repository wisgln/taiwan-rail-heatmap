import json
import pandas as pd
import sqlite3

# 讀取資料
with open('data/每日各站進出站人數-2026.json', encoding='utf-8') as f:
    raw = json.load(f)

df = pd.DataFrame(raw)

# 轉換欄位
df['date'] = pd.to_datetime(df['trnOpDate'], format='%Y%m%d')
df['boarding'] = df['gateInComingCnt'].astype(int)
df['alighting'] = df['gateOutGoingCnt'].astype(int)
df['total'] = df['boarding'] + df['alighting']
df['staCode'] = df['staCode'].astype(str)

# 只保留需要的欄位
df = df[['date', 'staCode', 'boarding', 'alighting', 'total']]

# 存入 SQLite
conn = sqlite3.connect('rail.db')
df.to_sql('passengers', conn, if_exists='replace', index=False)
conn.close()

print(f"✓ 共 {len(df)} 筆資料已存入 rail.db")
print(f"✓ 涵蓋 {df['staCode'].nunique()} 個車站")
print(f"✓ 日期範圍：{df['date'].min().date()} ~ {df['date'].max().date()}")
print("\n人流最多前 5 站：")
top5 = df.groupby('staCode')['total'].sum().sort_values(ascending=False).head()
print(top5)
import sqlite3
import pandas as pd

conn = sqlite3.connect('rail.db')

# 合併兩張表
df = pd.read_sql('''
    SELECT p.date, s.name_zh, s.city, p.boarding, p.alighting, p.total
    FROM passengers p
    JOIN stations s ON p.staCode = s.staCode
    ORDER BY p.total DESC
    LIMIT 10
''', conn)

conn.close()

print("人流最多前 10 筆：")
print(df.to_string(index=False))
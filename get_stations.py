import requests
import sqlite3

url = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/Station?%24format=JSON"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(url, headers=headers)
data = res.json()

# 整理成我們需要的欄位
stations = []
for s in data:
    stations.append({
        'staCode': s['StationID'],
        'name_zh': s['StationName']['Zh_tw'],
        'name_en': s['StationName']['En'],
        'lat': s['StationPosition']['PositionLat'],
        'lon': s['StationPosition']['PositionLon'],
        'city': s.get('LocationCity', ''),
    })

# 存入 SQLite
conn = sqlite3.connect('rail.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        staCode TEXT PRIMARY KEY,
        name_zh TEXT,
        name_en TEXT,
        lat REAL,
        lon REAL,
        city TEXT
    )
''')

for s in stations:
    cursor.execute('''
        INSERT OR REPLACE INTO stations VALUES (?, ?, ?, ?, ?, ?)
    ''', (s['staCode'], s['name_zh'], s['name_en'], s['lat'], s['lon'], s['city']))

conn.commit()
conn.close()

print(f"✓ {len(stations)} 個車站已存入 rail.db")
print("\n範例：")
for s in stations[:5]:
    print(f"  {s['staCode']} | {s['name_zh']} | {s['lat']}, {s['lon']}")
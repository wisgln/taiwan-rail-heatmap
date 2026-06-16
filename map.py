import sqlite3
import pandas as pd
import folium
from folium.plugins import HeatMap

conn = sqlite3.connect('rail.db')

# 抓每個車站的總人流 + 經緯度
df = pd.read_sql('''
    SELECT s.name_zh, s.lat, s.lon, s.city,
           SUM(p.total) as total
    FROM passengers p
    JOIN stations s ON p.staCode = s.staCode
    GROUP BY p.staCode
    ORDER BY total DESC
''', conn)
conn.close()

print(f"共 {len(df)} 個車站")
print(df.head())

# 建立地圖（以台灣中心為基準）
m = folium.Map(location=[23.97, 120.97], zoom_start=8, tiles='CartoDB positron')

# 熱力圖圖層
heat_data = [[row['lat'], row['lon'], row['total']] for _, row in df.iterrows()]
HeatMap(heat_data, radius=20, blur=15, min_opacity=0.4).add_to(m)

# 每個車站加上標記
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=5,
        color='steelblue',
        fill=True,
        fill_opacity=0.7,
        tooltip=f"{row['name_zh']}｜總人流：{row['total']:,}"
    ).add_to(m)

# 儲存為 HTML
m.save('map.html')
print("✓ 地圖已儲存為 map.html")
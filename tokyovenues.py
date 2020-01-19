import sqlite3
import json
from flask import Flask
from flask import request


keys = ['url', 'title', 'lat', 'lon', 'img_url']
num = 20

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def umasou():
    if request.method == 'GET':
        offset = int(request.args.get('offset', ''))
        lat = float(request.args.get('lat', ''))
        lon = float(request.args.get('lon', ''))
        radius = float(request.args.get('radius', ''))

    conn = sqlite3.connect('timeout.db')
    c = conn.cursor()

    lat_range = 0.010986907135315433 * radius
    lon_range = 0.008999947440306948 * radius

    c.execute(
        '''
        select * from venues where lat>? and lat<? and lon>? and lon<?
        ''',
        (lat - lat_range, lat + lat_range,
         lon - lon_range, lon + lon_range)
    )

    items = c.fetchall()
    items = items[offset*num : offset*num + num]

    items_dict = list(map(lambda x: dict(zip(keys, x)), items))
    c.close()

    return json.dumps({'items': items_dict}, ensure_ascii=False).encode()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

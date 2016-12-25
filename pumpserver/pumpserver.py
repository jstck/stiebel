#!/usr/bin/env python

from flask import Flask, make_response, json
import sqlite3
from datetime import datetime
import time

app = Flask(__name__)

HOST="0.0.0.0"
PORT=8081
MIME_JSON = "application/json"

def viernullvier(msg="NOT FOUND"):
    r = make_response(msg, 404)
    return r

def jsonResponse(data, prettyprint=True):
    if prettyprint:
        jsondata = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
    else:
        jsondata = json.dumps(data)

    r = make_response(jsondata)
    r.mimetype=MIME_JSON

    return r

def getDB():
    return sqlite3.connect('pump.db')

def getStates(db):
    c = db.cursor()

    result = {}

    for (id, state, last_update) in c.execute("SELECT id, state, last_update FROM states"):
        updated = datetime.fromtimestamp(last_update)
        r = {
            "id": id,
            "state": state,
            "updated_timestamp": last_update,
            "updated": updated.strftime("%Y-%m-%d %H:%M:%S")
        }
        result[id] = r

    return result

@app.route('/states')
def index():
    db = getDB()
    states = getStates(db)

    return jsonResponse(states)

@app.route('/state/<id>')
def state(id):
    db = getDB()
    states = getStates(db)
    if states.has_key(id):
        return jsonResponse(states[id])

    return viernullvier()

@app.route('/update/<id>/<state>')
def update(id, state):
    db = getDB()
    c = db.cursor()

    timestamp = int(time.time())

    c.execute("DELETE FROM states WHERE id=?", (id,))
    c.execute("INSERT INTO states (id, state, last_update) VALUES (?, ?, ?)", (id, state, timestamp))

    db.commit()

    return jsonResponse({"id": id, "state": state, "updated_timestamp": timestamp})


@app.route('/', defaults={'f': 'index.html'})
@app.route('/<path:f>')
def statics(f):
    return app.send_static_file(f)

if __name__=="__main__":
    app.run(host=HOST, port=PORT)

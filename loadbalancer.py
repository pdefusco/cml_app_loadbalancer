#!pip3 install https://$CDSW_DOMAIN/api/v2/python.tar.gz
#!pip3 install -r requirements.txt

from flask import Flask, redirect
import sqlite3
import logging
import random
import os
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Load Application List
def get_url_array():
  url_array_database = 'application_list.db'
  database = sqlite3.connect(url_array_database)
  sqlite_cursor = database.cursor()
  sqlite_cursor.execute('select * from app_urls')
  rows = sqlite_cursor.fetchall()
  url_array = {}
  for row in rows:
      url_array[row[0]] = row[1]
  database.close()
  return url_array

# Start Flask Stuff
flask_app = Flask(__name__, static_url_path='')

# Show Status of all Applications
@flask_app.route("/status")
def status():
  return {'apps':get_url_array()}

# Redirection to available applications
@flask_app.route("/")
def home():
  url_array = get_url_array()
  redirect_array  = list(get_url_array())
  for url in redirect_array:
    if url_array[url] == "locked":
        redirect_array.remove(url)
  if len(redirect_array) == 0:
    return "There are no running applications"
  else:
    return redirect(redirect_array[random.randint(0,len(redirect_array)-1)])

# Start App
if __name__ == "__main__":
  flask_app.run(host='127.0.0.1', port=int(os.environ['CDSW_APP_PORT']))
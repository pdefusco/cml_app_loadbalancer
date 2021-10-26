from flask import Flask
import sqlite3
import logging
import os
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

url_array_database = 'application_list.db'
app_url = "{}://{}.{}".format(
  os.environ["CDSW_PROJECT_URL"].split(":")[0],
  os.environ["APP_SUBDOMAIN"],
  os.environ["CDSW_DOMAIN"]
)

def state_update(new_state):
  global url_array_database 
  global app_url 
  database = sqlite3.connect(url_array_database)
  sqlite_cursor = database.cursor()
  app_count = sqlite_cursor.execute('select count(*) from app_urls where app_url = "{}"'.format(app_url)).fetchall()[0][0]
  if app_count == 0:
    sqlite_cursor.execute('insert into app_urls values ("{}","available")'.format(app_url))
    database.commit()
  else:
    sqlite_cursor.execute('update app_urls set state = "{}" where app_url = "{}"'.format(new_state,app_url))
    database.commit()
  database.close()

flask_app = Flask(__name__, static_url_path='')

@flask_app.route("/")
def home():
  global app_url
  return {"app_url" : "{}".format(app_url)}

@flask_app.route("/lock")
def lock():
  global app_url
  state_update("locked")
  return {"App {}".format(app_url) : "locked"}

@flask_app.route("/unlock")
def unlock():
  global app_url
  state_update("available")
  return {"App {}".format(app_url) : "unlocked"}

# App Application on first run
state_update("available")

# Start App
if __name__ == "__main__":
  flask_app.run(host='127.0.0.1', port=int(os.environ['CDSW_APP_PORT']))
#!pip3 install https://$CDSW_DOMAIN/api/v2/python.tar.gz
#!pip3 install -r requirements.txt

from flask import Flask, send_from_directory, request, redirect
from pandas.io.json import dumps as jsonify
from json import loads
import sqlite3
import logging
import random
import cmlapi
import os
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

# Some useful CURL commands
# curl -H "Content-Type: application/json" -X GET http://loclhost:5000/status
# curl -H "Content-Type: application/json" -X POST http://localhost:5000/lock_application -d '{"app_url":"http://stuff.cloudera.site"}'

# Required Global Parameters
minimum_unlocked_applications = 2
maximum_unlocked_applications = 5
project_runtime_identifier = "runtime_name"
application_script = "application.py"
url_array_database = 'application_list.db'

# Load Application List

database = sqlite3.connect(url_array_database)
sqlite_cursor = database.cursor()

# Create Table on first run
#sqlite_cursor.execute('''CREATE TABLE app_urls (app_url text, state text)''')
#sqlite_cursor.execute("INSERT INTO app_urls VALUES ('http://app_1.cloudera.site','available')")
#database.commit()

sqlite_cursor.execute('select * from app_urls')
rows = sqlite_cursor.fetchall()
url_array = {}
for row in rows:
    url_array[row[0]] = row[1]
database.close()


#url_array = {}
#url_array["http://app_1.cloudera.site"] = "available"

#Create CML API Instance
cml_api_instance = cmlapi.default_client()

# Helper functions
def redirect_array_builder(url_array):
  redirect_array = list(url_array)
  for url in redirect_array:
    if url_array[url] == "locked":
        redirect_array.remove(url)
  return redirect_array

# Start Flask Stuff
flask_app = Flask(__name__, static_url_path='')

# Show Status of all Applications
@flask_app.route("/status")
def status():
  return {'apps':url_array}

# Redirection to available applications
@flask_app.route("/")
def home():
  #global redirect_counter
  global url_array
  redirect_array  = redirect_array_builder(url_array)
  #return {"urls":redirect_array}
  # TODO check if available URLs less than min_number and create new application
  return "sending to {}".format(redirect_array[random.randint(0,len(redirect_array)-1)]) #redirect

# Get Application Lock
# TODO Check if key exists first
@flask_app.route("/lock_application",methods=['GET', 'POST'])
def lock_application():
  if request.method == 'POST':
    url_array[loads(request.data)['app_url']] = "locked"
  return "Application at {} locked".format(loads(request.data)['app_url'])

# Add/Unlock Application
@flask_app.route("/add_application",methods=['GET', 'POST'])
def add_application():
  if request.method == 'POST':
    url_array[loads(request.data)['app_url']] = "available"
  return "Application at {} added".format(loads(request.data)['app_url'])
## Update Redirection list

# AutoScale - Add/Remove Applications via Job Updates
@flask_app.route("/check_applications")
def check_applications():
  global url_array
  redirect_array  = redirect_array_builder(url_array)
 
  #Add Application
  if len(redirect_array) < minimum_unlocked_applications:
    print("adding Application")
    new_application = cmlapi.Application(
      cpu = 2,
      memory = 4,
      name = "Application No. {}".format(len(redirect_array)+1),
      subdomain = "app_{}".format(len(redirect_array)+1),
      script = application_script,
      runtime_identifier=project_runtime_identifier
    )
    cml_api_instance.create_application(new_application,os.environ["CDSW_PROJECT_ID"])
    url_array["http://{}.{}".format("app_{}".format(len(redirect_array)+1),os.environ["CDSW_DOMAIN"])] = "locked"
  
  #Remove Application
  elif len(redirect_array) > maximum_unlocked_applications:
    print("removing applications")
    #Find application id for last application in redirect array
    all_applications = cml_api_instance.list_applications(os.environ["CDSW_PROJECT_ID"])
    for application in all_applications:
      print(application)
      if application.name == redirect_array[len(redirect_array)-1]:
        application_id = application.application_id
    #lock application before removing it
    url_array[redirect_array[len(redirect_array)-1]] = "locked"
    #remove application
    cml_api_instance.delete_application(os.environ["CDSW_PROJECT_ID"],application_id)
  
  #Update sqllite table
  database = sqlite3.connect(url_array_database)
  sqlite_cursor = database.cursor()
  sqlite_cursor.execute('DELETE FROM app_urls')
  for app_url,state in url_array.items():
    sqlite_cursor.execute('INSERT INTO app_urls VALUES ("{}","{}")'.format(app_url, state))
  database.commit()
  database.close()
  
  # return list of available applications
  return {'redirect_array':redirect_array}


  
    



# Start App
if __name__ == "__main__":
  flask_app.run() #host='127.0.0.1', port=int(os.environ['CDSW_APP_PORT']))
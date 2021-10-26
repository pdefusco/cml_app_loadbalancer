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

# Required Global Parameters
minimum_unlocked_applications = 1
maximum_unlocked_applications = 2
project_runtime_identifier = "docker.repository.cloudera.com/cdsw/ml-runtime-workbench-python3.7-standard:2021.09.1-b5"
application_script = "application.py"

# Create Table on first run
#sqlite_cursor.execute(
# '''CREATE TABLE app_urls 
# (app_url text, state text)
# ''')
#sqlite_cursor.execute("INSERT INTO app_urls VALUES ('http://app-1.cloudera.site','available')")
#database.commit()

cml_api_instance = cmlapi.default_client()

url_array_database = 'application_list.db'

# Load Application List

database = sqlite3.connect(url_array_database)
sqlite_cursor = database.cursor()

sqlite_cursor.execute('select * from app_urls')
rows = sqlite_cursor.fetchall()


url_array = {}
for row in rows:
  url_array[row[0]] = row[1]
database.close()

redirect_array = list(url_array)
for url in redirect_array:
    if url_array[url] == "locked":
        redirect_array.remove(url)

#TODO Check the list of apps running apps

#Add Applications
if len(redirect_array) < minimum_unlocked_applications:
    print("adding Application")
    new_application = cmlapi.Application(
        cpu = 2,
        memory = 4,
        name = "App {}".format(len(redirect_array)+1),
        subdomain = "app-{}".format(len(redirect_array)+1),
        script = application_script,
        runtime_identifier=project_runtime_identifier,
        environment={"APP_SUBDOMAIN":"app-{}".format(len(redirect_array)+1)}
    )
    app_url = "{}://{}.{}".format(
        os.environ["CDSW_PROJECT_URL"].split(":")[0],
        "app-{}".format(len(redirect_array)+1),
        os.environ["CDSW_DOMAIN"]
    )
    url_array[app_url] = "locked"
    cml_api_instance.create_application(new_application,os.environ["CDSW_PROJECT_ID"])

#Remove Applications
elif len(redirect_array) > maximum_unlocked_applications:
    print("removing applications")
    #Find application id for last application in redirect array
    all_applications = cml_api_instance.list_applications(os.environ["CDSW_PROJECT_ID"])
    for application in all_applications.applications:
        app_url = "{}://{}.{}".format(
          os.environ["CDSW_PROJECT_URL"].split(":")[0],
          application.subdomain,
          os.environ["CDSW_DOMAIN"]
        )
        if app_url == redirect_array[len(redirect_array)-1]:
            application_id = application.id
    #lock application before removing it
    url_array.pop(app_url)
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
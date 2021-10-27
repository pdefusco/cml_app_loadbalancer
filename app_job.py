#!pip3 install https://$CDSW_DOMAIN/api/v2/python.tar.gz
#!pip3 install -r requirements.txt

import sqlite3
import cmlapi
import os

# Required Global Parameters
minimum_unlocked_applications = 3
maximum_unlocked_applications = 5
loadbalancer_subdomain = "loadbalancer"
project_runtime_identifier = "docker.repository.cloudera.com/cdsw/ml-runtime-workbench-python3.7-standard:2021.09.1-b5"
application_script = "application.py"
url_array_database = 'application_list.db'

# Create Table on first run
database = sqlite3.connect(url_array_database)
sqlite_cursor = database.cursor()
try:
    if sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()[0][0] != 'app_urls':
        sqlite_cursor.execute(
        '''CREATE TABLE app_urls 
        (app_url text, state text)
        ''')
        database.commit()
except:
    print("unable to create default table")

# Load Application List
sqlite_cursor.execute('select * from app_urls')
rows = sqlite_cursor.fetchall()
url_array = {}
for row in rows:
  url_array[row[0]] = row[1]
database.close()

# Check and fix app list
cml_api_instance = cmlapi.default_client()
deployed_apps_list = [apps.subdomain for apps in cml_api_instance.list_applications(os.environ["CDSW_PROJECT_ID"]).applications]
deployed_apps_list.remove(loadbalancer_subdomain)
stored_apps_list = [subdomains.split("//")[1].split(".")[0] for subdomains in list(url_array)]

# Updated stored list - add missing apps to url_array
apps_to_add = list(set(deployed_apps_list).difference(set(stored_apps_list)))
for app in apps_to_add:
    url_array["{}://{}.{}".format(
          os.environ["CDSW_PROJECT_URL"].split(":")[0],
          app,
          os.environ["CDSW_DOMAIN"]
        )] = "locked"

# Updated stored list - remove unknown apps from url_array
apps_to_remove = list(set(stored_apps_list).difference(set(deployed_apps_list)))
for app in apps_to_remove:
    url_array.pop("{}://{}.{}".format(
          os.environ["CDSW_PROJECT_URL"].split(":")[0],
          app,
          os.environ["CDSW_DOMAIN"]
        ))

# Create redirect array
redirect_array = list(url_array)
for url in redirect_array.copy(): #This took longer to figure out than it should have
    print(url_array[url])
    if url_array[url] == "locked":
        print('removing')
        redirect_array.remove(url)


#Add Applications
if len(redirect_array) < minimum_unlocked_applications:
    print("adding Application")
    new_application = cmlapi.Application(
        cpu = 2,
        memory = 4,
        name = "App {}".format(len(url_array)+1),
        subdomain = "app-{}".format(len(url_array)+1),
        script = application_script,
        runtime_identifier=project_runtime_identifier,
        environment={"APP_SUBDOMAIN":"app-{}".format(len(url_array)+1)}
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
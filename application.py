from flask import Flask, send_from_directory, request, redirect
from pandas.io.json import dumps as jsonify
from json import loads
import sqlite3
import logging
import random
import cmlapi
import os
import requests

loadbalancer_url = "http://loadbalancer.{}".format(os.environ["CDSW_DOMAIN"])

flask_app = Flask(__name__, static_url_path='')

# Redirection to available applications
@flask_app.route("/")
def home():
  app_number = request.base_url.split("//")[1].split("_")[1].split(".")[0]
  return "This is App {}".format(app_number)

@flask_app.route("/lock")
def home():
  requests.post("{}/lock_application".format(loadbalancer_url),{"app_url":request.base_url})
  app_number = request.base_url.split("//")[1].split("_")[1].split(".")[0]
  return "App {} is locked".format(app_number)

@flask_app.route("/unlock")
def home():
  requests.post("{}/add_application".format(loadbalancer_url),{"app_url":request.base_url})
  app_number = request.base_url.split("//")[1].split("_")[1].split(".")[0]
  return "App {} is unlocked".format(app_number)

# App Application on first run
requests.post("{}/add_application".format(loadbalancer_url),{"app_url":request.base_url})

# Start App
if __name__ == "__main__":
  flask_app.run() #host='127.0.0.1', port=int(os.environ['CDSW_APP_PORT']))
# # Part 6: Application

# This script explains how to create and deploy Applications in CML.
# This feature allows data scientists to **get ML solutions in front of stakeholders quickly**,
# including business users who need results fast.
# This may be good for sharing a **highly customized dashboard**, a **monitoring tool**, or a **product mockup**.


# This has to be here until DSE-16317 is fixed.
!pip3 install -r requirements.txt
!pip3 install requests-kerberos==0.12.0 flask==1.1.2 boto3==1.17.84
!pip3 install --upgrade git+https://github.com/fletchjeff/cmlbootstrap#egg=cmlbootstrap

  
import sys
sys.path.insert(1, '/home/cdsw/code')

from flask import Flask, send_from_directory, request
from IPython.display import Javascript, HTML
import random
import os
from churnexplainer import ExplainedModel
from collections import ChainMap
from flask import Flask
from pandas.io.json import dumps as jsonify
import logging
import subprocess
from IPython.display import Image
from cmlbootstrap import CMLBootstrap



Image("images/table_view.png")
#
# Clicking on any row will show a "local" interpreted model for that particular customer.
# Here, you can see how adjusting any one of the features will change that customer's churn prediction.
#
Image("images/single_view_1.png")
#
# Changing the *InternetService* to *DSL* lowers the probablity of churn.
# **Note**: this obviously does *not* mean that you should change that customer's internet service to DSL
# and expect they will be less likely to churn.
# Imagine if your ISP did that to you.
# Rather, the model is more optimistic about an otherwise identical customer who has been using DSL.
# This information simply gives you a clearer view of what to expect given specific factors
# as a starting point for developing your business strategies.
# Furthermore, as you start implementing changes based on the model, it may change customers' behavior
# so that the predictions stop being reliable.
# It's important to use Jobs to keep models up-to-date.
#
Image("images/single_view_2.png")
#
# There are many frameworks that ease the development of interactive, informative webapps.
# Once written, it is straightforward to deploy them in CML.


# This reduces the the output to the console window
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Since we have access in an environment variable, we want to write it to our UI
# Change the line in the flask/single_view.html file.
# if os.environ.get('SHTM_ACCESS_KEY') != None:
#   access_key = os.environ.get('SHTM_ACCESS_KEY', "")
#   subprocess.call(["sed", "-i",  's/const\saccessKey.*/const accessKey = "' +
#                    access_key + '";/', "/home/cdsw/flask/single_view.html"])


# Load the explained model
em = ExplainedModel(model_name='telco_linear', data_dir='/home/cdsw')
cml = CMLBootstrap()

# Creates an explained version of a partiuclar data point. This is almost exactly the same as the data used in the model serving code.


def explainid(N):
    customer_data = dataid(N)[0]
    customer_data.pop('id')
    customer_data.pop('Churn probability')
    data = em.cast_dct(customer_data)
    probability, explanation = em.explain_dct(data)
    return {'data': dict(data),
            'probability': probability,
            'explanation': explanation,
            'id': int(N)}

# Gets the rest of the row data for a particular customer.


def dataid(N):
    customer_id = em.data.index.dtype.type(N)
    customer_df = em.data.loc[[customer_id]].reset_index()
    return customer_df.to_dict(orient='records')


# Flask doing flasky things
flask_app = Flask(__name__, static_url_path='')


@flask_app.route('/')
def home():
    return "<script> window.location.href = '/app/index.html'</script>"


@flask_app.route('/app/<path:path>')
def send_file(path):
    return send_from_directory('app', path)

# Grabs a sample explained dataset for 10 randomly selected customers.


@flask_app.route('/sample_table')
def sample_table():
    sample_ids = random.sample(range(1, len(em.data)), 10)
    sample_table = []
    for ids in sample_ids:
        sample_table.append(explainid(str(ids)))
    return jsonify(sample_table)

# Shows the names and all the catagories of the categorical variables.


@flask_app.route("/categories")
def categories():
    return jsonify({feat: dict(enumerate(cats))
                    for feat, cats in em.categories.items()})

# Shows the names and all the statistical variations of the numerica variables.
@flask_app.route("/stats")
def stats():
    return jsonify(em.stats)


@flask_app.route("/model_access_keys")
def model_access_keys():
  project_id = cml.get_project()['id']
  params = {"projectId":project_id,"latestModelDeployment":True,"latestModelBuild":True}
  model_id = cml.get_models(params)[0]['id']
  latest_model = cml.get_model({"id": model_id, "latestModelDeployment": True, "latestModelBuild": True})
  return jsonify({
    'model_access_key': latest_model['accessKey']
  })

# A handy way to get the link if you are running in a session.
HTML("<a href='https://{}.{}'>Open Table View</a>".format(
    os.environ['CDSW_ENGINE_ID'], os.environ['CDSW_DOMAIN']))

# Launches flask. Note the host and port details. This is specific to CML/CDSW
if __name__ == "__main__":
    flask_app.run(host='127.0.0.1', port=int(os.environ['CDSW_APP_PORT']))
    
    

import flask
import requests
from flask import request

app = flask.Flask(__name__)

# Define routes
@app.route('/', methods=['GET'])
def index():
    return 'Ok'

@app.route('/health')
def health_check():
    return 'Ok', 200
@app.route('/new')
def newfnction():
    return 'hi how are you ?'
@app.route('/results/', methods=['GET'])
def results():
    prediction_id = request.args.get('predictionId')
    polybot_url = "http://127.0.0.1:8443/results/"  # Adjust the URL to point to the Polybot service
    try:
        response = requests.get(polybot_url, params={'predictionId': str(prediction_id)})
        response.raise_for_status()  # Raise an exception for any HTTP error status codes
        return 'Ok'
    except requests.RequestException as e:
        return f'Error accessing Polybot: {e}', 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)


from flask import json
from flask import request
from flask import Flask
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import render_template


client = MongoClient('mongodb://localhost:27017/')
db = client['TechStax']
collection = db['WebhookTask']


app = Flask(__name__)

@app.route('/')
def api_root():
    return render_template('index.html')

@app.route('/github', methods=['POST'])
def api_gh_message():
    if request.headers['Content-Type'] == 'application/json':
        event_type = request.headers.get('X-GitHub-Event')
        payload = request.json

        if event_type in ['push', 'pull_request', 'merge']:
            action_data = {
                'request_id': str(ObjectId()),
                'author': payload.get('pusher', {}).get('name') or payload.get('pull_request', {}).get('user', {}).get('login'),
                'action': event_type,
                'from_branch': payload.get('ref', '').split('/')[-1] if event_type == 'push' else payload.get('pull_request', {}).get('head', {}).get('ref', ''),
                'to_branch': payload.get('pull_request', {}).get('base', {}).get('ref', '') if event_type == 'pull_request' else payload.get('pull_request', {}).get('base', {}).get('ref', ''),
                'timestamp': payload.get('head_commit', {}).get('timestamp') if event_type == 'push' else payload.get('created_at') if event_type == 'pull_request' else payload.get('pull_request', {}).get('merged_at', ''),
            }
            result = collection.insert_one(action_data)
            print(f"Inserted document with ID: {result.inserted_id}")

            return "Data stored in MongoDB"

    return "Invalid request"


@app.route('/api/data', methods=['GET'])
def api_get_data():
    data = list(collection.find({}, {'_id': 0, 'request_id': 1, 'author': 1, 'action': 1, 'from_branch': 1, 'to_branch': 1, 'timestamp': 1}).sort('_id', -1).limit(10))
    return json.dumps(data)



if __name__ == "__main__":
    app.run(debug=True)

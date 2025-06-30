from flask import Flask, jsonify, send_from_directory
import subprocess
import json
import os

app = Flask(__name__, static_folder='frontend/build', static_url_path='/')

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/trace/<destination>')
def trace(destination):
    subprocess.run(['sudo', 'python', 'traceroute.py', destination], capture_output=True, text=True)
    with open('netpath_results.json', 'r') as f:
        results = json.load(f)
    return jsonify(results)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

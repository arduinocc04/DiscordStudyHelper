from flask import Flask
from flask import send_file
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/problems/<id>')
def problems(id):
    return send_file('problems/' + id, mimetype='image/jpeg')

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)

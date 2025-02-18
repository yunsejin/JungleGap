from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
import jwt
import datetime
import hashlib
import json

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/junglegapDB")
# client = MongoClient('mongodb://jungler:1234@localhost', 27017)
db = client.junglegapDB

SECRET_KEY = 'J2n8l6G9P'


@app.route('/', methods=['GET'])
def start():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        ranker_list = list(db.user.find({}, {'_id': 0 ,'pw':0}).sort('score', -1).limit(10))
        return render_template('main.html', userid=user_info['id'], score=user_info['score'], ranker=json.dumps(ranker_list))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def api_signup():
    id_receive = request.form.get('id_give', '')
    pw_receive = request.form.get('pw_give', '')

    if not id_receive:
        return jsonify({'result': 'notid'})
    elif not pw_receive:
        return jsonify({'result': 'notpw'})
    
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    existing_user = db.user.find_one({'id': id_receive})

    if existing_user:
        return jsonify({'result': 'fail'})
    
    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'score': 0})
    return jsonify({'result': 'success'})


@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail'})
    
@app.route('/api/score', methods=['POST'])
def api_score():
    score_receive = request.form['score_give']
    token_receive = request.cookies.get('mytoken')
    
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    db_score = db.user.find_one({'id': payload['id']}, {'_id': False, 'score': True})['score']
    db.user.update_one({'id': payload['id']}, {'$set': {'score': max(score_receive, db_score)}})
        
    return jsonify({'result': 'success'})
    

@app.route('/ingame')
def ingame():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        return render_template('ingame.html', userid=user_info['id'], score=user_info['score'])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
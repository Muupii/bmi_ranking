# coding: utf-8

# モジュールのインポート
import time
from flask import Flask, render_template, request, make_response, redirect
from urllib.parse import urlparse
import mysql.connector
import pandas as pd

# データベースとの接続
def connect_db():
    url = urlparse('mysql://*****:*****@localhost:3306/*****')

    conn = mysql.connector.connect(
        host=url.hostname or '*****',
        port=url.port or 3306,
        user=url.username or '*****',
        password=url.password or '*****',
        database=url.path[1:],
    )
    return conn

# pandas用のデータフレーム作成
def making_df():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM health_tb')
    df = pd.io.json.json_normalize(cur.fetchall()).loc[:,
         ["id", "name", "age", "height", "weight", "bmi"]]
    cur.close()
    conn.close()
    return df

# クラス使わなくてもいいけど無理やり使う
class Human():

    def __init__(self, name, height, weight, age):
        self.height = height
        self.weight = weight
        self.name = name
        
    def bmi(self):
        return self.weight / (self.height / 100) ** 2

# Flaskクラスのインスタンスを作成
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', time=time.time())

@app.route('/list')
def list():
    df = making_df()
    table = df.drop('id', axis=1).to_html(header='true', index=False, escape=False)
    return render_template('list.html', time=time.time(), title="Data List", table=table)

@app.route('/input')
def input():
    return render_template('input.html', time=time.time(), title="Data Input Form")

@app.route('/ranking')
def ranking():
    df = making_df()
    df = df.sort_values('bmi')
    if len(df.index) == 1:
        df['rank'] = [1]
    else:
        df['rank'] = range(1, len(df)+1)
    table = df.drop('id', axis=1).loc[:,
         ["rank", "name", "age", "height", "weight", "bmi"]].to_html(header='true', index=False, escape=False)
    return render_template('ranking.html', time=time.time(), title="Ranking", table=table)

@app.route('/confirm', methods=['POST', 'GET'])
def confirm():
    if not request.form['name'] or not request.form['height'] or not request.form['weight'] or not request.form['age']:
        return render_template('input.html', time=time.time(), title="Data Input Form", error="You shoud input all data!")
    
    name = request.form['name']
    height = float(request.form['height'])
    weight  = float(request.form['weight'])
    age  = int(request.form['age'])
    return render_template('confirm.html', time=time.time(), title="Confirm Your Input Data", name=name, height=height, weight=weight, age=age)

@app.route('/input2db', methods=['POST', 'GET'])
def input2db():
    # POSTデータの受け取り
    if request.method == 'POST':
        name = request.form['name']
        height = float(request.form['height'])
        weight  = float(request.form['weight'])
        age  = int(request.form['age'])

        # bmi計算。クラスを無理やり使う。BMIは有効数字二桁
        human = Human(name, height, weight, age)
        bmi = round(human.bmi(), 2)

        # データベース接続
        conn = connect_db()

        # データベースにINSERT
        cur = conn.cursor(dictionary=True)
        cur.execute('insert into health_tb (name, height, weight, age, bmi) values (\"{}\",{},{},{},{})'.format(
            name, height, weight, age, bmi))
        conn.commit()
        cur.close()
        conn.close()
        return render_template('input_success.html', time=time.time(), title="Input Success")
    else:
        return render_template('input.html', time=time.time(), title="Data Input Form", error="You shoud input all data!")
 
if __name__ == "__main__":
    app.run(debug=True)
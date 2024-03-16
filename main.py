from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
MENU = [
    {"name": "Пицца Маргарита", "price": 350, "weight": "300г"},
    {"name": "Пицца Пепперони", "price": 450, "weight": "400г"},
    {"name": "Пицца 4 сыра", "price": 500, "weight": "450г"},
]


def init_db():
    conn = sqlite3.connect('pizzaparadise.db')
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, 
        password TEXT)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, author TEXT, 
        rating INTEGER, comment TEXT, FOREIGN KEY(user_id) REFERENCES users(id))''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, pizza_name TEXT, 
        quantity INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()


init_db()

if __name__ == '__main__':
    app.run(debug=True)

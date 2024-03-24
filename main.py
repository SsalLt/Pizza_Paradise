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


@app.route('/')
def index():
    user_id = get_user_id()
    return render_template('index.html', user_id=user_id)


@app.route('/menu')
def menu():
    user_id = get_user_id()
    return render_template('menu.html', MENU=MENU, user_id=user_id)


@app.route('/about')
def about():
    user_id = get_user_id()
    return render_template('about.html', user_id=user_id)


@app.route('/reviews')
def reviews():
    conn = sqlite3.connect('pizzaparadise.db')
    cursor = conn.cursor()
    cursor.execute('SELECT reviews.*, users.username FROM reviews JOIN users ON reviews.user_id = users.id')
    reviews_data = cursor.fetchall()
    user_id = get_user_id()
    review_exists = False
    if user_id is not None:
        review_exists = cursor.execute('SELECT * FROM reviews WHERE user_id = ?', (user_id,)).fetchone() is not None
    conn.close()
    return render_template('reviews.html', reviews_data=reviews_data, user_id=user_id, review_exists=review_exists,
                           none=None)


@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = get_user_id()
    if user_id is None:
        return redirect(url_for('reviews'))
    author = request.form.get("author")
    rating = int(request.form.get("rating"))
    comment = request.form.get("comment")
    conn = sqlite3.connect('pizzaparadise.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reviews (user_id, author, rating, comment) VALUES (?, ?, ?, ?)',
                   (user_id, author, rating, comment))
    conn.commit()
    conn.close()
    return redirect(url_for('reviews'))


@app.route('/cart')
def cart():
    user_id = get_user_id()
    if user_id is None:
        error_message = 'Ошибка: Для просмотра корзины необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, error_message=error_message, none=None)
    cart_items = []
    total_price = 0
    conn = sqlite3.connect('pizzaparadise.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cart WHERE user_id = ?', (user_id,))
    cart_data = cursor.fetchall()
    for item in cart_data:
        pizza = next((p for p in MENU if p["name"] == item[2]), None)
        if pizza:
            cart_items.append({"name": pizza["name"], "price": pizza["price"], "quantity": item[3]})
            total_price += pizza["price"] * item[3]
    conn.close()
    return render_template('cart.html', user_id=user_id, cart_items=cart_items, total_price=total_price)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = get_user_id()
    if user_id is None:
        error_message = 'Ошибка: Для добавление в корзину необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, error_message=error_message, none=None)
    name = request.form.get("name")
    price = int(request.form.get("price"))
    conn = sqlite3.connect('pizzaparadise.db')
    cursor = conn.cursor()
    existing_item = cursor.execute('SELECT * FROM cart WHERE user_id = ? AND pizza_name = ?',
                                   (user_id, name)).fetchone()
    if existing_item:
        cursor.execute('UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND pizza_name = ?', (user_id, name))
    else:
        cursor.execute('INSERT INTO cart (user_id, pizza_name, quantity) VALUES (?, ?, ?)', (user_id, name, 1))
    conn.commit()
    conn.close()
    return redirect("/cart")


def get_login_reg_buttons(user_id):
    return render_template('login_reg_buttons.html', user_id=user_id)


def get_user_id():
    return session.get('user_id')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = ''
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        conn = sqlite3.connect('pizzaparadise.db')
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                              (username, password)).fetchone()
        conn.close()
        if user is not None:
            session['user_id'] = user[0]  # Устанавливаем user_id в сессии
            return redirect(url_for('menu'))
        else:
            error_message = 'Неверный логин или пароль.'
    return render_template('login.html', error_message=error_message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = ''
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        conn = sqlite3.connect('pizzaparadise.db')
        cursor = conn.cursor()
        existing_user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if existing_user is not None:
            error_message = 'Такой логин уже используется.'
        else:
            conn = sqlite3.connect('pizzaparadise.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    return render_template('register.html', error_message=error_message)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

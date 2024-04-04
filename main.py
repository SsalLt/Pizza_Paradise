from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizzaparadise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pizzaparadise.staff@yandex.ru'
app.config['MAIL_PASSWORD'] = 'wwigfvvgjboxmfvt'
mail = Mail(app)
MENU = [
    {"name": "Пицца Маргарита", "price": 350, "weight": "300г"},
    {"name": "Пицца Пепперони", "price": 450, "weight": "400г"},
    {"name": "Пицца 4 сыра", "price": 500, "weight": "450г"},
]
total_price = 0
cart_items = []


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    reviews = db.relationship('Review', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pizza_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


def get_login_reg_buttons(user_id):
    return render_template('login_reg_buttons.html', user_id=user_id)


def get_user_id():
    return session.get('user_id')


def get_email(user_id):
    user = User.query.get(user_id)
    return user.username


@app.route('/')
def index():
    user_id = get_user_id()
    return render_template('index.html', user_id=user_id)


@app.route('/menu')
def menu():
    user_id = get_user_id()
    session['payment_confirmation_sent'] = False
    return render_template('menu.html', MENU=MENU, user_id=user_id)


@app.route('/about')
def about():
    user_id = get_user_id()
    return render_template('about.html', user_id=user_id)


@app.route('/reviews')
def reviews():
    reviews_data = Review.query.join(User).add_columns(Review.id, User.username, Review.author, Review.rating,
                                                       Review.comment).all()
    user_id = get_user_id()
    review_exists = Review.query.filter_by(user_id=user_id).first() is not None if user_id is not None else False
    print(reviews_data)
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
    review = Review(user_id=user_id, author=author, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('reviews'))


@app.route('/cart')
def cart():
    global total_price
    global cart_items
    user_id = get_user_id()
    if user_id is None:
        error_message = 'Ошибка: Для просмотра корзины необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, error_message=error_message, none=None)
    cart_items = []
    total_price = 0
    cart_data = CartItem.query.filter_by(user_id=user_id).all()
    for item in cart_data:
        pizza = next((p for p in MENU if p["name"] == item.pizza_name), None)
        if pizza:
            cart_items.append({"name": pizza["name"], "price": pizza["price"], "quantity": item.quantity})
            total_price += pizza["price"] * item.quantity
    return render_template('cart.html', user_id=user_id, cart_items=cart_items, total_price=total_price)


# Обработчик для страницы оплаты


@app.route('/process_payment', methods=['POST'])
def process_payment():
    global total_price
    user_id = get_user_id()
    if user_id is None:
        error_message = 'Ошибка: Для просмотра статуса необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, error_message=error_message, none=None)
    if request.method == 'POST':
        card_number = request.form.get("card_number")
        if request.form.get("expiry_date").split('/'):
            exp_month, exp_year = request.form.get("expiry_date").split('/')
        else:
            error_message = 'Ошибка: Неверный формат даты окончания действия карты.'
            return render_template('payment_failure.html', user_id=user_id, error_message=error_message, none=None)

        cvc = request.form.get("cvc")
        if len(card_number) != 16 or not card_number.isdigit():
            error_message = 'Ошибка: Неверный номер карты.'
            return render_template('payment_failure.html', user_id=user_id, error_message=error_message, none=None)

        if not (1 <= int(exp_month) <= 12):
            error_message = 'Ошибка: Неверный месяц окончания срока действия карты.'
            return render_template('payment_failure.html', user_id=user_id, error_message=error_message, none=None)

        current_year = datetime.now().year
        if current_year <= int(exp_year) <= current_year + 10:
            error_message = 'Ошибка: Неверный год окончания срока действия карты.'
            return render_template('payment_failure.html', user_id=user_id, error_message=error_message, none=None)

        if len(cvc) != 3 or not cvc.isdigit():
            error_message = 'Ошибка: Неверный CVV/CVC.'
            return render_template('payment_failure.html', user_id=user_id, error_message=error_message, none=None)
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return redirect('/payment_success')

    return "Ошибка: Неверный метод запроса"


@app.route('/payment_success', methods=['GET', 'POST'])
def payment_success():
    print(session)
    global total_price
    user_id = get_user_id()
    user = User.query.get(user_id)
    if not session['payment_confirmation_sent'] and user:
        send_payment_confirmation_email(user.username, total_price)
        session['payment_confirmation_sent'] = True  # Устанавливаем флаг в сессии
    return render_template('payment_success.html', user_id=user_id, total_price=total_price)


def send_payment_confirmation_email(recipient_email, price):
    subject = "Подтверждение покупки"
    body = f"Уважаемый пользователь, ваша покупка в размере {price} рублей успешно обработана. Спасибо за ваш заказ!"
    msg = Message(subject, sender='pizzaparadise.staff@yandex.ru', recipients=[recipient_email])
    msg.body = body
    # Вложение изображения
    # with app.open_resource("path/to/your/image.jpg") as fp:
    #     msg.attach("image.jpg", "image/jpg", fp.read())
    mail.send(msg)


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    global total_price
    global cart_items
    user_id = get_user_id()
    discount = 20
    if user_id is None:
        error_message = 'Ошибка: Для оплаты необходимо выполнить вход.'
        return render_template('testpayment.html', user_id=user_id, error_message=error_message, none=None)

    if request.method == 'POST':
        return render_template('testpayment.html', user_id=user_id, total_price=total_price, cart_items=[cart_items],
                               discount=discount)

    return render_template('testpayment.html', total_price=total_price, user_id=user_id)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = get_user_id()
    if user_id is None:
        error_message = 'Ошибка: Для добавление в корзину необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, error_message=error_message, none=None)
    name = request.form.get("name")
    existing_item = CartItem.query.filter_by(user_id=user_id, pizza_name=name).first()
    if existing_item:
        existing_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, pizza_name=name, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    return redirect("/menu")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = ''
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        print(user)
        if user is not None:
            session['user_id'] = user.id
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
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            error_message = 'Такой логин уже используется.'
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id  # Устанавливаем user_id в сессии
            return redirect(url_for('login'))
    return render_template('register.html', error_message=error_message)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

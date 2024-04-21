from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizzaparadise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/images/avatars'  # Папка для сохранения загруженных файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Разрешенные типы файлов
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pizzaparadise.staff@yandex.ru'
app.config['MAIL_PASSWORD'] = 'wwigfvvgjboxmfvt'
mail = Mail(app)
MENU = [
    {"name": "Маргарита", "price": 350, "weight": "300г", "image": r'static\images\pizza\М.jpg'},
    {"name": "Пепперони", "price": 450, "weight": "400г", "image": r'static\images\pizza\П.jpg'},
    {"name": "4 сыра", "price": 500, "weight": "450г", "image": r'static\images\pizza\4.jpg'},
]

total_price = 0
cart_items = []
promo_in_rub = 0
new_total_price = 0
card_num = None
CVV = None
expiry_date = None
paypal_mail = None

PROMO = {"зимняя сказка": 99}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(100), nullable=True)  # Имя файла аватара

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
    username = None
    if user_id:
        username = get_email(user_id)
    return render_template('login_reg_buttons.html', user_id=user_id, username=username)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_id():
    return session.get('user_id')


def get_email(user_id):
    user = User.query.get(user_id)
    return user.username


def get_fullname(user_id):
    user = User.query.get(user_id)
    return user.first_name, user.last_name


@app.route('/')
@app.route('/index')
def index():
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    return render_template('index.html', user_id=user_id, username=username,
                           first_name=first_name, last_name=last_name)


@app.route('/menu')
def menu():
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    session['payment_confirmation_sent'] = False
    return render_template('menu.html', MENU=MENU, user_id=user_id,
                           username=username, first_name=first_name, last_name=last_name)


@app.route('/about')
def about():
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    return render_template('about.html', user_id=user_id,
                           username=username, first_name=first_name, last_name=last_name)


@app.route('/reviews')
def reviews():
    reviews_data = Review.query.join(User).add_columns(Review.id, User.username, Review.author, Review.rating,
                                                       Review.comment).all()
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    print(username)
    review_exists = Review.query.filter_by(user_id=user_id).first() is not None if user_id is not None else False
    return render_template('reviews.html', reviews_data=reviews_data,
                           user_id=user_id, username=username, review_exists=review_exists,
                           none=None, first_name=first_name, last_name=last_name)


@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = get_user_id()
    if user_id is None:
        return redirect(url_for('reviews'))
    author = (request.form.get("author")).lstrip('Имя пользователя: ')
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
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    if user_id is None:
        error_message = 'Ошибка: Для просмотра корзины необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, username=username, error_message=error_message,
                               none=None, first_name=first_name, last_name=last_name)
    cart_items = []
    total_price = 0
    cart_data = CartItem.query.filter_by(user_id=user_id).all()
    for item in cart_data:
        pizza = next((p for p in MENU if p["name"] == item.pizza_name), None)
        if pizza:
            cart_items.append({"name": pizza["name"], "price": pizza["price"], "quantity": item.quantity})
            total_price += pizza["price"] * item.quantity
    return render_template('cart.html', user_id=user_id, username=username, cart_items=cart_items,
                           total_price=total_price, first_name=first_name, last_name=last_name)


def get_info():
    print(request.form)
    paypal_email = request.form.get("paypal")
    card_number = request.form.get("card_number")
    cvc = request.form.get("cvc")
    expiry_date = request.form.get("expiry_date")

    if paypal_email:
        return paypal_email, 'paypal'
    elif card_number and cvc and expiry_date:
        return card_number, cvc, expiry_date
    else:
        return None


@app.route('/process_payment', methods=['POST'])
def process_payment():
    global total_price
    global CVV
    global card_num
    global expiry_date
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    if user_id is None:
        error_message = 'Ошибка: Для просмотра статуса необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, username=username, error_message=error_message,
                               none=None, first_name=first_name, last_name=last_name)
    if request.method == 'POST':
        data = get_info()
        if data:
            if 'paypal' in data:
                return redirect('/payment_success')
            else:
                card_number, cvc, expiry_date = data
                if '/' in expiry_date:
                    exp_month, exp_year = expiry_date.split('/')
                else:
                    error_message = 'Ошибка: Неверный формат даты окончания действия карты.'
                    return render_template('payment_failure.html', user_id=user_id, username=username,
                                           error_message=error_message,
                                           none=None, first_name=first_name, last_name=last_name)
                if ' ' in card_number:
                    card_number: str = card_number.replace(' ', '')
                    # print(card_number, type(card_number))
                if len(card_number) != 16 or not card_number.isdigit():
                    error_message = 'Ошибка: Неверный номер карты.'
                    return render_template('payment_failure.html', user_id=user_id, username=username,
                                           error_message=error_message,
                                           none=None, first_name=first_name, last_name=last_name)

                if not (1 <= int(exp_month) <= 12):
                    error_message = 'Ошибка: Неверный месяц окончания срока действия карты.'
                    return render_template('payment_failure.html', user_id=user_id, username=username,
                                           error_message=error_message,
                                           none=None, first_name=first_name, last_name=last_name)

                current_year = datetime.now().year
                if current_year <= int(exp_year) <= current_year + 10:
                    error_message = 'Ошибка: Неверный год окончания срока действия карты.'
                    return render_template('payment_failure.html', user_id=user_id, username=username,
                                           error_message=error_message,
                                           none=None, first_name=first_name, last_name=last_name)

                if len(cvc) != 3 or not cvc.isdigit():
                    error_message = 'Ошибка: Неверный CVV/CVC.'
                    return render_template('payment_failure.html', user_id=user_id, username=username,
                                           error_message=error_message,
                                           none=None, first_name=first_name, last_name=last_name)
                return redirect('/payment_success')
        else:
            error_message = 'Ошибка: Неверный формат платёжных данных.'
            return render_template('payment_failure.html', user_id=user_id, username=username,
                                   error_message=error_message,
                                   none=None, first_name=first_name, last_name=last_name)

    return "Ошибка: Неверный метод запроса"


@app.route('/payment_success', methods=['GET', 'POST'])
def payment_success():
    global new_total_price
    global total_price
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    user = User.query.get(user_id)
    if new_total_price:
        price = new_total_price
    else:
        price = total_price
    if not session['payment_confirmation_sent']:
        send_payment_confirmation_email(user.username, price)
        session['payment_confirmation_sent'] = True  # Устанавливаем флаг в сессии
    return render_template('payment_success.html', user_id=user_id, username=username,
                           total_price=price, first_name=first_name, last_name=last_name)


@app.route('/apply_promo_code', methods=['POST'])
def apply_promo_code():
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    global CVV
    global card_num
    global expiry_date
    global total_price
    global promo_in_rub
    global paypal_mail
    global new_total_price
    error_message = None
    success_message = None
    data = get_info()
    new_discount = 0
    if data:
        if 'paypal' in data:
            paypal_mail = data[0]
        else:
            card_num, CVV, expiry_date = data
    else:
        paypal_mail = None
    new_total_price = total_price
    promo_code = request.form.get('promo_code')
    try:
        if PROMO[promo_code.lower()]:
            new_discount = int(PROMO[promo_code])
            promo_in_rub = round(total_price * (new_discount / 100), 2)
            success_message = f'Промокод на скидку {new_discount}% успешно активирован'
    except KeyError:
        error_message = 'Введен некорректный промокод'
        promo_in_rub = 0
        new_discount = 0

    new_total_price -= promo_in_rub
    return render_template('testpayment.html', discount=new_discount, total_price=new_total_price,
                           promo_in_rub=promo_in_rub, cart_items=[cart_items], user_id=user_id, username=username,
                           CVV=CVV, first_name=first_name, last_name=last_name,
                           expiry_date=expiry_date, card_num=card_num, paypal_mail=paypal_mail,
                           error_message=error_message, success_message=success_message)


def send_payment_confirmation_email(recipient_email, price):
    user_id = get_user_id()
    cart_data = CartItem.query.filter_by(user_id=user_id).all()

    subject = "Подтверждение покупки"
    body = f"Уважаемый пользователь, ваша покупка в размере {price} рублей успешно обработана. Спасибо за ваш заказ!"
    msg = Message(subject, sender='pizzaparadise.staff@yandex.ru', recipients=[recipient_email])
    msg.body = body

    pizza_quantities = {item.pizza_name: item.quantity for item in cart_data}

    for item in cart_data:
        pizza = next((p for p in MENU if p["name"] == item.pizza_name), None)
        if pizza:
            quantity = pizza_quantities.get(item.pizza_name, 0)
            for i in range(quantity):
                with app.open_resource(pizza["image"]) as fp:
                    filename = f"{pizza['name']}_{i}.jpg"  # Уникальное имя файла для каждого изображения
                    msg.attach(filename, "image/jpg", fp.read())
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    mail.send(msg)


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    global total_price
    global cart_items
    global promo_in_rub
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    discount = 0
    if user_id is None:
        error_message = 'Ошибка: Для оплаты необходимо выполнить вход.'
        return render_template('testpayment.html', user_id=user_id, username=username, error_message=error_message,
                               none=None, first_name=first_name, last_name=last_name)

    if request.method == 'POST':
        return render_template('testpayment.html', user_id=user_id, username=username, total_price=total_price,
                               cart_items=[cart_items], first_name=first_name, last_name=last_name,
                               discount=discount, promo_in_rub=promo_in_rub)

    return render_template('testpayment.html', total_price=total_price, username=username,
                           user_id=user_id, first_name=first_name, last_name=last_name)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = get_user_id()
    username = first_name = last_name = None
    if user_id:
        username = get_email(user_id)
        first_name, last_name = get_fullname(user_id)
    if user_id is None:
        error_message = 'Ошибка: Для добавление в корзину необходимо выполнить вход.'
        return render_template('cart.html', user_id=user_id, username=username,
                               first_name=first_name, last_name=last_name,
                               error_message=error_message, none=None)
    name = request.form.get("name")
    quantity = int(request.form.get('quantity'))
    existing_item = CartItem.query.filter_by(user_id=user_id, pizza_name=name).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, pizza_name=name, quantity=quantity)
        db.session.add(cart_item)
    success_mess = f'Вы добавили в корзину {name} - {quantity} шт. '
    db.session.commit()
    return render_template('menu.html', MENU=MENU, user_id=user_id, username=username,
                           first_name=first_name, last_name=last_name,
                           success_mess=success_mess)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = ''
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
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
        password1 = request.form.get("password1")
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            error_message = 'Такой логин уже используется.'
        elif password != password1:
            error_message = 'Введенные пароли не совпадают'
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


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = get_user_id()
    username = get_email(user_id)
    first_name, last_name = get_fullname(user_id)
    user = User.query.get(user_id)  # Получаем объект пользователя из базы данных
    print(user.avatar)
    if not user.avatar or not os.listdir('static/images/avatars'):
        user.avatar = '../default_avatar.jpg'
    if request.method == 'POST':
        return redirect(url_for('profile'))

    return render_template('profile.html', user_id=user_id, username=username,
                           user=user, first_name=first_name,
                           last_name=last_name)  # Передаем объект пользователя в шаблон


def delete_old_avatar(folder_path):
    # Получаем список файлов в папке
    files = os.listdir(folder_path)
    # Сортируем файлы по времени последнего доступа (по возрастанию)
    files.sort(key=lambda x: os.path.getatime(os.path.join(folder_path, x)))
    # Удаляем самый старый файл
    if files:
        os.remove(os.path.join(folder_path, files[0]))


@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = get_user_id()
    if user_id:
        user = User.query.get(user_id)
        if user:
            full_name = request.form['full_name'].lstrip()
            if ' ' in full_name:
                first_name, last_name = full_name.split(' ', 1)
                user.first_name = first_name.strip().capitalize()
                user.last_name = last_name.strip().capitalize()
            else:
                user.first_name = full_name.strip()
                user.last_name = ''
                # Обработка загруженного файла аватара
            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file and allowed_file(avatar_file.filename):
                    filename = secure_filename(avatar_file.filename)
                    # Удаляем самый старый аватар
                    delete_old_avatar(app.config['UPLOAD_FOLDER'])
                    # Сохраняем новый аватар
                    avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    user.avatar = filename  # Сохраняем имя файла в базе данных

                else:
                    user.avatar = '../default_avatar.jpg'  # Сохраняем имя файла в базе данных
        db.session.commit()
    return redirect(url_for('profile'))


@app.errorhandler(404)
def page_not_found(error):
    message_list = ['Неправильно набран адрес или такой',
                    'страницы больше не существует,',
                    'а возможно никогда и не существовало.']
    return render_template('error.html', error_type=404, error_message=message_list), 404


@app.errorhandler(500)
def internal_server_error(error):
    message_list = ['Внутренняя ошибка сервера.',
                    'Кажется, вы так много нажимали кнопки,',
                    'что сломали сервер. Спасибо!']
    return render_template('error.html', error_type=500, error_message=message_list), 500


@app.errorhandler(418)
def internal_server_error(error):
    message_list = ['Я чайник.',
                    'А что вы хотели?',
                    '']
    return render_template('error.html', error_type=418, error_message=message_list), 418


@app.errorhandler(401)
def unauthorized(error):
    message_list = ['Не авторизован.',
                    'Для данного действия',
                    'необходимо войти в аккаунт.']
    return render_template('error.html', error_type=401, error_message=message_list), 401


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)

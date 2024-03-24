from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizzaparadise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
mail = Mail(app)

MENU = [
    {"name": "Пицца Маргарита", "price": 350, "weight": "300г"},
    {"name": "Пицца Пепперони", "price": 450, "weight": "400г"},
    {"name": "Пицца 4 сыра", "price": 500, "weight": "450г"},
]


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
    return redirect("/cart")


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

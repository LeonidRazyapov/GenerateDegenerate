from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from connector import DataBase
from user import UserLogin
from datetime import datetime
import websockets
import shutil
import asyncio
import json
import os
import config

app = Flask(__name__, template_folder='templates', static_folder='static/')

login_manager = LoginManager(app)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{config.USERDB}:{config.PASSWORDDB}@{config.HOSTDB}/{config.DB}'
app.config['SECRET_KEY'] = 'a really really really really long secret key'
app.config['UPLOAD_FOLDER'] = 'static/images/'

db = DataBase(config.HOSTDB, config.USERDB, config.PASSWORDDB, config.DB)

dbAlchemy = SQLAlchemy(app)


async def get_path_image(positive, negative, x, y):
    async with websockets.connect("ws://127.0.0.1:7860/queue/join") as ws:
        await ws.send('{"fn_index":101,"session_hash":"ti92s1fazal"}')
        await ws.send(
            '{' + f'"data":["task(2yainx97p16qhdt)","{positive}","{negative}",[],1,1,7,{x},{y},false,0.7,2,"Latent",0,0,0,"anythingV3_fp16.safetensors","Use same sampler","Use same scheduler","","",[],"None",20,"DPM++ 2M","Automatic",false,"",0.8,-1,false,-1,0,0,0,false,false,"positive","comma",0,false,false,"start","","Seed","",[],"Nothing","",[],"Nothing","",[],true,false,false,false,false,false,false,0,false,[],"","",""],"event_data":null,"fn_index":101,"session_hash":"ti92s1fazal"' + '}')
        while True:
            try:
                result = await ws.recv()
            except Exception as e:
                break
        print(result)
        js = json.loads(result)
        name = js.get('output').get('data')[0]
        print(name)
        try:
            print(1)
            return name[0].get('name').rsplit('?', 2)[0]
        except Exception as e:
            print(e)


class Report(dbAlchemy.Model):
    __tablename__ = "reports"

    id = dbAlchemy.Column(dbAlchemy.Integer, primary_key=True)
    idUsers = dbAlchemy.Column(dbAlchemy.Integer, dbAlchemy.ForeignKey('users.id'), nullable=False)
    error = dbAlchemy.Column(dbAlchemy.String(64), unique=False, nullable=False)
    text = dbAlchemy.Column(dbAlchemy.String(2000), nullable=False)


class User(dbAlchemy.Model):
    __tablename__ = "users"

    id = dbAlchemy.Column(dbAlchemy.Integer, primary_key=True)
    name = dbAlchemy.Column(dbAlchemy.String(20), unique=False, nullable=False)
    email = dbAlchemy.Column(dbAlchemy.String(120), unique=False, nullable=False)
    password = dbAlchemy.Column(dbAlchemy.String(20), nullable=False)
    photo = dbAlchemy.Column(dbAlchemy.String(60), default='avatar.png', nullable=False)
    admin = dbAlchemy.Column(dbAlchemy.String(1), default='n', unique=False)


class Image(dbAlchemy.Model):
    __tablename__ = "images"

    id = dbAlchemy.Column(dbAlchemy.Integer, primary_key=True)
    idUsers = dbAlchemy.Column(dbAlchemy.Integer, nullable=True)
    path = dbAlchemy.Column(dbAlchemy.String(128), nullable=False)
    positive = dbAlchemy.Column(dbAlchemy.String(128), default='', nullable=False)
    negative = dbAlchemy.Column(dbAlchemy.String(128), default='', nullable=False)


class DashBoardView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        if current_user.user[5] == 'n':
            return redirect(url_for('login'))

        all_users = User.query.all()
        all_images = Image.query.all()
        return self.render('admin/dashboard_index.html', all_users=all_users, all_images=all_images)


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, db)


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if current_user.get_id() == None:
        return redirect(url_for('login'))

    if request.method == 'POST':

        if 'avatar' in request.files and request.files['avatar'].filename != '':

            file = request.files['avatar']
            if os.path.isfile(f'static/images/{current_user.user[0]}/{file.filename}'):
                os.remove(f'static/images/{current_user.user[0]}/{file.filename}')
            file.save(f'static/images/{current_user.user[0]}/{file.filename}')
            file.close()
            db.update_photo_by_id(current_user.user[0], file.filename)

        if 'email' in request.form and 'username' in request.form and 'password' in request.form:
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']

            db.update_user_by_id(current_user.user[0], username, email, password)

        return redirect(url_for('profile'))

    if request.query_string == b'edit':
        return render_template('profile_edit.html')
    return render_template('profile.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.get_id() != None:
        return redirect(url_for('profile'))

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = db.get_user_by_email(email)

        if user == None or user[3] != password:
            return render_template('login.html', error='Не верный пароль или email')

        if user[5] == 'y':
            if not 'pin-code' in request.form:
                return render_template('login.html', PIN=True, password=password, email=email)
            if not request.form['pin-code'] == '1448':
                return render_template('login.html', PIN=True, password=password, email=email,
                                       error='Не верный пин-код')

        userlogin = UserLogin().create(user)

        login_user(userlogin)

        return redirect(url_for('profile'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if db.is_exists_user(email):
            return render_template('register.html', error='Пользователь с таким email уже существует')

        db.registor(username, email, password)

        id = db.get_user_by_email(email)[0]
        if not os.path.isdir(f'static/images/{id}'):
            os.mkdir(f'static/images/{id}')
        shutil.copyfile('static/images/avatar.png', f'static/images/{id}/avatar.png')

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/', methods=['GET', 'POST'])
def image():
    global company
    idUser = 0
    name = 'chushpan.jpg'  # Default image name
    if request.method == 'POST':
        Positive = request.form.get('Positive')
        Negative = request.form.get('Negative')
        X = request.form.get('X')
        Y = request.form.get('Y')
        path = asyncio.run(get_path_image(Positive, Negative, X, Y))
        if path:
            new_path = os.path.join('static', 'images', os.path.basename(path))
            shutil.copy(path, new_path)
            name = os.path.basename(new_path)
        if current_user.get_id() != None:
            idUser = current_user.user[0]

        db.add_image(idUser, name, Positive, Negative)
    return render_template('home.html', img=name)  # render the HTML template


@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        if not ('where-error' in request.form and 'text' in request.form):
            return render_template('report.html')
        error = request.form['where-error']
        text = request.form['text']
        db.add_report(current_user.user[0], error, text)
        return render_template('report.html', status='Отправлено!')

    return render_template('report.html')  # render the HTML template


admin = Admin(app, name='Админка', template_mode='bootstrap3', index_view=DashBoardView(), endpoint='admin')
admin.add_view(ModelView(User, dbAlchemy.session, name='Пользователь'))
admin.add_view(ModelView(Image, dbAlchemy.session, name='Изображения'))
admin.add_view(ModelView(Report, dbAlchemy.session, name='Обращения'))

if __name__ == '__main__':
    with app.app_context():
        dbAlchemy.create_all()
    app.run(host='0.0.0.0', port='80', debug=True)

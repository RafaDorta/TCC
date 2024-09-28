from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo,Email
from pymongo import MongoClient
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['meu_banco']
users_collection = db['users']
users_graficos = db['graficos']


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(message="Insira um email válido")])
    password = PasswordField('Senha', validators=[DataRequired(), EqualTo('confirm', message='As senhas devem coincidir')])
    confirm = PasswordField('Confirme a Senha', validators=[DataRequired()])
    submit = SubmitField('Criar Conta')

class ForgotPasswordForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    submit = SubmitField('Enviar E-mail de Recuperação')

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
@login_required
def index():
    return render_template('index.html', name=current_user.id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_data = users_collection.find_one({'username': username})
        if user_data and user_data['password'] == password:
            user = User(username)
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('success'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        existing_user = users_collection.find_one({'username': username})
        existing_email = users_collection.find_one({'email': email})

        if existing_user is None and existing_email is None:
            users_collection.insert_one({'username': username, 'email': email, 'password': password})
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('login'))
        elif existing_user:
            flash('Usuário já existe. Escolha outro nome de usuário.', 'danger')
        elif existing_email:
            flash('Este email já está em uso. Escolha outro email.', 'danger')
            
    return render_template('register.html', form=form)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        username = form.username.data
        user_data = users_collection.find_one({'username': username})
        if user_data:
            flash(f'E-mail de recuperação enviado para o usuário {username}.', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
    return render_template('forgot_password.html', form=form)

@app.route('/success')
@login_required
def success():
    return render_template('success.html', name=current_user.id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/graficos', methods=['GET', 'POST'])
@login_required
def grafico():
    labels = []
    data = []
    
    if request.method == 'POST':
        # Obter as datas do formulário
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Converter as strings de data para objetos datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Fazer a consulta no MongoDB com base nas datas
        query = {
            'data': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        results = list(users_graficos.find(query))

        

        # Extrair os dados para os gráficos
        labels = [result['date'].strftime('%Y-%m-%d') for result in results] 
        data = [result['speed'] for result in results]

    # Renderizar o template com os dados do gráfico
    return render_template('grafico.html', labels=json.dumps(labels), data=json.dumps(data))

if __name__ == "__main__":
    app.run(debug=True)

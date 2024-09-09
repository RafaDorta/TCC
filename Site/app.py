from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from pymongo import MongoClient
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['meu_banco']  # Substitua pelo nome do seu banco de dados
collection = db['meu_collection']  # Substitua pelo nome da sua coleção

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuários fictícios (substitua por banco de dados em produção)
users = {'admin': {'password': '1234'}}

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

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
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('success'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
    return render_template('login.html', form=form)

@app.route('/success')
@login_required
def success():
    return render_template('success.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# Nova rota para gráficos
@app.route('/graficos', methods=['GET', 'POST'])
@login_required
def grafico():
    labels = []
    data = []
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Converter datas para datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Buscar dados no MongoDB com base nas datas
        query = {'data': {'$gte': start_date, '$lte': end_date}}
        results = list(collection.find(query))

        labels = [result['data'].strftime('%Y-%m-%d') for result in results]
        data = [result['valor'] for result in results]  # Substitua 'valor' pela chave correta do seu dado

    return render_template('grafico.html', labels=json.dumps(labels), data=json.dumps(data))

if __name__ == "__main__":
    app.run(debug=True)

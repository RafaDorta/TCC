from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo,Email
from pymongo import MongoClient
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DecimalField, TimeField
from wtforms.validators import DataRequired, NumberRange
from flask import Flask, render_template, redirect, url_for, flash, request
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from bson import ObjectId
import matplotlib.pyplot as plt
import os
from collections import Counter
from datetime import datetime
import os
import matplotlib
matplotlib.use('Agg')  # Define o backend não interativo do matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from wtforms import DateField
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['meu_banco']
users_collection = db['users']
users_graficos = db['graficos']
services_collection = db['services']



app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Ou outro servidor SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'roadguard.notreply@gmail.com'  # Seu e-mail
app.config['MAIL_PASSWORD'] = 'Teste1234*'  # Sua senha ou senha de app
app.config['MAIL_DEFAULT_SENDER'] = 'roadguard.notreply@gmail.com'  # E-mail padrão

mail = Mail(app)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



class ServiceForm(FlaskForm):
    name = StringField('Nome do Serviço', validators=[DataRequired()])
    departure = StringField('Local de Saída', validators=[DataRequired()])
    arrival = StringField('Local de Chegada', validators=[DataRequired()])
    time = TimeField('Horário', validators=[DataRequired()])
    price = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Data', format='%Y-%m-%d', validators=[DataRequired()]) 
    submit = SubmitField('Criar Serviço')


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
    return render_template('login.html', name=current_user.id)

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
            # Envia e-mail com a senha
            msg = Message('Recuperação de Senha',
                          recipients=[user_data['email']])
            msg.body = f'Sua senha atual é: {user_data["password"]}'
            mail.send(msg)
            flash(f'E-mail de recuperação enviado para {user_data["email"]}.', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
    return render_template('forgot_password.html', form=form)


@app.route('/success')
@login_required
def success():
    # Obtém a data e hora atuais
    current_datetime = datetime.utcnow()

    # Busca os próximos serviços que o usuário pegou
    upcoming_services = list(services_collection.find({
        'designated_for': current_user.id,
        'date': {'$gte': current_datetime}  # Filtra serviços pela data e hora atuais
    }).sort('date', 1))  # Ordena por data para pegar o próximo serviço

    # Busca o último serviço realizado pelo usuário
    recent_service = services_collection.find_one({
        'designated_for': current_user.id,
        'date': {'$lt': current_datetime}  # Filtra serviços que foram realizados antes da data atual
    }, sort=[('date', -1)])  # Ordena pela data, do mais recente para o mais antigo

    return render_template('success.html', name=current_user.id, upcoming_services=upcoming_services, recent_service=recent_service)





@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/graficos', methods=['GET', 'POST'])
@login_required
def grafico():
    users = users_graficos.distinct("username")  # Obtém os usuários distintos
    results = []

    if request.method == 'POST':
        username = request.form['username']
        selected_month = int(request.form['month'])
        query = {'username': username}

        # Ordena os resultados pela data, do mais recente para o mais antigo
        results = list(users_graficos.find(query).sort('date', -1))

        # Converte as strings de data para objetos datetime e filtra pelo mês selecionado
        dates = []
        for result in results:
            if isinstance(result['date'], str):
                result['date'] = datetime.strptime(result['date'], '%d/%m/%Y, %H:%M:%S')
            # Verificar se o mês da data corresponde ao mês selecionado
            if result['date'].month == selected_month:
                dates.append(result['date'].date())  # Pega apenas a data (sem horário)

        # Conta as ocorrências por dia
        date_counts = Counter(dates)

        # Preparar os dados para o gráfico
        sorted_dates = sorted(date_counts.keys())
        occurrences = [date_counts[date] for date in sorted_dates]

        # Gera o gráfico
        plt.figure(figsize=(10, 6))
        plt.plot(sorted_dates, occurrences, marker='o')

        # Definindo os ticks no eixo X para mostrar cada dia do mês selecionado
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

        plt.xlabel('Datas')
        plt.ylabel('Ocorrências')
        plt.title(f'Ocorrências por dia para o usuário {username} no mês {selected_month}')
        plt.xticks(rotation=45)  # Rotaciona as datas no eixo X para facilitar a leitura

        # Salva o gráfico como imagem no diretório estático
        image_filename = f'grafico_{username}_{selected_month}.png'
        image_path = os.path.join('static', image_filename)
        plt.savefig(image_path)
        plt.close()  # Fecha o gráfico para liberar a memória

        return render_template('grafico.html', users=users, image_path=image_filename)

    # Caso o método seja GET, renderiza o formulário
    return render_template('grafico.html', users=users)


@app.route('/relatorio', methods=['GET', 'POST'])
@login_required
def relatorio():
    users = users_graficos.distinct("username")
    results = []

    if request.method == 'POST':
        username = request.form['username']
        query = {'username': username}
        # Ordena os resultados pela data do mais recente para o mais antigo
        results = list(users_graficos.find(query).sort('date', -1))

        # Converte as strings de data para objetos datetime
        for result in results:
            if isinstance(result['date'], str):
                result['date'] = datetime.strptime(result['date'], '%d/%m/%Y, %H:%M:%S')

    return render_template('relatorio.html', results=results, users=users)

@app.route('/graficos/pdf', methods=['POST'])
@login_required
def generate_pdf():
    username = request.form['username']
    query = {'username': username}
    results = list(users_graficos.find(query).sort('date', -1))

    # Cria um buffer para o PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Adiciona o logo e título
    logo_path = 'logo.jpg'  # Atualize com o caminho do logo
    p.drawImage(logo_path, 200, 700, width=200, height=100)  # Logo centralizado
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(300, 650, f'Histórico de Alertas - Usuário: {username}')
    
    # Configurações de layout
    y = 620
    p.setFont("Helvetica", 10)
    
    # Loop para os resultados e formatação de texto
    for result in results:
        if isinstance(result['date'], str):
            result['date'] = datetime.strptime(result['date'], '%d/%m/%Y, %H:%M:%S')

        # Obtém o endereço e a velocidade
        endereco = result.get("address", "Endereço não disponível")
        velocidade = result.get("speed", "Velocidade não disponível")

        # Adiciona os dados no estilo solicitado (negrito e bem formatado)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, f"• Data: {result['date'].strftime('%d/%m/%Y')}")
        y -= 15

        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, f"Local:")
        p.setFont("Helvetica", 10)
        p.drawString(150, y, endereco)
        y -= 15

        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, f"Horário:")
        p.setFont("Helvetica", 10)
        p.drawString(150, y, result['date'].strftime('%H:%M:%S'))
        y -= 15  # Aumentado o espaço antes da velocidade

        # Formata a velocidade com duas casas decimais
        if isinstance(velocidade, (int, float)):
            velocidade = round(velocidade, 2)  # Arredonda para duas casas decimais

        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, f"Velocidade:")
        p.setFont("Helvetica", 10)
        p.drawString(170, y, f"{velocidade} KM/H")  # Posição ajustada para evitar sobreposição
        y -= 30  # Espaçamento extra entre blocos de informações

        if y < 50:  # Verifica se precisa iniciar uma nova página
            p.showPage()
            y = 750

    p.save()

    # Envia o PDF como resposta
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'alertas-{username}.pdf', mimetype='application/pdf')


@app.route('/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    form = ServiceForm()  # Instancia o formulário

    # Coleta todos os usuários cadastrados
    all_users = users_collection.distinct("username")

    if form.validate_on_submit():
        # Captura os dados do formulário
        service_name = form.name.data
        departure = form.departure.data
        arrival = form.arrival.data
        time = form.time.data
        price = float(form.price.data)  # Converte Decimal para float
        date = form.date.data  # Captura a data

        # Verifica se já existe um serviço com o mesmo nome
        existing_service = services_collection.find_one({'name': service_name})

        if existing_service:
            flash('Já existe um serviço com este nome.', 'danger')
        else:
            # Insere o novo serviço no banco, vinculado ao usuário atual
            services_collection.insert_one({
                'name': service_name,
                'departure': departure,
                'arrival': arrival,
                'time': time.strftime('%H:%M'),  # Formato HH:MM
                'price': price,  # Preço como float
                'date': datetime.combine(date, datetime.min.time()),  # Converte a data para datetime
                'created_by': current_user.id,
                'created_at': datetime.utcnow()
            })
            flash('Serviço criado com sucesso!', 'success')
            return redirect(url_for('servicos'))  # Redireciona para a lista de serviços

    # Busca todos os serviços existentes
    services = list(services_collection.find({'created_by': current_user.id}))  # Converte o cursor em uma lista

    # Contar alertas por usuário
    user_alert_counts = users_graficos.aggregate([
        {"$group": {"_id": "$username", "count": {"$sum": 1}}}
    ])

    # Criar um dicionário com contagens de alertas
    alert_counts = {user["_id"]: user["count"] for user in user_alert_counts}

    # Ordenar e pegar os 3 usuários com menos alertas
    top_users = sorted(alert_counts.items(), key=lambda x: x[1])[:3]

    return render_template('servicos.html', services=services, form=form, top_users=top_users, all_users=all_users)



@app.route('/designate_service/<service_id>', methods=['POST'])
@login_required
def designate_service(service_id):
    username_to_designate = request.form['username']
    user_data = users_collection.find_one({'username': username_to_designate})

    if not user_data:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('servicos'))

    # Verifica se o serviço já tem um designado
    service = services_collection.find_one({'_id': ObjectId(service_id)})
    if service.get('designated_for'):
        flash('Este serviço já foi designado a outro usuário.', 'danger')
        return redirect(url_for('servicos'))

    # Atualiza o serviço com o usuário designado
    services_collection.update_one(
        {'_id': ObjectId(service_id)},
        {'$set': {'designated_for': user_data['username']}}
    )
    flash(f'Serviço designado para {username_to_designate} com sucesso!', 'success')
    return redirect(url_for('servicos'))




@app.route('/pegar_servico/<service_id>', methods=['POST'])
@login_required
def pegar_servico(service_id):
    service = services_collection.find_one({'_id': ObjectId(service_id)})

    if service:
        if service.get('taken_by'):
            flash('Este serviço já foi designado a outro usuário.', 'danger')
        else:
            assigned_user = request.form['assign_to']  # Obtem o usuário designado

            # Atualiza o serviço com o usuário designado
            services_collection.update_one(
                {'_id': ObjectId(service_id)},
                {'$set': {'taken_by': assigned_user}}
            )
            flash(f'O serviço foi designado para {assigned_user} com sucesso!', 'success')
    else:
        flash('Serviço não encontrado.', 'danger')

    return redirect(url_for('servicos'))







if __name__ == "__main__":
    app.run(debug=True)

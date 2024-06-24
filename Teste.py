from datetime import datetime
import geocoder
from geopy.geocoders import Nominatim
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time
import random
from pymongo import MongoClient
import gridfs
from googlemaps import exceptions
import googlemaps


textoPDF= ""
loc= ""
locFim =" "


_GEOLOCATION_BASE_URL = "https://www.googleapis.com"
client = googlemaps.Client(key='AIzaSyD-ddpqUaS0PfKqJ45DRb49wMVtRyT-idg')

def get_address_from_coordinates(latitude, longitude):
    result = client.reverse_geocode((latitude, longitude))
    if result:
        return result[0]['formatted_address']
    else:
        return "Endereço não encontrado."
    

def calcular_distancia_tempo(origem, destino):
    now = datetime.now()
    directions_result = client.directions(origem, destino, mode="driving", departure_time=now)

    if directions_result:
        # Extrair distância e duração da resposta
        distancia_em_metros = directions_result[0]['legs'][0]['distance']['value']
        distancia_km = distancia_em_metros /1000
        duracao_segundos = directions_result[0]['legs'][0]['duration']['value']
        duracao_horas = duracao_segundos / 3600 
        return distancia_km, duracao_horas
    else:
        return None, None


def _geolocation_extract(response):
    body = response.json()
    if response.status_code in (200, 404):
        return body

    try:
        error = body["error"]["errors"][0]["reason"]
    except KeyError:
        error = None

    if response.status_code == 403:
        raise exceptions._OverQueryLimit(response.status_code, error)
    else:
        raise exceptions.ApiError(response.status_code, error)


def geolocate(client, home_mobile_country_code=None,
              home_mobile_network_code=None, radio_type=None, carrier=None,
              consider_ip=None, cell_towers=None, wifi_access_points=None):

    params = {}
    if home_mobile_country_code is not None:
        params["homeMobileCountryCode"] = home_mobile_country_code
    if home_mobile_network_code is not None:
        params["homeMobileNetworkCode"] = home_mobile_network_code
    if radio_type is not None:
        params["radioType"] = radio_type
    if carrier is not None:
        params["carrier"] = carrier
    if consider_ip is not None:
        params["considerIp"] = consider_ip
    if cell_towers is not None:
        params["cellTowers"] = cell_towers
    if wifi_access_points is not None:
        params["wifiAccessPoints"] = wifi_access_points

    return client._request("/geolocation/v1/geolocate", {},  # No GET params
                           base_url=_GEOLOCATION_BASE_URL,
                           extract_body=_geolocation_extract,
                           post_json=params)


def dbConnect():
    try:
        client = MongoClient("mongodb+srv://root:root@cluster0.imwfnaa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        dbConnection = client["TCC"]
        return dbConnection
    except Exception as e:
        print("Error in DB Connect:", e)
   

def geraTexto(texto):
    data = texto[2:6]  +": "+ texto[10:20]
    hora = "Hora: " + texto[22:30]
    loc = "Localização: " + texto[34:42] +": "+ texto[46:52] +"  " + texto[58:68] +":"+ texto[70:78]
    textoFinal = data +"     "+  hora + "     "+ loc + "+"
    return textoFinal

def gerar_pdf(nome_arquivo, texto,vm):
    c = canvas.Canvas(nome_arquivo, pagesize=letter)
    c.drawImage("logo.jpg", 200,650, 200, 100)
    c.drawString(250, 600, "Histórico de Alertas")
    final = texto.split('+')
    x,y=80,550
    for frases in final:
        c.drawString(x ,y,frases)
        y = y - 30
    
    c.drawString(200 ,y,"Velocidade Média: ")
    c.drawString(310 ,y,vm + 'KM/H')
    c.save()
    client = dbConnect()
    fs = gridfs.GridFS(client)
    with open("c:/Users/raffa/Downloads/Teste TCC/Teste.pdf", "rb") as arquivo:
        dados_pdf = arquivo.read()
    fs.put(dados_pdf, filename="teste.pdf")

    print("Upload completed")


def gerarRelatorio(lista):
    result = geolocate(client, wifi_access_points=[{'macAddress': '56-7F-8C-9A-D0-20'}])
    latitude = result['location']['lat']
    longitude = result['location']['lng']
    global loc 
    loc = get_address_from_coordinates(latitude,longitude)
    
    lista.append({
        'Data': datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
        'Latitude': latitude,
        'Longitude': longitude
    })
    
    return lista

def geraOcorrencia():
    listaAlertas = []
    gerarRelatorio(listaAlertas)
    string_resultante = ''.join([str(d) for d in listaAlertas])
    txt = geraTexto(string_resultante)
    return txt

with open("exemplo.txt", "r") as arquivo:
    conteudo = arquivo.read()

texto = geraOcorrencia()
loc_Inicial = loc
print(loc_Inicial)
time.sleep(15)
txt2 = geraOcorrencia()
loc_fim = loc
txtFinal = "".join([conteudo, texto, txt2])
print(loc_fim)

distancia, duracao = calcular_distancia_tempo(loc_Inicial, loc_fim)
vm = distancia/duracao

if distancia and duracao:
    print(f"Distância: {distancia}")
    print(f"Duração: {duracao}")
    print(f"Velocidade Média = {vm} KM/H")
else:
    print("Não foi possível calcular a distância e a duração.")

with open("exemplo.txt", "w") as arquivo:
    arquivo.write(txtFinal)
numero_string = format(vm, '.2f')
gerar_pdf("teste.pdf",txtFinal, numero_string) 




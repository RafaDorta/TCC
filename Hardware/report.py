from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time
from pymongo import MongoClient
from googlemaps import exceptions
import googlemaps


client = MongoClient('mongodb://localhost:27017/')
db = client['meu_banco']
users_graficos = db['graficos']


_GEOLOCATION_BASE_URL = "https://www.googleapis.com"
client = googlemaps.Client(key='AIzaSyBu2IkPNjkUMYtoWSEtQWF6NbPqSE7_hwM')

def get_address_from_coordinates(latitude, longitude):
    try:
        result = client.reverse_geocode((latitude, longitude))
        if result:
            return result[0]['formatted_address']
        else:
            return "Endereço não encontrado."
    except exceptions.ApiError as e:
        print(f"Erro ao chamar a API: {e}")
        return None

    

def calculateSpeed(origem, destino):
    now = datetime.now()
    directions_result = client.directions(origem, destino, mode="driving", departure_time=now)

    if directions_result:
        # Extrair distância e duração da resposta
        distancia_em_metros = directions_result[0]['legs'][0]['distance']['value']
        print(distancia_em_metros)
        avg_Speed = (distancia_em_metros/10) * 3.6
        return avg_Speed
    else:
        return None


user = "Admin"
initial_Lat,initial_Lng = "-23.702052","-46.544032"
date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
initial_LocAddress = get_address_from_coordinates(initial_Lat, initial_Lng)
time.sleep(10)
final_Lat,final_Lng = "-23.702750", "-46.542242"
final_LocAddress = get_address_from_coordinates(final_Lat, final_Lng)
speed = calculateSpeed(initial_LocAddress,final_LocAddress)

data_to_insert = {
    'username': user,
    'date': date,
    'address': initial_LocAddress,
    'speed': speed
}

# Inserir dados na coleção
users_graficos.insert_one(data_to_insert)


print("Dados inseridos com sucesso:", data_to_insert)

 




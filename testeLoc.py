
from googlemaps import exceptions
import googlemaps
from geopy.geocoders import Nominatim
import time
from datetime import datetime


_GEOLOCATION_BASE_URL = "https://www.googleapis.com"
client = googlemaps.Client(key='AIzaSyD-ddpqUaS0PfKqJ45DRb49wMVtRyT-idg')

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

def get_address_from_coordinates(latitude, longitude):
    result = client.reverse_geocode((latitude, longitude))
    if result:
        return result[0]['formatted_address']
    else:
        return "Endereço não encontrado."


def _geolocation_extract(response):
    """
    Mimics the exception handling logic in ``client._get_body``, but
    for geolocation which uses a different response format.
    """
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




result = geolocate(client, wifi_access_points=[{'macAddress': '56-7F-8C-9A-D0-20'}])
latitude = result['location']['lat']
longitude = result['location']['lng']
print(latitude, longitude)
adress1 = get_address_from_coordinates(latitude, longitude)
print(adress1)
time.sleep(10)
result = geolocate(client, wifi_access_points=[{'macAddress': '56-7F-8C-9A-D0-20'}])
latitude = result['location']['lat']
longitude = result['location']['lng']
print(latitude, longitude)
adress2 = get_address_from_coordinates(latitude, longitude)
print(adress2)

distancia, duracao = calcular_distancia_tempo(adress1, adress2)

if distancia and duracao:
    print(f"Distância: {distancia}")
    print(f"Duração: {duracao}")
    print(f"Velocidade Média = {distancia/duracao} KM/H")
else:
    print("Não foi possível calcular a distância e a duração.")
import requests


class CityDoesNotExist(Exception):
    """Для ситуации, когда название скомого города не совпадает с тем, что возвращает api"""
    pass


class SetDoesNotExist(Exception):
    """Для ситуации, когда метод .filter возвращает пустой набор"""
    pass


def deg_to_compass(num):
    """
    :param num: угол направления ветра
    :return: аббревиатуру направления ветра
    """
    val = int((float(num) / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]


def save_to_database(response):
    from weather_forecast.models import City, Forecast, Weather, WeatherIcon, WeatherGroup

    city_inf = response['city']

    city = City.objects.get_or_create(name=city_inf['name'], defaults={'city_id': city_inf['id'],
                                                                       'country': city_inf['country'],
                                                                       'coord_lat': city_inf['coord']['lat'],
                                                                       'coord_lon': city_inf['coord']['lon']})[0]

    for forecast in response['list']:

        weather_inf = forecast['weather'][0]
        group = WeatherGroup.objects.get_or_create(name=weather_inf['main'])[0]
        icon = WeatherIcon.objects.get_or_create(name=weather_inf['icon'])[0]
        weather = Weather.objects.get_or_create(weather_id=weather_inf['id'], defaults={'group': group,
                                                                                        'description': weather_inf['description'],
                                                                                        'icon': icon})[0]

        forecast['main'].pop('temp_kf')
        Forecast.objects.get_or_create(dt_txt=forecast['dt_txt'], city=city, defaults={**forecast['main'],
                                                                                       'weather': weather,
                                                                                       'clouds': forecast['clouds']['all'],
                                                                                       'wind_speed': forecast['wind']['speed'],
                                                                                       'wind_dir': deg_to_compass(forecast['wind']['deg']),
                                                                                       'snow': forecast.get('snow', {'3h': 0})['3h'],
                                                                                       'rain': forecast.get('rain', {'3h': 0}).get('3h', 0)})

        """forecast.get('snow', {'3h': 0})['3h'] - работает, а forecast.get('rain', {'3h': 0})['3h'] выдаёт ошибку
        ключа. Для обхода магической аномалии используется форма forecast.get('rain', {'3h': 0}).get('3h', 0)"""


def request_to_api(city_name):
    response = requests.get(
        'http://api.openweathermap.org/data/2.5/forecast?q={0}&units=metric&APPID=457a76f25e6c0e0c0ac1ff4b1f6f0658'.format(
            city_name))
    response = response.json()
    if response['city']['name'] != city_name:
        raise CityDoesNotExist
    save_to_database(response)

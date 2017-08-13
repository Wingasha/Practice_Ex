from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import requests
import datetime

# Create your models here.


class SetDoesNotExist(Exception):
    """Для ситуации, когда метод .filter возвращает пустой набор"""
    pass


"""
Не знаю какие поля нужны для отображения в шаблоне, так что сохраню в бд побольше.
"""

class WeatherGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return '%s' % self.name


class WeatherDescription(models.Model):
    description = models.CharField(max_length=100)

    def __str__(self):
        return '%s' % self.description


class WeatherIcon(models.Model):
    name = models.CharField(max_length=10)
    # icon = models.ImageField(upload_to='icons')

    def __str__(self):
        return '%s' % self.name


class Weather(models.Model):
    weather_id = models.IntegerField()
    group = models.ForeignKey(WeatherGroup)
    description = models.ForeignKey(WeatherDescription)
    icon = models.ForeignKey(WeatherIcon)

    def __str__(self):
        return '%d' % self.weather_id


class City(models.Model):
    city_id = models.IntegerField()
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    coord_lat = models.FloatField()
    coord_lon = models.FloatField()

    def __str__(self):
        return '%s %s' % self.name, self.country


"""
Проблема с временными поясами. Возможно необходимо хранить время в формате UTC, а потом конвертировать и т.д.
"""
class Forecast(models.Model):
    temp = models.FloatField()
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    pressure = models.FloatField()
    sea_level = models.FloatField()
    grnd_level = models.FloatField()
    humidity = models.IntegerField()

    clouds = models.IntegerField()
    wind_speed = models.FloatField()
    wind_dir = models.CharField(max_length=10)
    snow = models.FloatField()
    rain = models.FloatField()
    dt_txt = models.DateTimeField()

    weather = models.ForeignKey(Weather)
    city = models.ForeignKey(City)

    def __str__(self):
        return '{} {} {}'.format(self.city, self.weather, self.dt_txt)

    @staticmethod
    def get_forecasts(city_name, search_date, whence=''):
        """
        Метод получения прогноза на ближайшие 5 дней. В случае отсутвия информации по городу
        :param city_name: название города
        :param search_date:
        :param whence: строка, которая указывает откуда берётся ответ - api или database. При вызове не указывать
        :return: словарь, который содержит информацию о том откуда получен результат 'from', список объектов QuerySet в
        'forecast_list', объяснение в 'error', если поиск не дал результатов
        """
        date = search_date
        forecast_list = []
        try:
            city = City.objects.get(name=city_name)
            for i in range(0, 5):
                """В цикле постепенно добвляем в список forecast_set 5 объектов  QuerySet по каждому дню. Если хоть 1
                будет пуск, то возбуждаем исключение SetDoesNotExist. Если добавление прошло успешно то возвращаем
                 результат в виде словаря. И да, если обращение к api не было, о чём свидетельствует внутренняя пустота
                 и бренность переменной whence, то делаем присвоение  whence = 'Database'"""
                forecast_set = city.forecast_set.filter(dt_txt__year=date.year, dt_txt__month=date.month,
                                                              dt_txt__day=date.day)
                if forecast_set.exists():
                    forecast_list.append(forecast_set)
                    date += datetime.timedelta(days=1)
                else:
                    raise SetDoesNotExist
            if whence == '':
                whence = 'Database'
            return {'from': whence, 'forecast_list': forecast_list, 'city': city}
        except SetDoesNotExist:
            if search_date != datetime.datetime.today().date():
                """
                Если в базе не нашлось прогноза на 5 дней за выбраную дату в прошлом, то и  api такого не выдаст.
                Можно даже будет проверить, чтоб на входе не получать дату 'из будущего'.
                """
                return {'from': '', 'forecast_list': [], 'error': "It's impossible to get a forecast for 5 days for a specified date"}
            else:
                """Если же запрос был на текущую дату, то делаем запрос к api и соответственно делаем присвоение
                whence = 'API', после сохраняем результат вызова в модель и рекурсивно вызываем этот же метод"""
                whence = 'API'
                response = requests.get(
                    'http://api.openweathermap.org/data/2.5/forecast?q={0}&units=metric&APPID=457a76f25e6c0e0c0ac1ff4b1f6f0658'.format(
                        city_name))
                save_to_model(response)
                return Forecast.get_forecasts(city_name, search_date, whence)

        except ObjectDoesNotExist:
            """Срабатывает в случае отсутствия информации по указаному городу в бд"""
            whence = 'API'
            response = requests.get(
                'http://api.openweathermap.org/data/2.5/forecast?q={0}&units=metric&APPID=457a76f25e6c0e0c0ac1ff4b1f6f0658'.format(city_name))
            test = response.json()
            if test['city']['name'] != city_name:
                """Нужно проверять название города, которое вводит пользователь и то, что выдаёт api Ведь даже написав
                набор букв, api всё равно выдаст какой-то город. Планировалось возвращать пустой результат с
                соотвественным сообщением об ошибке, но посколько api ищет приблизительный результат и дабы не войти в
                бесконечную рекурсию название говода для поиска перезаписываем"""
                city_name = test['city']['name']
            save_to_model(response)
            return Forecast.get_forecasts(city_name, search_date, whence)


def save_to_model(response: 'requests object'):
    response = response.json()
    city_inf = response['city']

    city = get_record(City, {'name': city_inf['name']}, name=city_inf['name'], city_id=city_inf['id'],
                      country=city_inf['country'], coord_lat=city_inf['coord']['lat'], coord_lon=city_inf['coord']['lon'])

    for forecast in response['list']:

        weather_inf = forecast['weather'][0]
        group = get_record(WeatherGroup, {'name': weather_inf['main']}, name=weather_inf['main'])
        description = get_record(WeatherDescription, {'description': weather_inf['description']},
                                 description=weather_inf['description'])
        icon = get_record(WeatherIcon, {'name': weather_inf['icon']}, name=weather_inf['icon'])
        weather = get_record(Weather, {'weather_id': weather_inf['id'], 'group': group,
                                       'description': description, 'icon': icon},
                             weather_id=weather_inf['id'], group=group, description=description, icon=icon)

        date = datetime.datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S')
        forecast['main'].pop('temp_kf')
        get_record(Forecast, {'dt_txt__year': date.year, 'dt_txt__month': date.month,
                                 'dt_txt__day': date.day, 'dt_txt__hour': date.hour, 'city': city},
                   **forecast['main'], weather=weather, clouds=forecast['clouds']['all'],
                   wind_speed=forecast['wind']['speed'], wind_dir=deg_to_compass(forecast['wind']['deg']),
                   snow=forecast.get('snow', {'3h': 0})['3h'],
                   rain=forecast.get('rain', {'3h': 0}).get('3h', 0),
                   dt_txt=forecast['dt_txt'], city=city)
        """forecast.get('snow', {'3h': 0})['3h'] - работает, а forecast.get('rain', {'3h': 0})['3h'] выдаёт ошибку
        ключа. Для обхода магической аномалии используется форма forecast.get('rain', {'3h': 0}).get('3h', 0)"""


def get_record(model: models.Model, param, **kwargs):
    """
    Метод для получения записи модели. Если запись с нужными параметрами есть, то возращаем её, а если такой в бд нет,
    то с помощью переданных именованых аргументов kwargs создаём нужную запись
    :param model: модель, запись которой нужно получить
    :param param: словарь с именоваными аргументами для поиска записи в бд
    :param kwargs: именованные аргументы для создания записи в бд
    :return: record - объект модели
    """
    record = None
    try:
        record = model.objects.get(**param)
    except ObjectDoesNotExist:
        record = model.objects.create(**kwargs)
    finally:
        return record


def deg_to_compass(num):
    """
    :param num: угол направления ветра
    :return: аббревиатуру направления ветра
    """
    val = int((float(num) / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]



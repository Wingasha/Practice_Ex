from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import datetime

from weather_forecast.utils import request_to_api, SetDoesNotExist, CityDoesNotExist


class WeatherGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return '%s' % self.name


class WeatherIcon(models.Model):
    name = models.CharField(max_length=10)
    # icon = models.ImageField(upload_to='icons')

    def __str__(self):
        return '%s' % self.name


class Weather(models.Model):
    weather_id = models.IntegerField()
    group = models.ForeignKey(WeatherGroup)
    description = models.CharField(max_length=100)
    icon = models.ForeignKey(WeatherIcon)

    def __str__(self):
        return '%d %s' % self.weather_id, self.description


class City(models.Model):
    city_id = models.IntegerField()
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    coord_lat = models.FloatField()
    coord_lon = models.FloatField()

    def __str__(self):
        return '%s %s' % self.name, self.country


class ForecastManager(models.Manager):
    def get_forecast(self, city_name, search_date, whence='Database'):
        next_days = [search_date + datetime.timedelta(days=i) for i in range(0, 5)]
        forecast_list = []
        try:
            city = City.objects.get(name=city_name)
        except ObjectDoesNotExist:
            try:
                request_to_api(city_name)
                city = City.objects.get(name=city_name)
                whence = 'API'
            except CityDoesNotExist:
                return {'forecast_list': [],
                        'error': "The city with the specified name does not exist"}

        try:
            for i in range(0, 5):
                """В цикле постепенно добвляем в список forecast_set 5 объектов  QuerySet по каждому дню. Если хоть 1
                будет пуск, то возбуждаем исключение SetDoesNotExist. Если добавление прошло успешно то возвращаем
                 результат в виде словаря. И да, если обращение к api не было, о чём свидетельствует внутренняя пустота
                 и бренность переменной whence, то делаем присвоение  whence = 'Database'"""
                forecast_per_day = city.forecast_set.filter(dt_txt__year=next_days[i].year,
                                                            dt_txt__month=next_days[i].month,
                                                            dt_txt__day=next_days[i].day)
                if forecast_per_day.exists():
                    forecast_list.append(forecast_per_day)
                else:
                    raise SetDoesNotExist
            return {'from': whence, 'forecast_list': forecast_list, 'city': city}
        except SetDoesNotExist:
            if search_date != datetime.datetime.today().date():
                """
                Если в базе не нашлось прогноза на 5 дней за выбраную дату в прошлом, то и  api такого не выдаст.
                Можно даже будет проверить, чтоб на входе не получать дату 'из будущего'.
                """
                return {'forecast_list': [],
                        'error': "It's impossible to get a forecast for 5 days for a specified date"}
            else:
                """Если же запрос был на текущую дату, то делаем запрос к api и соответственно делаем присвоение
                whence = 'API', после сохраняем результат вызова в модель и рекурсивно вызываем этот же метод"""
                whence = 'API'
                request_to_api(city_name)
                # рекурсия не торт, нужно изменить
                return self.get_forecast(city_name, search_date, whence)


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

    next_five_days = ForecastManager()
    objects = models.Manager()

    def __str__(self):
        return '%s %s %s' % self.city, self.weather, self.dt_txt

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
    def get_forecast_list(self, city: City, search_date: datetime):
        """
        Возвращает спико спикок forecast_list, который содержит объекты  QuerySet за каждый день.
        :param city: City
        :param search_date: datetime
        :return: forecast_list: []
        """
        forecast_list = []
        """
        В цикле постепенно добвляет в список forecast_list объекты  QuerySet по каждому дню. Если хоть 1 будет пуск,
        то возбуждается исключение SetDoesNotExist. Если добавление прошло успешно то возвращается forecast_list.
        """
        for date in (search_date + datetime.timedelta(days=i) for i in range(0, 5)):
            forecast_per_day = city.forecast_set.filter(dt_txt__year=date.year,
                                                        dt_txt__month=date.month,
                                                        dt_txt__day=date.day)
            if forecast_per_day.exists():
                forecast_list.append(forecast_per_day)
            else:
                raise SetDoesNotExist

        return forecast_list

    def get_context(self, city_name, search_date):
        """
        Возвращает context, содержащий список прогнозов и откуда он получен - база данных или api, а также сообщение об
        ошибке, если она была.
        :param city_name: str
        :param search_date: datetime
        :return: context: dict
        """
        context = {'from': 'Database', 'forecast_list': []}

        try:
            city = City.objects.get(name=city_name)
        except ObjectDoesNotExist:
            try:
                request_to_api(city_name)
                context['from'] = 'API'
                city = City.objects.get(name=city_name)
            except CityDoesNotExist as error:
                context['error'] = "The city with the specified name does not exist. Maybe you meant the '%s'" % error
                return context
        context['city'] = city

        try:
            context['forecast_list'] = self.get_forecast_list(city, search_date)
            return context
        except SetDoesNotExist:
            if search_date != datetime.datetime.today().date():
                """
                Если в базе не нашлось прогноза на 5 дней за выбраную дату в прошлом, то и  api такого не выдаст.
                Можно даже будет проверить, чтоб на входе не получать дату 'из будущего'.
                """
                context['error'] = "It's impossible to get a forecast for 5 days for a specified date"
                return context
            else:
                """Если же запрос был на текущую дату, то делаем запрос к api"""
                request_to_api(city_name)
                context['from'] = 'API'
                context['forecast_list'] = self.get_forecast_list(city, search_date)
                return context


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

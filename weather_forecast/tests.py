from django.test import TestCase
from django.core.urlresolvers import reverse

import datetime

from weather_forecast import models, utils


# Create your tests here.
class TestModel(TestCase):

    def setUp(self):
        utils.request_to_api('London')

    def test_get_forecast_from_api_with_current_date(self):
        """Проверка на получение прогноза за текущую дату города, которого нет в бд"""
        city_name = 'Kiev'
        date = datetime.datetime.today().date()
        result = models.Forecast.next_five_days.get_context(city_name, date)
        self.assertEqual(result['from'], 'API')

    def test_get_forecast_from_database_with_current_date(self):
        """Проверка на получение прогноза за текущую дату города, который есть в бд"""
        city_name = 'London'
        date = datetime.datetime.today()
        result = models.Forecast.next_five_days.get_context(city_name, date)
        self.assertEqual(result['from'], 'Database')

    def test_get_frorecast_with_unexists_city(self):
        """Проверка поиска с несуществующем названием города"""
        city_name = 'Zaporozhye'
        date = datetime.datetime.today().date()
        result = models.Forecast.next_five_days.get_context(city_name, date)
        self.assertEqual(result['error'], "The city with the specified name does not exist. Maybe you meant the 'Zaporizhzhya'")

    def test_get_forecast_with_future_date(self):
        """Проверка поиска прогноза за датой в будущем (возможно перекинуть проверку на фронтэнд)"""
        city_name = 'London'
        date = datetime.datetime.today().date() + datetime.timedelta(days=10)
        result = models.Forecast.next_five_days.get_context(city_name, date)
        self.assertEqual(result['error'], "It's impossible to get a forecast for 5 days for a specified date")

    def test_get_forecast_with_past_date(self):
        """Проверка поиска прогноза за прошлой датой, при его отсутствии в бд"""
        city_name = 'London'
        date = datetime.datetime.today().date() - datetime.timedelta(days=10)
        result = models.Forecast.next_five_days.get_context(city_name, date)
        self.assertEqual(result['error'], "It's impossible to get a forecast for 5 days for a specified date")

    def test_forecasts_for_different_citys(self):
        """Проверка того, прогнозы ссылались на свой город. То есть, чтоб при записи прогнозов по новому городу,
        другие прогнозы не теряли ссылку на свой город"""
        first_city = 'Paris'
        second_city = 'Tokyo'
        date = datetime.datetime.today().date()
        first_result = models.Forecast.next_five_days.get_context(first_city, date)
        second_result = models.Forecast.next_five_days.get_context(second_city, date)
        for f_set, s_set in zip(first_result['forecast_list'], second_result['forecast_list']):
            for f_forecast, s_forecast in zip(f_set, s_set):
                self.assertEqual(first_city, f_forecast.city.name)
                self.assertEqual(second_city, s_forecast.city.name)


class TestView(TestCase):
    """Нужно дописать тесты"""

    def test_page_loading(self):
        """Проверка загрузки страницы"""
        response = self.client.get(reverse('weather_forecast:main_page'))
        self.assertEqual(response.status_code, 200)

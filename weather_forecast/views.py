from django.shortcuts import render
from .forms import SearchForm
from django.views import View
import datetime

from weather_forecast.models import Forecast, City


class ForecastPage(View):
    initial = {'city': '', 'date': ''}
    form_class = SearchForm
    template_name = 'weather_forecast/weather_forecast.html'
    default_city = 'Zaporizhzhya'

    def get(self, request, *args, **kwargs):
        """При первой загрузки страницы выводит дефолтный прогноз"""
        context = ForecastPage.get_default_forecast()
        form = self.form_class(initial=self.initial)
        context['form'] = form
        context['dates'] = ForecastPage.get_dates_for_view(datetime.datetime.today())
        return render(request, 'weather_forecast/weather_forecast.html', context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            context = Forecast.near_forecast.get_forecast(data['city'], data['date'])
            context['dates'] = ForecastPage.get_dates_for_view(data['date'])
        else:
            """В принципе, форма всегда будет валидна, поскольку дату вести можно только через календарь, а вот в поле
            названиея города можно ввести любой текст. Может стоит сделать только ввод букв для проверки валидности"""
            context = {'from': '', 'forecast_list': ForecastPage.get_default_forecast()['forecast_list'],
                       'error': "Form is not valid", 'dates': ForecastPage.get_dates_for_view(datetime.datetime.today())}
        if not context['forecast_list']:
            """Если форма валидна, но поиск недал результатов, то есть список прогнозов 'forecast_list' пуст,
            то записываем туду дефолтный прогноз, а также город. Метод get_default_forecast() не пойдёт, потому, что
            он затрёт сообщение об ошибки"""
            context['forecast_list'] = ForecastPage.get_default_forecast()['forecast_list']
            context['city'] = City.objects.get(name=ForecastPage.default_city)
            context['dates'] = ForecastPage.get_dates_for_view(datetime.datetime.today())
        context['form'] = form
        return render(request, self.template_name, context)

    @staticmethod
    def get_dates_for_view(date):
        """
        Формирует и возвращает список из пар название_дня_недели - число_месяц для подстановки в заголовки вкладок
        :param date: datetime object
        """
        dates = [date + datetime.timedelta(days=x) for x in range(0, 5)]
        return zip([x.strftime("%A") for x in dates], ['{:02d}.{:02d}'.format(x.day,x.month) for x in dates])

    @staticmethod
    def get_default_forecast():
        """
        Метод возвращает прогноз погоды, который отображается по умолчанию
        """
        return Forecast.near_forecast.get_forecast(ForecastPage.default_city, datetime.datetime.today().date())

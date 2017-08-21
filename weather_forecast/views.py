from django.shortcuts import render
from django.views import View

from datetime import datetime

from weather_forecast.models import Forecast
from weather_forecast.utils import get_dates_for_view
from weather_forecast.forms import SearchForm


class ForecastPage(View):
    initial = {'city': 'Zaporizhzhya', 'date': datetime.now()}
    form_class = SearchForm
    template_name = 'weather_forecast/next_days_forecast.html'

    def get(self, request):
        """При первой загрузки страницы выводит дефолтный прогноз"""
        context = Forecast.next_five_days.get_context(self.initial['city'], self.initial['date'])
        form = self.form_class(initial={'city': self.initial['city'],
                                        'date': self.initial['date'].strftime('%d/%m/%Y')})
        context['form'] = form
        context['dates'] = get_dates_for_view(datetime.today())
        return render(request, 'weather_forecast/next_days_forecast.html', context)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            context = Forecast.next_five_days.get_context(cleaned_data['city'], cleaned_data['date'])
            context['dates'] = get_dates_for_view(cleaned_data['date'])
        if not context['forecast_list']:
            """Если форма валидна, но поиск недал результатов, то есть список прогнозов 'forecast_list' пуст,
            то записываем туда дефолтный прогноз, а также город."""
            context.update(Forecast.next_five_days.get_context(self.initial['city'], self.initial['date']))
            context['dates'] = get_dates_for_view(datetime.today())
        context['form'] = form
        return render(request, self.template_name, context)

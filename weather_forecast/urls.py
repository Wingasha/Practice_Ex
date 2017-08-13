from django.conf.urls import url

from . import views

app_name = 'weather_forecast'
urlpatterns = [
    url(r'^$', views.ForecastPage.as_view(), name='main_page'),
]
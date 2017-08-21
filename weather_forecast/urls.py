from django.conf.urls import url

from weather_forecast import views

app_name = 'weather_forecast'
urlpatterns = [
    url(r'^$', views.ForecastPage.as_view(), name='main_page'),
]
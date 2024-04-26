from django.urls import path
from appoint import views
from website import views as webview


urlpatterns = [
    path('patientappo', views.patientappo, name="patientappointment"),
    path('login/', webview.loginn, name="login"),
]

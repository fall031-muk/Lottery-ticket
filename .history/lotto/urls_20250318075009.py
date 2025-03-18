from django.urls import path
from lotto.api.views import GetLottoNumber

urlpatterns = [
    path('numbers', GetLottoNumber.as_view(), name='get_lotto'), #127.0.0.1:8000/lottery/numbers
]
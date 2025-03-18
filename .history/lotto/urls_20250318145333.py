from django.urls import path
from lotto.api.views import GetLottoNumber, LottoMainView

urlpatterns = [
    path('', LottoMainView.as_view(), name='lotto_main'),  # 메인 페이지
    path('numbers', GetLottoNumber.as_view(), name='get_lotto'),  # API 엔드포인트
]
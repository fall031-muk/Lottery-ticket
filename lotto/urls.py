from django.urls import path
from lotto.api.views import GetLottoNumber, LottoMainView, GetLatestDrawNumber, GetDrawInfo
from lotto import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', LottoMainView.as_view(), name='lotto_main'),  # 메인 페이지
    path('numbers', GetLottoNumber.as_view(), name='get_lotto'),  # API 엔드포인트
    path('latest-draw', GetLatestDrawNumber.as_view(), name='get_latest_draw'),  # 최신 회차 API
    path('draw-info', GetDrawInfo.as_view(), name='get_draw_info'),  # 특정 회차 정보 API
    path('about/', views.about, name='about'),  # 사이트 소개 페이지
    path('privacy/', TemplateView.as_view(template_name='lotto/privacy.html'), name='privacy'),  # 개인정보 처리방침
    path('terms/', TemplateView.as_view(template_name='lotto/terms.html'), name='terms'),  # 이용약관
]
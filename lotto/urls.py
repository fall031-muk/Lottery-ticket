from django.urls import path
from lotto.api.views import GetLottoNumber, GetLatestDrawNumber, GetDrawInfo, GetNumberStatistics
from lotto import views
from django.views.generic import TemplateView, RedirectView

urlpatterns = [
    # 메인 페이지는 루트로 리다이렉트 (중복 콘텐츠 방지)
    path('', RedirectView.as_view(url='/', permanent=True), name='lotto_main'),
    path('numbers', GetLottoNumber.as_view(), name='get_lotto'),  # API 엔드포인트
    path('latest-draw', GetLatestDrawNumber.as_view(), name='get_latest_draw'),  # 최신 회차 API
    path('draw-info', GetDrawInfo.as_view(), name='get_draw_info'),  # 특정 회차 정보 API
    path('statistics', GetNumberStatistics.as_view(), name='get_statistics'),  # 번호 통계 API
    path('about/', views.about, name='about'),  # 사이트 소개 페이지
    path('privacy/', TemplateView.as_view(template_name='lotto/privacy.html'), name='privacy'),  # 개인정보 처리방침
    path('terms/', TemplateView.as_view(template_name='lotto/terms.html'), name='terms'),  # 이용약관
    # 랜딩 페이지
    path('history/', views.history, name='history'),
    path('stats/', views.stats_page, name='stats_page'),
    path('calculator/', views.calculator, name='calculator'),
    # 컨텐츠 준비 후 오픈
    # path('tips/', views.tips, name='tips'),
    # path('news/', views.news, name='news'),
]
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import datetime


class StaticViewSitemap(Sitemap):
    """정적 페이지들의 사이트맵"""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        # home만 사용하고 lotto_main 중복 제거
        return ['home', 'about', 'privacy', 'terms', 'history', 'stats_page', 'calculator']
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):
        return timezone.now()


# LottoSitemap 제거하여 중복 방지
# class LottoSitemap(Sitemap):
#     """로또 관련 페이지들의 사이트맵"""
#     priority = 1.0
#     changefreq = 'daily'
#     protocol = 'https'
#     
#     def items(self):
#         return ['lotto_main']
#     
#     def location(self, item):
#         return reverse(item)
#     
#     def lastmod(self, item):
#         return timezone.now()


# 사이트맵 딕셔너리 - LottoSitemap 제거
sitemaps = {
    'static': StaticViewSitemap,
} 
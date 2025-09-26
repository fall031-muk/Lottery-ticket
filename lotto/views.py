from django.shortcuts import render
from lotto.api.views import load_lotto_data

def about(request):
    """사이트 소개 및 문의 페이지"""
    return render(request, 'lotto/about.html')

def history(request):
    draws = load_lotto_data() or []
    context = {
        'draws': draws[:100]
    }
    return render(request, 'lotto/history.html', context)

def stats_page(request):
    return render(request, 'lotto/statistics.html')

def calculator(request):
    return render(request, 'lotto/calculator.html')

def tips(request):
    return render(request, 'lotto/tips.html')

def news(request):
    return render(request, 'lotto/news.html')
from django.shortcuts import render

def about(request):
    """사이트 소개 및 문의 페이지"""
    return render(request, 'lotto/about.html') 
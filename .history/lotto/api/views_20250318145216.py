import random
import requests

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render


class LottoMainView(APIView):
    """
    로또 메인 페이지를 렌더링하는 뷰
    """
    def get(self, request):
        return render(request, 'lotto/index.html')


class GetLottoNumber(APIView):
    """
    로또 번호를 생성하는 API 뷰
    """
    def get(self, request):
        # 직전 회차 번호 제외 여부
        exclude_last = request.GET.get('exclude_last', 'false').lower() == 'true'
        
        # 직전 회차 번호 가져오기
        last_draw_numbers = []
        if exclude_last:
            # 현재 최신 회차를 가정 (실제로는 동적으로 계산해야 함)
            current_draw = 1065
            try:
                lotto_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={current_draw}"
                lotto_response = requests.get(lotto_url)
                data = lotto_response.json()
                
                if data.get('returnValue') == 'success':
                    last_draw_numbers = [
                        data.get('drwtNo1'), data.get('drwtNo2'), data.get('drwtNo3'),
                        data.get('drwtNo4'), data.get('drwtNo5'), data.get('drwtNo6')
                    ]
            except Exception as e:
                print(f"API 호출 오류: {e}")
        
        # 사용 가능한 숫자 배열 생성
        available_numbers = []
        for i in range(1, 46):
            if exclude_last and i in last_draw_numbers:
                continue
            available_numbers.append(i)
        
        # 무작위로 6개 번호 선택
        lotto_number = random.sample(available_numbers, 6)
        lotto_number.sort()
        
        return Response(lotto_number, status=status.HTTP_200_OK)

import random
import requests
import datetime
from dateutil.relativedelta import relativedelta

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


class GetLatestDrawNumber(APIView):
    """
    최신 로또 회차 번호를 제공하는 API 뷰
    """
    def get(self, request):
        latest_draw = get_latest_draw_number()
        return Response({'latest_draw': latest_draw}, status=status.HTTP_200_OK)


def get_latest_draw_number():
    """
    현재 최신 로또 회차 번호를 가져오는 함수
    
    방법 1: 기준 날짜부터 주 수 계산
    로또 1회차 날짜: 2002년 12월 7일
    매주 토요일마다 1회차씩 증가
    """
    # 1. 날짜 기반 계산 (정확성 향상을 위해 보정값 추가)
    first_draw_date = datetime.date(2002, 12, 7)  # 로또 1회차 날짜
    today = datetime.date.today()
    
    # 두 날짜 사이의 주 수 계산 
    weeks_passed = ((today - first_draw_date).days) // 7
    estimated_draw = weeks_passed + 1
    
    # 추가 보정: 토요일 이전에 조회하는 경우를 고려
    if today.weekday() < 5:  # 월(0)~금(4)에 조회하는 경우 최신 회차는 지난 주 토요일 기준
        estimated_draw -= 1
    
    # 2. API 시도를 통한 검증 (추정 회차와 인접한 회차 확인)
    # 더 넓은 범위로 검색하여 누락 방지
    for offset in [0, 1, -1, 2, -2, 3, -3]:  # 가장 가능성 높은 순서대로 확인
        draw_no = estimated_draw + offset
        if draw_no <= 0:  # 음수 회차는 건너뜀
            continue
            
        try:
            lotto_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            response = requests.get(lotto_url)
            data = response.json()
            
            if data.get('returnValue') == 'success':
                # 가장 최신 회차 찾기
                max_valid_draw = draw_no
                
                # 더 높은 회차가 있는지 조금 더 확인
                for next_draw in range(draw_no + 1, draw_no + 5):
                    try:
                        next_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={next_draw}"
                        next_response = requests.get(next_url)
                        next_data = next_response.json()
                        
                        if next_data.get('returnValue') == 'success':
                            max_valid_draw = next_draw
                        else:
                            break  # 실패하면 더 이상 찾지 않음
                    except Exception:
                        break
                        
                return max_valid_draw
        except Exception:
            continue
    
    # 3. 모든 방법 실패 시 추정 회차 반환
    return estimated_draw


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
            # 현재 최신 회차를 동적으로 가져옴
            current_draw = get_latest_draw_number()
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


class GetDrawInfo(APIView):
    """
    특정 회차의 로또 당첨 정보를 제공하는 API 뷰
    CORS 문제를 해결하기 위한 프록시 역할
    """
    def get(self, request):
        draw_no = request.GET.get('draw_no')
        if not draw_no:
            return Response({"error": "회차 번호가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lotto_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            response = requests.get(lotto_url)
            data = response.json()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"당첨 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

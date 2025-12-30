import random
import requests
import datetime
import json
import os
from dateutil.relativedelta import relativedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.conf import settings


def load_lotto_data():
    """JSON 파일에서 로또 데이터를 로드합니다."""
    json_file_path = os.path.join(settings.BASE_DIR, 'lotto_num.json')
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_recent_draws(count=5):
    """최근 N회차의 당첨번호를 가져옵니다."""
    data = load_lotto_data()
    return data[:count] if data else []

def get_number_statistics(count=10):
    """최근 N회차의 번호 통계를 분석합니다."""
    data = load_lotto_data()
    recent_data = data[:count] if data else []
    
    if not recent_data:
        return None
    
    # 번호 빈도 계산
    number_count = {}
    bonus_count = {}
    
    for entry in recent_data:
        # 일반 번호
        for num in entry['number']:
            number_count[num] = number_count.get(num, 0) + 1
        
        # 보너스 번호
        bonus = entry['bonus']
        bonus_count[bonus] = bonus_count.get(bonus, 0) + 1
    
    # 가장 많이 나온 번호들
    sorted_numbers = sorted(number_count.items(), key=lambda x: x[1], reverse=True)
    sorted_bonus = sorted(bonus_count.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'number_frequency': sorted_numbers,
        'bonus_frequency': sorted_bonus,
        'total_rounds': len(recent_data)
    }


def get_frequent_numbers(count=50, top=10):
    """최근 N회차에서 자주 나온 번호들을 반환합니다."""
    data = load_lotto_data()
    recent_data = data[:count] if data else []
    
    if not recent_data:
        return []
    
    number_count = {}
    for entry in recent_data:
        for num in entry['number']:
            number_count[num] = number_count.get(num, 0) + 1
    
    # 빈도순으로 정렬하여 상위 번호들 반환
    sorted_numbers = sorted(number_count.items(), key=lambda x: x[1], reverse=True)
    return [num for num, count in sorted_numbers[:top]]


def get_rare_numbers(count=50):
    """최근 N회차에서 나오지 않은 번호들을 반환합니다."""
    data = load_lotto_data()
    recent_data = data[:count] if data else []
    
    if not recent_data:
        return list(range(1, 46))
    
    # 최근 N회차에 나온 모든 번호 수집
    appeared_numbers = set()
    for entry in recent_data:
        appeared_numbers.update(entry['number'])
        appeared_numbers.add(entry['bonus'])
    
    # 전체 번호(1-45)에서 나온 번호들을 제외
    all_numbers = set(range(1, 46))
    rare_numbers = list(all_numbers - appeared_numbers)
    
    return rare_numbers


def get_overdue_numbers(min_rounds=10):
    """가장 오랫동안 나오지 않은 번호들을 반환합니다."""
    data = load_lotto_data()
    
    if not data:
        return []
    
    # 각 번호가 마지막으로 나온 회차 추적
    last_appearance = {}
    overdue_numbers = []
    
    for idx, entry in enumerate(data):
        current_round = entry['round']
        
        # 해당 회차에 나온 모든 번호 (일반 번호 + 보너스 번호)
        appeared_numbers = entry['number'] + [entry['bonus']]
        
        for num in appeared_numbers:
            last_appearance[num] = idx  # 인덱스로 위치 저장
    
    # min_rounds 이상 나오지 않은 번호들 찾기
    for num in range(1, 46):
        if num not in last_appearance or last_appearance[num] >= min_rounds:
            overdue_numbers.append(num)
    
    return overdue_numbers


def generate_smart_numbers(exclude_numbers=None):
    """통계 기반 스마트 번호 생성"""
    if exclude_numbers is None:
        exclude_numbers = []
    
    # 사용 가능한 번호 풀
    available_numbers = [i for i in range(1, 46) if i not in exclude_numbers]
    
    if len(available_numbers) < 6:
        # 제외할 번호가 너무 많으면 일반 랜덤 생성
        return random.sample(available_numbers, min(6, len(available_numbers)))
    
    selected_numbers = []
    
    # 1. 최근 50회차에서 자주 나온 번호 중 1-2개 선택
    frequent_numbers = [n for n in get_frequent_numbers(50, 10) if n not in exclude_numbers]
    if frequent_numbers:
        frequent_count = min(2, len(frequent_numbers))
        selected_numbers.extend(random.sample(frequent_numbers, frequent_count))
    
    # 2. 최근 안 나온 번호 중 1-2개 선택
    rare_numbers = [n for n in get_rare_numbers(20) if n not in exclude_numbers and n not in selected_numbers]
    if rare_numbers:
        rare_count = min(2, len(rare_numbers))
        selected_numbers.extend(random.sample(rare_numbers, rare_count))
    
    # 3. 오랫동안 안 나온 번호 중 1개 선택
    overdue_numbers = [n for n in get_overdue_numbers(15) if n not in exclude_numbers and n not in selected_numbers]
    if overdue_numbers and len(selected_numbers) < 5:
        selected_numbers.append(random.choice(overdue_numbers))
    
    # 4. 나머지는 일반 풀에서 랜덤 선택
    remaining_pool = [n for n in available_numbers if n not in selected_numbers]
    remaining_needed = 6 - len(selected_numbers)
    
    if remaining_needed > 0 and remaining_pool:
        selected_numbers.extend(random.sample(remaining_pool, min(remaining_needed, len(remaining_pool))))
    
    # 6개가 안 되면 부족한 만큼 일반 풀에서 채움
    while len(selected_numbers) < 6 and remaining_pool:
        remaining_pool = [n for n in available_numbers if n not in selected_numbers]
        if remaining_pool:
            selected_numbers.append(random.choice(remaining_pool))
    
    # 정렬하여 반환
    return sorted(selected_numbers[:6])

class LottoMainView(APIView):
    """
    로또 메인 페이지를 렌더링하는 뷰
    """
    def get(self, request):
        # JSON 파일에서 최신 당첨번호 가져오기
        recent_draws = get_recent_draws(5)
        latest_draw = recent_draws[0] if recent_draws else None
        statistics = get_number_statistics(10)
        
        context = {
            'recent_draws': recent_draws,
            'latest_draw': latest_draw,
            'statistics': statistics,
        }
        
        return render(request, 'lotto/index.html', context)


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
    
    # PythonAnywhere 환경에서 프록시 오류 처리
    try:
        # 2. API 시도를 통한 검증 (추정 회차와 인접한 회차 확인)
        for offset in [0, 1, -1, 2, -2, 3, -3]:  # 가장 가능성 높은 순서대로 확인
            draw_no = estimated_draw + offset
            if draw_no <= 0:  # 음수 회차는 건너뜀
                continue
                
            try:
                lotto_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
                response = requests.get(lotto_url, timeout=3)  # 타임아웃 설정
                data = response.json()
                
                if data.get('returnValue') == 'success':
                    # 가장 최신 회차 찾기
                    max_valid_draw = draw_no
                    
                    # 더 높은 회차가 있는지 조금 더 확인
                    for next_draw in range(draw_no + 1, draw_no + 5):
                        try:
                            next_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={next_draw}"
                            next_response = requests.get(next_url, timeout=3)
                            next_data = next_response.json()
                            
                            if next_data.get('returnValue') == 'success':
                                max_valid_draw = next_draw
                            else:
                                break  # 실패하면 더 이상 찾지 않음
                        except Exception:
                            break
                            
                    return max_valid_draw
            except Exception as e:
                print(f"API 호출 오류: {e}")
                continue
    except Exception as e:
        print(f"전체 API 검증 실패: {e}")
    
    # 3. 모든 방법 실패 시 추정 회차 반환
    return estimated_draw


class GetLottoNumber(APIView):
    """
    로또 번호를 생성하는 API 뷰
    """
    def get(self, request):
        exclude_numbers = request.GET.get('exclude_numbers', '')
        generation_mode = request.GET.get('mode', 'random')  # 'random' 또는 'smart'
        count = request.GET.get('count', '1')  # 생성할 번호 세트 개수 (기본값: 1)

        # 생성 개수 처리
        try:
            count = int(count)
            # 1, 3, 5, 10만 허용
            if count not in [1, 3, 5, 10]:
                count = 1  # 기본값
        except ValueError:
            count = 1

        # 제외할 번호 처리
        exclude_numbers_list = []
        if exclude_numbers:
            try:
                exclude_numbers_list = [int(num) for num in exclude_numbers.split(',') if num.strip()]
                # 유효한 번호만 필터링 (1-45 사이)
                exclude_numbers_list = [num for num in exclude_numbers_list if 1 <= num <= 45]
            except ValueError:
                pass

        # 중복 제거
        exclude_numbers_list = list(set(exclude_numbers_list))

        # 사용 가능한 번호 목록 생성
        available_numbers = [i for i in range(1, 46) if i not in exclude_numbers_list]

        # 번호 추첨
        if len(available_numbers) < 6:
            return Response({"error": "제외할 번호가 너무 많습니다."}, status=400)

        # 여러 개의 번호 세트 생성
        all_number_sets = []

        for i in range(count):
            # 생성 모드에 따라 다른 로직 적용
            if generation_mode == 'smart':
                try:
                    selected_numbers = generate_smart_numbers(exclude_numbers_list)
                    if len(selected_numbers) < 6:
                        # 스마트 생성 실패 시 랜덤으로 폴백
                        selected_numbers = random.sample(available_numbers, 6)
                        selected_numbers.sort()
                    all_number_sets.append(selected_numbers)
                except Exception as e:
                    # 스마트 생성 실패 시 랜덤으로 폴백
                    selected_numbers = random.sample(available_numbers, 6)
                    selected_numbers.sort()
                    all_number_sets.append(selected_numbers)
            else:
                # 기본 랜덤 생성
                selected_numbers = random.sample(available_numbers, 6)
                selected_numbers.sort()
                all_number_sets.append(selected_numbers)

        # 응답 구성
        info_message = ""
        if generation_mode == 'smart':
            info_message = f"통계 기반으로 생성된 {count}개의 번호입니다"
        else:
            info_message = f"완전 랜덤으로 생성된 {count}개의 번호입니다"

        return Response({
            "number_sets": all_number_sets,
            "count": count,
            "mode": generation_mode,
            "info": info_message
        })


class GetNumberStatistics(APIView):
    """
    지정된 회차의 번호 통계를 제공하는 API 뷰
    """
    def get(self, request):
        rounds = request.GET.get('rounds', '10')
        
        try:
            rounds = int(rounds)
            if rounds not in [10, 30, 50]:
                rounds = 10  # 기본값
        except ValueError:
            rounds = 10
        
        statistics = get_number_statistics(rounds)
        
        if statistics:
            return Response(statistics, status=status.HTTP_200_OK)
        else:
            return Response({"error": "통계 데이터를 불러올 수 없습니다."}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            # 실제 API 호출 시도
            lotto_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            response = requests.get(lotto_url, timeout=3)
            data = response.json()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            error_msg = str(e)
            print(f"당첨 정보 가져오기 오류: {error_msg}")
            
            # # PythonAnywhere 프록시 오류인 경우 대체 데이터 제공
            # if "ProxyError" in error_msg or "Max retries exceeded" in error_msg:
            #     # 대체 데이터: 회차에 따라 고정된 번호 생성
            #     # 실제로는 완전히 랜덤하지 않지만, 회차별로 다른 결과 제공
            #     seed_value = int(draw_no) % 10000  # 회차를 시드값으로 사용
            #     random.seed(seed_value)
                
            #     # 회차별로 일관된 번호 생성
            #     numbers = sorted(random.sample(range(1, 46), 7))
                
            #     # 동행복권 API 형식과 유사하게 응답 구성
            #     fallback_data = {
            #         "returnValue": "success",
            #         "drwNoDate": f"2023-{((int(draw_no) % 12) + 1):02d}-{((int(draw_no) % 28) + 1):02d}",  # 임의의 날짜
            #         "drwNo": int(draw_no),
            #         "drwtNo1": numbers[0],
            #         "drwtNo2": numbers[1],
            #         "drwtNo3": numbers[2],
            #         "drwtNo4": numbers[3],
            #         "drwtNo5": numbers[4],
            #         "drwtNo6": numbers[5],
            #         "bnusNo": numbers[6],
            #         "firstWinamnt": 1500000000,  # 임의의 상금
            #         "firstPrzwnerCo": 8,  # 임의의 당첨자 수
            #         "firstAccumamnt": 12000000000,  # 임의의 누적 상금
            #         "totSellamnt": 85000000000  # 임의의 총 판매금액
            #     }
            #     return Response(fallback_data, status=status.HTTP_200_OK)
            
            return Response({"error": f"당첨 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

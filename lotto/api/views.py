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


def load_pension_data():
    """JSON 파일에서 연금복권 데이터를 로드합니다."""
    json_file_path = os.path.join(settings.BASE_DIR, 'pension_num.json')
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_pension_stats(window=100):
    """
    연금복권 당첨 데이터 통계 계산
    - 조 빈도, 각 자리수 빈도, 보너스 빈도
    """
    data = load_pension_data()
    recent = data[:window] if data else []
    if not recent:
        return None

    group_freq = {}
    pos_freq = [dict() for _ in range(6)]  # 6자리
    bonus_freq = {}

    for entry in recent:
        group_freq[entry['group']] = group_freq.get(entry['group'], 0) + 1
        num_str = str(entry['number']).zfill(6)
        for idx, ch in enumerate(num_str):
            pos_freq[idx][ch] = pos_freq[idx].get(ch, 0) + 1
        bonus_str = str(entry.get('bonus', '')).zfill(6)
        if bonus_str:
            bonus_freq[bonus_str] = bonus_freq.get(bonus_str, 0) + 1

    return {
        'group_freq': group_freq,
        'pos_freq': pos_freq,
        'bonus_freq': bonus_freq,
        'total': len(recent)
    }


def _pick_from_freq(freq_map, prefer='hot'):
    """freq_map: dict(str->count). prefer hot or cold."""
    if not freq_map:
        return str(random.randint(0, 9))
    items = sorted(freq_map.items(), key=lambda x: x[1], reverse=True)
    if prefer == 'hot':
        top = items[:min(3, len(items))]
    elif prefer == 'cold':
        top = items[-min(3, len(items)):]
    else:
        top = items
    choices = [k for k, _ in top]
    return random.choice(choices)


def generate_pension_number(count=1, mode="random", stats=None):
    """
    연금복권 번호 생성 (조 1~5, 번호 000000~999999)
    mode: random | hot | cold | balanced
    """
    results = []
    stats = stats or get_pension_stats(window=100)

    # group 선택 기준
    group_hot = None
    group_cold = None
    if stats and stats.get('group_freq'):
        sorted_groups = sorted(stats['group_freq'].items(), key=lambda x: x[1], reverse=True)
        group_hot = sorted_groups[0][0]
        group_cold = sorted_groups[-1][0]

    for _ in range(count):
        # 그룹 선택
        if mode == "hot" and group_hot:
            group = group_hot
        elif mode == "cold" and group_cold:
            group = group_cold
        elif mode == "balanced" and group_hot and group_cold:
            group = random.choice([group_hot, group_cold])
        else:
            group = random.randint(1, 5)

        # 번호 6자리 생성
        digits = []
        for idx in range(6):
            if stats and stats.get('pos_freq'):
                prefer = "hot" if mode == "hot" else "cold" if mode == "cold" else None
                digit = _pick_from_freq(stats['pos_freq'][idx], prefer=prefer)
            else:
                digit = str(random.randint(0, 9))
            digits.append(digit)

        # 균형 모드는 앞자리/뒷자리 핫/콜드 섞기
        if mode == "balanced" and stats and stats.get('pos_freq'):
            for idx in range(6):
                prefer = "hot" if idx < 3 else "cold"
                digits[idx] = _pick_from_freq(stats['pos_freq'][idx], prefer=prefer)

        number = "".join(digits)
        results.append({
            'group': group,
            'number': number
        })

    return results

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


def generate_balanced_numbers(exclude_numbers=None):
    """
    밸런스 모드: 홀짝 균형 + 구간 분산 + 합계 최적화
    - 홀수 3개 + 짝수 3개
    - 합계 120-140 사이
    - 구간별 균등 분배
    """
    if exclude_numbers is None:
        exclude_numbers = []

    available_numbers = [i for i in range(1, 46) if i not in exclude_numbers]

    if len(available_numbers) < 6:
        return random.sample(available_numbers, min(6, len(available_numbers)))

    max_attempts = 100
    for attempt in range(max_attempts):
        # 홀수와 짝수 분리
        available_odds = [n for n in available_numbers if n % 2 == 1]
        available_evens = [n for n in available_numbers if n % 2 == 0]

        # 홀수 3개, 짝수 3개 선택
        if len(available_odds) >= 3 and len(available_evens) >= 3:
            odds = random.sample(available_odds, 3)
            evens = random.sample(available_evens, 3)
            numbers = sorted(odds + evens)

            # 합계 체크 (120-140)
            total = sum(numbers)
            if 120 <= total <= 140:
                # 구간별 체크 (1-15, 16-30, 31-45 각 구간에서 최소 1개)
                zone1 = len([n for n in numbers if 1 <= n <= 15])
                zone2 = len([n for n in numbers if 16 <= n <= 30])
                zone3 = len([n for n in numbers if 31 <= n <= 45])

                if zone1 >= 1 and zone2 >= 1 and zone3 >= 1:
                    return numbers

    # 조건을 만족하는 번호를 찾지 못한 경우 랜덤 생성
    return sorted(random.sample(available_numbers, 6))


def generate_underdog_numbers(exclude_numbers=None, recent_rounds=20):
    """
    언더독 모드: 최근 N회차 미출현 번호 중심
    - 최근 20회차에 안 나온 번호 위주 선택
    - 저빈도 번호 포함
    """
    if exclude_numbers is None:
        exclude_numbers = []

    available_numbers = [i for i in range(1, 46) if i not in exclude_numbers]

    if len(available_numbers) < 6:
        return random.sample(available_numbers, min(6, len(available_numbers)))

    # 최근 회차 데이터 로드
    data = load_lotto_data()
    recent_data = data[:recent_rounds] if data else []

    # 최근 회차에 나온 번호 수집
    appeared = set()
    for draw in recent_data:
        appeared.update(draw['number'])
        appeared.add(draw['bonus'])

    # 미출현 번호
    cold_numbers = [n for n in available_numbers if n not in appeared]

    selected_numbers = []

    # 미출현 번호 4개 선택 (있으면)
    if len(cold_numbers) >= 4:
        selected_numbers.extend(random.sample(cold_numbers, 4))
    elif cold_numbers:
        selected_numbers.extend(cold_numbers)

    # 나머지는 저빈도 번호에서 선택
    if len(selected_numbers) < 6:
        # 빈도 계산
        from collections import Counter
        freq = Counter()
        for draw in recent_data:
            freq.update(draw['number'])

        # 저빈도 번호 (빈도가 낮은 순서대로)
        low_freq_numbers = [n for n, count in freq.most_common()[::-1] if n not in exclude_numbers and n not in selected_numbers]

        remaining_needed = 6 - len(selected_numbers)
        if len(low_freq_numbers) >= remaining_needed:
            selected_numbers.extend(random.sample(low_freq_numbers[:15], remaining_needed))
        else:
            # 부족하면 일반 풀에서 채우기
            remaining_pool = [n for n in available_numbers if n not in selected_numbers]
            if remaining_pool:
                selected_numbers.extend(random.sample(remaining_pool, min(remaining_needed, len(remaining_pool))))

    return sorted(selected_numbers[:6])


def generate_prize_optimized_numbers(exclude_numbers=None):
    """
    상금 최적화 모드: 당첨 시 상금을 최대화하는 조합
    - 생일 번호(1-31) 피하기 (많은 사람들이 선택)
    - 32 이상 번호 위주 선택
    - 7의 배수 등 인기 번호 피하기
    """
    if exclude_numbers is None:
        exclude_numbers = []

    available_numbers = [i for i in range(1, 46) if i not in exclude_numbers]

    if len(available_numbers) < 6:
        return random.sample(available_numbers, min(6, len(available_numbers)))

    # 인기 번호 정의 (피해야 할 번호)
    popular_numbers = set()
    # 1. 생일 범위 (1-31)
    popular_numbers.update(range(1, 32))
    # 2. 7의 배수
    popular_numbers.update([7, 14, 21, 28, 35, 42])
    # 3. 연속 번호 패턴 회피를 위한 인기 번호
    popular_numbers.update([1, 2, 3, 5, 10, 20, 30, 40])

    # 비인기 번호 (32-45 범위 중심)
    unpopular_numbers = [n for n in available_numbers if n not in popular_numbers]
    popular_available = [n for n in available_numbers if n in popular_numbers]

    selected_numbers = []

    # 비인기 번호에서 4개 선택
    if len(unpopular_numbers) >= 4:
        selected_numbers.extend(random.sample(unpopular_numbers, 4))
    else:
        selected_numbers.extend(unpopular_numbers)

    # 나머지는 인기 번호에서 선택 (완전히 편향되지 않도록)
    remaining_needed = 6 - len(selected_numbers)
    if remaining_needed > 0 and popular_available:
        selected_numbers.extend(random.sample(popular_available, min(remaining_needed, len(popular_available))))

    # 부족하면 일반 풀에서 채우기
    if len(selected_numbers) < 6:
        remaining_pool = [n for n in available_numbers if n not in selected_numbers]
        if remaining_pool:
            selected_numbers.extend(random.sample(remaining_pool, 6 - len(selected_numbers)))

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
        generation_mode = request.GET.get('mode', 'random')  # 'random', 'smart', 'balanced', 'underdog', 'prize'
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
            try:
                if generation_mode == 'smart':
                    selected_numbers = generate_smart_numbers(exclude_numbers_list)
                elif generation_mode == 'balanced':
                    selected_numbers = generate_balanced_numbers(exclude_numbers_list)
                elif generation_mode == 'underdog':
                    selected_numbers = generate_underdog_numbers(exclude_numbers_list)
                elif generation_mode == 'prize':
                    selected_numbers = generate_prize_optimized_numbers(exclude_numbers_list)
                else:
                    # 기본 랜덤 생성
                    selected_numbers = random.sample(available_numbers, 6)
                    selected_numbers.sort()

                if len(selected_numbers) < 6:
                    # 생성 실패 시 랜덤으로 폴백
                    selected_numbers = random.sample(available_numbers, 6)
                    selected_numbers.sort()

                all_number_sets.append(selected_numbers)
            except Exception as e:
                # 생성 실패 시 랜덤으로 폴백
                selected_numbers = random.sample(available_numbers, 6)
                selected_numbers.sort()
                all_number_sets.append(selected_numbers)

        # 응답 구성
        mode_descriptions = {
            'random': f"완전 랜덤으로 생성된 {count}개의 번호입니다",
            'smart': f"통계 기반으로 생성된 {count}개의 번호입니다",
            'balanced': f"홀짝 균형과 구간 분산을 고려한 {count}개의 번호입니다",
            'underdog': f"최근 미출현 번호 위주로 생성된 {count}개의 번호입니다",
            'prize': f"당첨금 최적화를 고려한 {count}개의 번호입니다"
        }

        info_message = mode_descriptions.get(generation_mode, f"생성된 {count}개의 번호입니다")

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


class GetNumberAnalysis(APIView):
    """
    번호 패턴 분석 대시보드 데이터를 제공하는 API 뷰
    홀짝 비율, 합계 분포, 구간별 분포, 연속 번호 출현 등 분석
    """
    def get(self, request):
        rounds = request.GET.get('rounds', '30')

        try:
            rounds = int(rounds)
            if rounds not in [10, 30, 50, 100]:
                rounds = 30  # 기본값
        except ValueError:
            rounds = 30

        data = load_lotto_data()
        recent_data = data[:rounds] if data else []

        if not recent_data:
            return Response({"error": "데이터를 불러올 수 없습니다."},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 분석 결과 초기화
        odd_even_counts = {'3:3': 0, '4:2': 0, '2:4': 0, '5:1': 0, '1:5': 0, '6:0': 0, '0:6': 0}
        sum_ranges = {'90-110': 0, '111-130': 0, '131-150': 0, '151-170': 0, '171-190': 0, '191-210': 0}
        zone_distributions = {}
        consecutive_count = 0
        sum_list = []

        for draw in recent_data:
            numbers = draw['number']

            # 1. 홀짝 비율 분석
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            even_count = 6 - odd_count
            ratio_key = f"{odd_count}:{even_count}"
            if ratio_key in odd_even_counts:
                odd_even_counts[ratio_key] += 1

            # 2. 합계 분석
            total = sum(numbers)
            sum_list.append(total)

            if 90 <= total <= 110:
                sum_ranges['90-110'] += 1
            elif 111 <= total <= 130:
                sum_ranges['111-130'] += 1
            elif 131 <= total <= 150:
                sum_ranges['131-150'] += 1
            elif 151 <= total <= 170:
                sum_ranges['151-170'] += 1
            elif 171 <= total <= 190:
                sum_ranges['171-190'] += 1
            elif 191 <= total <= 210:
                sum_ranges['191-210'] += 1

            # 3. 구간별 분포 (1-10, 11-20, 21-30, 31-40, 41-45)
            zone_pattern = []
            zone_pattern.append(len([n for n in numbers if 1 <= n <= 10]))
            zone_pattern.append(len([n for n in numbers if 11 <= n <= 20]))
            zone_pattern.append(len([n for n in numbers if 21 <= n <= 30]))
            zone_pattern.append(len([n for n in numbers if 31 <= n <= 40]))
            zone_pattern.append(len([n for n in numbers if 41 <= n <= 45]))

            pattern_key = '-'.join(map(str, zone_pattern))
            zone_distributions[pattern_key] = zone_distributions.get(pattern_key, 0) + 1

            # 4. 연속 번호 출현 체크
            has_consecutive = False
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] == 1:
                    has_consecutive = True
                    break
            if has_consecutive:
                consecutive_count += 1

        # 합계 통계 계산
        avg_sum = sum(sum_list) / len(sum_list) if sum_list else 0
        min_sum = min(sum_list) if sum_list else 0
        max_sum = max(sum_list) if sum_list else 0

        # 구간별 분포 상위 5개만 반환
        sorted_zone_distributions = sorted(zone_distributions.items(), key=lambda x: x[1], reverse=True)[:5]

        result = {
            'rounds': rounds,
            'odd_even_ratios': odd_even_counts,
            'sum_ranges': sum_ranges,
            'sum_stats': {
                'average': round(avg_sum, 1),
                'min': min_sum,
                'max': max_sum
            },
            'zone_distributions': dict(sorted_zone_distributions),
            'consecutive_percentage': round((consecutive_count / len(recent_data)) * 100, 1) if recent_data else 0,
            'consecutive_count': consecutive_count,
            'total_draws': len(recent_data)
        }

        return Response(result, status=status.HTTP_200_OK)


class GetPensionNumber(APIView):
    """
    연금복권 번호를 생성하는 API 뷰
    """
    def get(self, request):
        count = request.GET.get('count', '1')
        mode = request.GET.get('mode', 'random')  # random/hot/cold/balanced

        # 생성 개수 처리
        try:
            count = int(count)
            if count not in [1, 3, 5, 10]:
                count = 1
        except ValueError:
            count = 1

        stats = get_pension_stats(window=100)

        # 연금복권 번호 생성
        pension_numbers = generate_pension_number(count, mode=mode, stats=stats)

        return Response({
            "pension_numbers": pension_numbers,
            "count": count,
            "mode": mode,
            "info": f"{mode} 모드로 생성된 {count}개의 연금복권 번호입니다",
            "stats_total": stats['total'] if stats else 0
        })


class PensionMainView(APIView):
    """
    연금복권 메인 페이지를 렌더링하는 뷰
    """
    def get(self, request):
        # JSON 파일에서 최신 당첨번호 가져오기
        pension_data = load_pension_data()
        latest_pension = pension_data[0] if pension_data else None
        recent_pensions = pension_data[:10] if pension_data else []

        context = {
            'latest_pension': latest_pension,
            'recent_pensions': recent_pensions,
        }

        return render(request, 'lotto/pension.html', context)


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

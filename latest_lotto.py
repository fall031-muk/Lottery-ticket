import json
from datetime import datetime
import os

class LatestLottoManager:
    def __init__(self, json_file_path="lotto_num.json"):
        self.json_file_path = json_file_path
        
    def get_latest_lotto_data(self):
        """JSON 파일에서 최신 당첨번호 데이터를 가져옵니다."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            if not data:
                return None
                
            # JSON이 최신순으로 정렬되어 있으므로 첫 번째 항목이 최신
            latest = data[0]
            return latest
            
        except FileNotFoundError:
            print(f"❌ {self.json_file_path} 파일을 찾을 수 없습니다.")
            return None
        except json.JSONDecodeError:
            print(f"❌ {self.json_file_path} 파일을 읽는 중 오류가 발생했습니다.")
            return None
    
    def display_latest_lotto(self):
        """최신 당첨번호를 화면에 출력합니다."""
        latest = self.get_latest_lotto_data()
        
        if latest:
            print("🎯 최신 로또 당첨번호")
            print("=" * 40)
            print(f"회차: {latest['round']}회")
            print(f"추첨일: {latest['date']}")
            print(f"당첨번호: {' - '.join(map(str, sorted(latest['number'])))}")
            print(f"보너스번호: {latest['bonus']}")
            print("=" * 40)
            return latest
        else:
            print("❌ 최신 당첨번호를 가져올 수 없습니다.")
            return None
    
    def get_recent_numbers(self, count=5):
        """최근 N회차의 당첨번호를 가져옵니다."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            if not data:
                return []
                
            # 최근 count개 회차 반환
            return data[:count]
            
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def display_recent_numbers(self, count=5):
        """최근 N회차의 당첨번호를 출력합니다."""
        recent = self.get_recent_numbers(count)
        
        if recent:
            print(f"📊 최근 {count}회차 당첨번호")
            print("=" * 50)
            for lotto in recent:
                numbers_str = ' - '.join(map(str, sorted(lotto['number'])))
                print(f"{lotto['round']}회 ({lotto['date']}): {numbers_str} + {lotto['bonus']}")
            print("=" * 50)
        else:
            print("❌ 최근 당첨번호를 가져올 수 없습니다.")
    
    def check_file_update(self):
        """JSON 파일의 마지막 수정시간을 확인합니다."""
        try:
            if os.path.exists(self.json_file_path):
                modify_time = os.path.getmtime(self.json_file_path)
                modify_datetime = datetime.fromtimestamp(modify_time)
                print(f"📅 JSON 파일 마지막 업데이트: {modify_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                return modify_datetime
            else:
                print(f"❌ {self.json_file_path} 파일이 존재하지 않습니다.")
                return None
        except Exception as e:
            print(f"❌ 파일 정보를 확인하는 중 오류 발생: {e}")
            return None
    
    def get_number_statistics(self):
        """최근 10회차의 번호 통계를 분석합니다."""
        recent = self.get_recent_numbers(10)
        
        if not recent:
            return None
        
        # 번호 빈도 계산
        number_count = {}
        bonus_count = {}
        
        for lotto in recent:
            # 일반 번호
            for num in lotto['number']:
                number_count[num] = number_count.get(num, 0) + 1
            
            # 보너스 번호
            bonus = lotto['bonus']
            bonus_count[bonus] = bonus_count.get(bonus, 0) + 1
        
        # 가장 많이 나온 번호들
        sorted_numbers = sorted(number_count.items(), key=lambda x: x[1], reverse=True)
        sorted_bonus = sorted(bonus_count.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'number_frequency': sorted_numbers,
            'bonus_frequency': sorted_bonus,
            'total_rounds': len(recent)
        }
    
    def display_statistics(self):
        """번호 통계를 출력합니다."""
        stats = self.get_number_statistics()
        
        if stats:
            print(f"📈 최근 {stats['total_rounds']}회차 번호 통계")
            print("=" * 40)
            print("자주 나온 번호 (TOP 10):")
            for i, (num, count) in enumerate(stats['number_frequency'][:10], 1):
                print(f"{i:2d}. {num:2d}번 ({count}회)")
            
            print("\n자주 나온 보너스번호 (TOP 5):")
            for i, (num, count) in enumerate(stats['bonus_frequency'][:5], 1):
                print(f"{i:2d}. {num:2d}번 ({count}회)")
            print("=" * 40)

def main():
    """메인 실행 함수"""
    lotto_manager = LatestLottoManager()
    
    print("🎲 로또 당첨번호 관리 시스템")
    print()
    
    # 파일 업데이트 정보 확인
    lotto_manager.check_file_update()
    print()
    
    # 최신 당첨번호 출력
    latest = lotto_manager.display_latest_lotto()
    print()
    
    # 최근 5회차 출력
    lotto_manager.display_recent_numbers(5)
    print()
    
    # 통계 출력
    lotto_manager.display_statistics()

if __name__ == "__main__":
    main() 
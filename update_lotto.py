import json
from datetime import datetime

class LottoUpdater:
    def __init__(self, json_file_path="lotto_num.json"):
        self.json_file_path = json_file_path
    
    def load_current_data(self):
        """현재 JSON 파일의 데이터를 로드합니다."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"❌ {self.json_file_path} 파일을 찾을 수 없습니다.")
            return []
        except json.JSONDecodeError:
            print(f"❌ {self.json_file_path} 파일을 읽는 중 오류가 발생했습니다.")
            return []
    
    def save_data(self, data):
        """데이터를 JSON 파일로 저장합니다."""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 파일 저장 중 오류 발생: {e}")
            return False
    
    def add_new_round(self, round_num, date, numbers, bonus):
        """새로운 회차 데이터를 추가합니다."""
        # 입력 검증
        if not self.validate_input(round_num, date, numbers, bonus):
            return False
        
        # 현재 데이터 로드
        data = self.load_current_data()
        
        # 중복 회차 체크
        for entry in data:
            if entry['round'] == round_num:
                print(f"❌ {round_num}회차는 이미 존재합니다.")
                return False
        
        # 새 데이터 생성
        new_entry = {
            "round": round_num,
            "date": date,
            "number": sorted(numbers),  # 번호를 정렬해서 저장
            "bonus": bonus
        }
        
        # 데이터 추가 (최신순으로 정렬)
        data.append(new_entry)
        data.sort(key=lambda x: x['round'], reverse=True)
        
        # 저장
        if self.save_data(data):
            print(f"✅ {round_num}회차 데이터가 성공적으로 추가되었습니다!")
            print(f"   날짜: {date}")
            print(f"   당첨번호: {' - '.join(map(str, sorted(numbers)))}")
            print(f"   보너스번호: {bonus}")
            return True
        else:
            return False
    
    def validate_input(self, round_num, date, numbers, bonus):
        """입력 데이터를 검증합니다."""
        # 회차 번호 검증
        if not isinstance(round_num, int) or round_num <= 0:
            print("❌ 회차 번호는 양의 정수여야 합니다.")
            return False
        
        # 날짜 형식 검증 (YYYY-MM-DD)
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print("❌ 날짜는 YYYY-MM-DD 형식이어야 합니다.")
            return False
        
        # 당첨번호 검증
        if not isinstance(numbers, list) or len(numbers) != 6:
            print("❌ 당첨번호는 6개여야 합니다.")
            return False
        
        for num in numbers:
            if not isinstance(num, int) or not (1 <= num <= 45):
                print("❌ 당첨번호는 1~45 사이의 정수여야 합니다.")
                return False
        
        if len(set(numbers)) != 6:
            print("❌ 당첨번호에 중복이 있습니다.")
            return False
        
        # 보너스번호 검증
        if not isinstance(bonus, int) or not (1 <= bonus <= 45):
            print("❌ 보너스번호는 1~45 사이의 정수여야 합니다.")
            return False
        
        if bonus in numbers:
            print("❌ 보너스번호는 당첨번호와 중복될 수 없습니다.")
            return False
        
        return True
    
    def get_latest_round(self):
        """현재 저장된 최신 회차를 반환합니다."""
        data = self.load_current_data()
        if data:
            return data[0]['round']  # 최신순으로 정렬되어 있으므로 첫 번째가 최신
        return 0
    
    def interactive_add(self):
        """대화형으로 새 회차를 추가합니다."""
        print("🆕 새 회차 데이터 추가")
        print("=" * 30)
        
        latest_round = self.get_latest_round()
        suggested_round = latest_round + 1
        
        try:
            # 회차 입력
            round_input = input(f"회차 번호 (제안: {suggested_round}): ").strip()
            round_num = int(round_input) if round_input else suggested_round
            
            # 날짜 입력
            today = datetime.now().strftime('%Y-%m-%d')
            date_input = input(f"추첨일 (YYYY-MM-DD, 기본값: {today}): ").strip()
            date = date_input if date_input else today
            
            # 당첨번호 입력
            numbers_input = input("당첨번호 6개 (공백으로 구분): ").strip()
            numbers = [int(x) for x in numbers_input.split()]
            
            # 보너스번호 입력
            bonus = int(input("보너스번호: "))
            
            # 데이터 추가
            return self.add_new_round(round_num, date, numbers, bonus)
            
        except ValueError:
            print("❌ 입력 형식이 올바르지 않습니다.")
            return False
        except KeyboardInterrupt:
            print("\n❌ 입력이 취소되었습니다.")
            return False

def main():
    """메인 실행 함수"""
    updater = LottoUpdater()
    
    print("🔄 로또 데이터 업데이트 시스템")
    print()
    
    # 현재 최신 회차 표시
    latest = updater.get_latest_round()
    if latest:
        print(f"현재 최신 회차: {latest}회")
    else:
        print("저장된 데이터가 없습니다.")
    
    print()
    
    # 대화형 추가
    while True:
        result = updater.interactive_add()
        print()
        
        if result:
            # 최신 데이터 로드해서 보여주기
            from latest_lotto import LatestLottoManager
            lotto_manager = LatestLottoManager()
            lotto_manager.display_latest_lotto()
        
        # 계속 추가할지 물어보기
        continue_input = input("다른 회차를 추가하시겠습니까? (y/N): ").strip().lower()
        if continue_input not in ['y', 'yes']:
            break
    
    print("👋 업데이트를 완료했습니다!")

if __name__ == "__main__":
    main() 
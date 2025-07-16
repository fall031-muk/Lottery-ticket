import re
import json

def parse_lotto_html(file_path):
    """HTML 파일에서 로또 정보를 추출하여 JSON 형태로 변환"""
    
    # 여러 인코딩을 시도해보기
    encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                print(f"파일을 {encoding} 인코딩으로 읽었습니다.")
                break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        raise ValueError("파일을 읽을 수 없습니다. 인코딩을 확인해주세요.")
    
    # 각 회차의 tr 태그 찾기
    tr_pattern = r'<tr>.*?</tr>'
    tr_matches = re.findall(tr_pattern, content, re.DOTALL)
    
    lotto_data = []
    
    for tr in tr_matches:
        # 회차 추출
        round_match = re.search(r'<td align="right">(\d+)</td>', tr)
        if not round_match:
            continue
            
        round_num = int(round_match.group(1))
        
        # 날짜 추출
        date_match = re.search(r'<td align="center">(\d{4}\.\d{2}\.\d{2})</td>', tr)
        if not date_match:
            continue
            
        date = date_match.group(1)
        
        # 모든 td 태그에서 숫자만 추출 (당첨번호 + 보너스번호)
        all_tds = re.findall(r'<td>(\d+)</td>', tr)
        
        # 마지막 7개 td가 당첨번호 6개 + 보너스번호 1개
        if len(all_tds) >= 7:
            winning_numbers = [int(num) for num in all_tds[-7:-1]]  # 마지막 7개 중 앞의 6개
            bonus_number = int(all_tds[-1])  # 마지막 1개
            
            # 날짜 형식 변환 (YYYY.MM.DD -> YYYY-MM-DD)
            formatted_date = date.replace('.', '-')
            
            lotto_entry = {
                "round": round_num,
                "date": formatted_date,
                "number": winning_numbers,
                "bonus": bonus_number
            }
            
            lotto_data.append(lotto_entry)
    
    # 회차순으로 정렬 (내림차순 - 최신 회차가 위로)
    lotto_data.sort(key=lambda x: x['round'], reverse=True)
    
    return lotto_data

def save_to_json(data, output_file):
    """데이터를 JSON 파일로 저장"""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    input_file = "/Users/muk/Downloads/excel.json"
    output_file = "lotto_num.json"
    
    print("로또 데이터 파싱 중...")
    lotto_data = parse_lotto_html(input_file)
    
    print(f"총 {len(lotto_data)}개의 회차 데이터를 찾았습니다.")
    
    # 첫 번째와 마지막 회차 확인
    if lotto_data:
        print(f"첫 번째 회차: {lotto_data[0]['round']}회 ({lotto_data[0]['date']})")
        print(f"마지막 회차: {lotto_data[-1]['round']}회 ({lotto_data[-1]['date']})")
        
        # 샘플 데이터 출력
        print("\n샘플 데이터:")
        for i in range(min(3, len(lotto_data))):
            entry = lotto_data[i]
            print(f"{entry['round']}회 ({entry['date']}): {entry['number']} + {entry['bonus']}")
    
    # JSON 파일로 저장
    save_to_json(lotto_data, output_file)
    print(f"\n데이터가 '{output_file}' 파일로 저장되었습니다.") 
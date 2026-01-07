"""연금복권 720+ 과거 당첨번호를 dhlottery API에서 가져와 pension_num.json을 갱신하는 스크립트.
환경 제약: 현재 작업 샌드박스는 네트워크가 차단되어 있어 실제 요청은 실패한다.
실제 업데이트는 네트워크 허용 환경에서 실행하세요."""
import json
import os
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

URL = "https://dhlottery.co.kr/pt720/selectPstPt720WnList.do"
JSON_FILE = os.path.join(os.path.dirname(__file__), "pension_num.json")


def load_existing(path: str = JSON_FILE) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_entries(entries: List[Dict], path: str = JSON_FILE) -> None:
    dedup = {e["round"]: e for e in entries if "round" in e}
    sorted_entries = sorted(dedup.values(), key=lambda x: x["round"], reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted_entries, f, ensure_ascii=False, indent=2)


def normalize_entry(raw: Dict) -> Optional[Dict]:
    """여러 키 이름을 허용해 round/group/number/bonus/date를 표준화."""
    key_map = {
        # 회차
        "round": ["round", "drwNo", "turnNo", "times", "gameRound", "psltEpsd"],
        # 추첨일
        "date": ["drawDate", "drwDate", "date", "opendate", "opnDt", "psltRflYmd"],
        # 조
        "group": ["group", "grpNo", "groupNo", "josu", "wnBndNo"],
        # 당첨번호
        "number": [
            "number",
            "winNo",
            "przwnerNo",
            "firstNo",
            "no",
            "winNumber",
            "wnRnkVl",
        ],
        # 보너스
        "bonus": ["bonus", "bonusNo", "bnNo", "bonusNumber", "bnsRnkVl"],
    }

    def first_key(d: Dict, names: List[str]):
        for k in names:
            if k in d:
                return d[k]
        return None

    round_val = first_key(raw, key_map["round"])
    number_val = first_key(raw, key_map["number"])
    group_val = first_key(raw, key_map["group"])
    bonus_val = first_key(raw, key_map["bonus"])
    date_val = first_key(raw, key_map["date"])

    try:
        round_int = int(round_val)
    except Exception:
        return None

    # number는 문자열 6자리로 정규화
    if number_val is not None:
        number_str = str(number_val).zfill(6)
    else:
        return None

    bonus_str = str(bonus_val).zfill(6) if bonus_val is not None else ""

    # group은 1~5
    group_int = None
    if group_val is not None:
        try:
            group_int = int(group_val)
        except Exception:
            group_int = None

    # 날짜가 8자리 숫자(YYYYMMDD)이면 YYYY-MM-DD로 변환
    if date_val and re.fullmatch(r"\d{8}", str(date_val)):
        d = str(date_val)
        date_val = f"{d[:4]}-{d[4:6]}-{d[6:]}"

    return {
        "round": round_int,
        "date": str(date_val).replace(".", "-") if date_val else "",
        "group": group_int,
        "number": number_str,
        "bonus": bonus_str,
    }


def parse_json_payload(payload) -> List[Dict]:
    """JSON 응답에서 당첨 리스트를 찾아 표준화."""
    candidates = []
    if isinstance(payload, list):
        candidates.append(payload)
    elif isinstance(payload, dict):
        # 1단계 value
        for v in payload.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                candidates.append(v)
            # 2단계 중첩 dict 내부 리스트도 추가
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, list) and vv and isinstance(vv[0], dict):
                        candidates.append(vv)

    results = []
    for cand in candidates:
        for item in cand:
            norm = normalize_entry(item)
            if norm:
                results.append(norm)
    return results


def parse_html_payload(html: str) -> List[Dict]:
    """HTML 응답인 경우 테이블/리스트를 파싱."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    # 테이블 행 기반 파싱
    for tr in soup.select("table tbody tr"):
        text = tr.get_text(" ", strip=True)
        round_m = re.search(r"(\d+)회", text)
        group_m = re.search(r"([1-5])조", text)
        nums = re.findall(r"\b(\d{6})\b", text)
        if round_m and nums:
            entries.append({
                "round": int(round_m.group(1)),
                "date": "",
                "group": int(group_m.group(1)) if group_m else None,
                "number": nums[0],
                "bonus": nums[1] if len(nums) > 1 else "",
            })

    # 리스트 항목 기반 파싱 (li 등)
    if not entries:
        for block in soup.find_all(text=re.compile("회")):
            text = block if isinstance(block, str) else block.get_text(" ", strip=True)
            round_m = re.search(r"(\d+)회", text)
            group_m = re.search(r"([1-5])조", text)
            nums = re.findall(r"\b(\d{6})\b", text)
            if round_m and nums:
                entries.append({
                    "round": int(round_m.group(1)),
                    "date": "",
                    "group": int(group_m.group(1)) if group_m else None,
                    "number": nums[0],
                    "bonus": nums[1] if len(nums) > 1 else "",
                })
    return entries


def fetch_page(page_index: int = 1, page_size: int = 100) -> List[Dict]:
    resp = requests.get(URL, params={"pageIndex": page_index, "pageSize": page_size}, timeout=5)
    try:
        payload = resp.json()
        parsed = parse_json_payload(payload)
        if parsed:
            return parsed
    except ValueError:
        pass
    return parse_html_payload(resp.text)


def update_pension(max_fetch: int = 100, sleep_sec: float = 0.2) -> List[Dict]:
    existing = load_existing()
    have_rounds = {e["round"] for e in existing if "round" in e}

    collected: List[Dict] = []
    page = 1
    while len(collected) < max_fetch:
        page_data = fetch_page(page_index=page, page_size=min(50, max_fetch))
        if not page_data:
            break
        for entry in page_data:
            if entry["round"] in have_rounds:
                continue
            collected.append(entry)
            have_rounds.add(entry["round"])
            if len(collected) >= max_fetch:
                break
        page += 1
        time.sleep(sleep_sec)

    merged = existing + collected
    save_entries(merged)
    return merged


if __name__ == "__main__":
    print("⚠️  이 스크립트는 네트워크가 허용된 환경에서 실행하세요.")
    try:
        updated = update_pension(max_fetch=100)
        print(f"총 {len(updated)}개 회차를 저장했습니다. (pension_num.json 갱신)")
        if updated:
            print(f"최신 회차: {updated[0]['round']}회")
    except Exception as e:
        print(f"업데이트 실패: {e}")


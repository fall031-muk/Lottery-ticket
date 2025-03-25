# 🎱 로또 번호 생성기

행운의 로또 번호를 생성하고 당첨 번호를 확인할 수 있는 웹 서비스입니다.

🔗 **서비스 링크**: [https://hmyun.pythonanywhere.com/](https://hmyun.pythonanywhere.com/)

## 🌟 주요 기능

- **로또 번호 자동 생성**: 랜덤 알고리즘으로 로또 번호를 생성합니다
- **최신 당첨 번호 확인**: 동행복권 API를 통해 실시간으로 최신 당첨 번호를 확인할 수 있습니다
- **직전 회차 제외/선택 기능**: 직전회차의 번호를 제외하고 생성할 수 있습니다
- **반응형 디자인**: 모바일, 태블릿, PC 등 모든 디바이스에서 편리하게 사용 가능합니다

## ⚠️ 알림사항

- PythonAnywhere 무료 계정의 제한으로 인해 이전 회차 당첨 번호 조회 기능은 현재 사용할 수 없습니다

## 🛠 기술 스택

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite
- **API**: 동행복권 API 연동
- **Deployment**: PythonAnywhere (무료 호스팅)

## 🚀 설치 및 실행 방법

1. 저장소 클론
```bash
git clone https://github.com/fall031-muk/Lottery-ticket.git
cd Lottery-ticket
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

5. 개발 서버 실행
```bash
python manage.py runserver
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 🙏 감사의 글

이 프로젝트는 [동행복권](https://www.dhlottery.co.kr/)의 API를 활용하여 제작되었습니다.

## 📞 연락처

문의사항이나 버그 리포트는 이슈를 통해 남겨주세요.

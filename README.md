# WORKFIT 마케팅 AGENT 프로세스

![v01](autoMktprocess/source/Gp6EkBmawAELvhB-1.jpg)


RSS 피드 및 웹 스크래핑을 통해 최신 정보를 수집하고, 생성형 AI를 활용하여 주요 포인트를 추출한 뒤, 다양한 채널로 전송하는 수준입니다.

개별 커스텀을 원하는 마케터나, 창업자들은 기능 개선에 대한 논의는 누구나 참여 가능한 아래 오픈채팅방에서 네트워킹을 하세요
[카카오톡 오픈채팅 참여하기](https://open.kakao.com/o/gl5tS9rh)

## 현 버전 기능

- RSS 피드 스크래핑
- 생성형 AI (Google Gemini) 기반 콘텐츠 요약 및 "도파민 포인트" 추출
- SQLite를 이용한 결과 데이터 저장 (중복 방지)
- 다양한 출력 형식 및 전송 채널 지원 (콘솔 출력 기본, 확장 가능)

## 설정

이 프로젝트는 환경 변수 또는 프로젝트 루트의 `.env` 파일을 통해 설정을 관리합니다.
필요한 환경 변수는 다음과 같습니다:

```dotenv
# .env 파일 예시

# Google Gemini API 키 (필수)
GEMINI_API_KEY="YOUR_GOOGLE_API_KEY"

# 사용할 Gemini 모델 이름 (선택 사항, 기본값: gemini-1.5-flash)
# GEMINI_MODEL_NAME="gemini-pro"

# 스크래핑할 RSS 피드 URL 목록 (최소 1개 필수)
RSS_FEED_1="https://www.businesspost.co.kr/BP?command=rss"
RSS_FEED_2="https://www.yna.co.kr/RSS/economy.xml"
# RSS_FEED_3="..."

# SQLite 데이터베이스 파일명 (선택 사항, 기본값: automkt.db)
# DATABASE_FILE_NAME="my_articles.db"

# Slack 알림을 위한 Webhook URL (선택 사항)
# SLACK_WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL"
```

## 설치 및 실행

1.  **저장소 클론:**
    ```bash
    git clone <repository_url>
    cd autoMktprocess
    ```
2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```
3.  **의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **.env 파일 생성 및 설정:** 위 "설정" 섹션을 참고하여 `.env` 파일을 생성하고 필요한 값을 입력합니다.
5.  **실행:**
    ```bash
    python main.py
    ```

## 데이터베이스

- 결과는 SQLite 데이터베이스 파일(기본값: `automkt.db`)에 저장됩니다.
- DB Browser for SQLite 같은 도구를 사용하여 내용을 확인할 수 있습니다. 
"""데이터베이스 테이블 스키마 (모델) 정의"""

# articles 테이블 생성 SQL 문
ARTICLES_TABLE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,      -- 고유 식별자
        title TEXT NOT NULL,                   -- 기사 제목 (필수)
        link TEXT NOT NULL UNIQUE,             -- 기사 링크 (필수, 고유값)
        summary TEXT,                          -- 기사 요약 (선택)
        dopamine_points TEXT,                  -- 도파민 포인트 (JSON 문자열 저장)
        gen_image TEXT,                        -- 생성된 이미지 경로/URL (선택)
        posting_image TEXT,                    -- 포스팅용 이미지 경로/URL (선택)
        posting_video TEXT,                    -- 포스팅용 비디오 경로/URL (선택)
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 스크랩 시간 (자동 기록)
        -- 필요시 여기에 컬럼 추가 (예: published_date TIMESTAMP)
    )
"""

# 필요에 따라 다른 테이블 스키마도 여기에 추가할 수 있습니다.
# USERS_TABLE_SCHEMA = """ ... """ 
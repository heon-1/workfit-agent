import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import os # 설정 로드를 위해 os 추가

from core.models import ARTICLES_TABLE_SCHEMA # 모델 스키마 임포트
from configs.settings import load_config # 설정 로드를 위해 임포트

# 전역 변수 대신 함수 호출 시 파일명 전달 방식으로 변경 고려 가능
# 또는 설정에서 파일명을 읽어오는 함수 추가
config = load_config() # 초기 설정 로드
DATABASE_FILE = config.get('database', {}).get('file_name', 'automkt.db') # 설정에서 DB 파일명 읽기

def get_db_connection() -> Optional[sqlite3.Connection]:
    """SQLite 데이터베이스 연결을 생성하고 반환합니다."""
    try:
        db_file = DATABASE_FILE # 전역 또는 설정에서 가져온 파일명 사용
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"데이터베이스 연결 실패 ({DATABASE_FILE}): {e}", exc_info=True)
        return None

def initialize_db():
    """데이터베이스 및 테이블을 초기화합니다.
       core/models.py에 정의된 스키마를 사용합니다.
    """
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        # core.models 에서 가져온 스키마 사용
        cursor.execute(ARTICLES_TABLE_SCHEMA)
        # 필요시 다른 테이블 스키마도 여기에 추가
        # cursor.execute(USERS_TABLE_SCHEMA)
        conn.commit()
        logging.info(f"데이터베이스 테이블({DATABASE_FILE}) 초기화 완료 (또는 이미 존재)")
    except sqlite3.Error as e:
        logging.error(f"테이블 생성 실패: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def save_article(article_data: Dict[str, Any]) -> bool:
    """처리된 기사 데이터를 데이터베이스에 저장합니다.

    Args:
        article_data (Dict[str, Any]): 저장할 기사 데이터 ('title', 'link', 'summary', 'dopamine_points')

    Returns:
        bool: 저장 성공 여부
    """
    required_fields = ['title', 'link', 'dopamine_points']
    if not all(field in article_data for field in required_fields):
        logging.warning(f"저장에 필요한 필드가 누락되었습니다: {article_data}")
        return False

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # dopamine_points 리스트를 JSON 문자열로 변환
        dopamine_points_json = json.dumps(article_data.get('dopamine_points', []), ensure_ascii=False)

        # 링크 기준으로 중복 확인 후 삽입 시도 (INSERT OR IGNORE)
        cursor.execute("""
            INSERT OR IGNORE INTO articles (title, link, summary, dopamine_points, scraped_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            article_data['title'],
            article_data['link'],
            article_data.get('summary', ''), # 요약은 없을 수도 있음
            dopamine_points_json,
            datetime.now()
        ))

        conn.commit()

        # 변경된 행의 수를 확인하여 실제로 삽입되었는지 확인
        if cursor.rowcount > 0:
            logging.info(f"기사 저장 성공: '{article_data['title']}'")
            return True
        else:
            logging.info(f"이미 존재하는 기사 또는 저장 실패: '{article_data['title']}' (link: {article_data['link']})")
            return False # 이미 존재하거나 다른 이유로 저장 안 됨

    except sqlite3.Error as e:
        logging.error(f"기사 저장 실패: {e} - 데이터: {article_data}", exc_info=True)
        return False
    except json.JSONDecodeError as e:
        logging.error(f"Dopamine points JSON 변환 실패: {e} - 데이터: {article_data.get('dopamine_points')}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

# --- 데이터 조회 함수 (선택 사항) ---
def get_article_by_link(link: str) -> Optional[Dict[str, Any]]:
    """링크를 기준으로 기사를 조회합니다."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE link = ?", (link,))
        row = cursor.fetchone()
        if row:
            article = dict(row)
            # JSON 문자열을 다시 파이썬 리스트로 변환
            if article.get('dopamine_points'):
                try:
                    article['dopamine_points'] = json.loads(article['dopamine_points'])
                except json.JSONDecodeError:
                    logging.warning(f"DB에서 조회한 dopamine_points JSON 파싱 실패: link={link}")
                    article['dopamine_points'] = [] # 파싱 실패 시 빈 리스트
            return article
        else:
            return None
    except sqlite3.Error as e:
        logging.error(f"링크로 기사 조회 실패: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()

def get_all_articles(limit: int = 100) -> List[Dict[str, Any]]:
    """모든 기사를 조회합니다 (최근 N개)."""
    conn = get_db_connection()
    if conn is None: return []
    articles = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles ORDER BY scraped_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        for row in rows:
            article = dict(row)
            if article.get('dopamine_points'):
                try:
                    article['dopamine_points'] = json.loads(article['dopamine_points'])
                except json.JSONDecodeError:
                     article['dopamine_points'] = []
            articles.append(article)
        return articles
    except sqlite3.Error as e:
        logging.error(f"모든 기사 조회 실패: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()

def get_articles_without_gen_image(limit: int = 10) -> List[Dict[str, Any]]:
    """gen_image 필드가 비어있거나 NULL인 기사를 조회합니다."""
    conn = get_db_connection()
    if conn is None: return []
    articles = []
    try:
        cursor = conn.cursor()
        # gen_image가 NULL이거나 빈 문자열인 경우를 조회
        cursor.execute("SELECT id, title, link, summary FROM articles WHERE gen_image IS NULL OR gen_image = '' ORDER BY scraped_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        for row in rows:
            article = dict(row) # row_factory에 의해 이미 dict일 수 있음
            # dopamine_points는 이미지 생성에 직접 필요하지 않으므로 여기서는 제외 (필요시 추가 조회)
            articles.append(article)
        return articles
    except sqlite3.Error as e:
        logging.error(f"gen_image 없는 기사 조회 실패: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()

def update_article_gen_image(article_id: int, gen_image_path: str) -> bool:
    """ID를 기준으로 특정 기사의 gen_image 필드를 업데이트합니다.

    Args:
        article_id (int): 업데이트할 기사의 고유 ID
        gen_image_path (str): 저장된 생성 이미지의 경로

    Returns:
        bool: 업데이트 성공 여부
    """
    if not article_id or not gen_image_path:
        logging.warning("업데이트를 위한 ID 또는 이미지 경로가 없습니다.")
        return False

    conn = get_db_connection()
    if conn is None: return False

    sql = "UPDATE articles SET gen_image = ? WHERE id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (gen_image_path, article_id))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"기사(id={article_id}) gen_image 업데이트 성공: {gen_image_path}")
            return True
        else:
            logging.warning(f"기사(id={article_id})를 찾지 못했거나 gen_image 업데이트할 내용이 없습니다.")
            return False
    except sqlite3.Error as e:
        logging.error(f"기사 gen_image 업데이트 실패: {e} - id={article_id}, path={gen_image_path}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

"""
# --- 미디어 정보 업데이트 함수 (추후 구현 시 활성화) ---
def update_article_media(link: str, media_data: Dict[str, Optional[str]]) -> bool:
    ""링크를 기준으로 특정 기사의 미디어 관련 필드를 업데이트합니다.

    Args:
        link (str): 업데이트할 기사의 고유 링크
        media_data (Dict[str, Optional[str]]): 업데이트할 필드와 값 딕셔너리.
                                               예: {'gen_image': '/path/to/img.jpg', 'posting_video': None}
                                               키는 'gen_image', 'posting_image', 'posting_video' 중 하나 이상.

    Returns:
        bool: 업데이트 성공 여부
    ""
    if not link or not media_data:
        logging.warning("업데이트를 위한 링크 또는 미디어 데이터가 없습니다.")
        return False

    conn = get_db_connection()
    if conn is None: return False

    set_clauses = []
    values = []
    allowed_keys = {'gen_image', 'posting_image', 'posting_video'}

    for key, value in media_data.items():
        if key in allowed_keys:
            set_clauses.append(f"{key} = ?")
            values.append(value)
        else:
            logging.warning(f"허용되지 않은 업데이트 필드: {key}")

    if not set_clauses:
        logging.warning("업데이트할 유효한 미디어 필드가 없습니다.")
        return False

    values.append(link) # WHERE 절을 위한 값 추가
    sql = f"UPDATE articles SET {', '.join(set_clauses)} WHERE link = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"기사(link={link}) 미디어 정보 업데이트 성공: {media_data}")
            return True
        else:
            # 링크에 해당하는 기사가 없거나 값이 동일하여 변경되지 않은 경우
            logging.warning(f"기사(link={link})를 찾지 못했거나 업데이트할 내용이 없습니다.")
            return False
    except sqlite3.Error as e:
        logging.error(f"기사 미디어 정보 업데이트 실패: {e} - link={link}, data={media_data}", exc_info=True)
        return False
    finally:
        if conn: conn.close()
""" 
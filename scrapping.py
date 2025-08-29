import os
import json
import time
import requests
import dotenv
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from models import StatusItem

bojautologin = dotenv.dotenv_values('.env')['BOJ_AUTO_LOGIN']
assert len(bojautologin) > 0

def ensure_cache_dir() -> None:
    if not os.path.isdir('cache'):
        os.makedirs('cache', exist_ok=True)


def url_to_cache_path(url: str) -> str:
    encoded = quote(url, safe='')
    return os.path.join('cache', f'{encoded}.html')


def fetch_boj(url: str, use_cache: bool = True) -> Tuple[str, bool]:
    ensure_cache_dir()
    cache_path = url_to_cache_path(url)

    if use_cache and os.path.isfile(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read(), True

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'Cookie': f'bojautologin={bojautologin};'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text

    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return html, False


def parse_status_page(html: str) -> Tuple[List[StatusItem], Optional[str]]:
    soup = BeautifulSoup(html, 'html.parser')

    rows = soup.select('table#status-table tbody tr')
    results: List[StatusItem] = []

    for tr in rows:
        tds = tr.find_all('td')
        if len(tds) < 9:
            continue

        # 제출 번호
        submission_id = tds[0].get_text(strip=True)

        # 아이디
        user_anchor = tds[1].find('a')
        user_id = user_anchor.get_text(strip=True) if user_anchor else tds[1].get_text(strip=True)

        # 문제 번호 (대회 표기: A, B, ...)
        problem_anchor = tds[2].find('a')
        problem_no = problem_anchor.get_text(strip=True) if problem_anchor else tds[2].get_text(strip=True)

        # 결과
        result_span = tds[3].find('span')
        result_text = result_span.get_text(strip=True) if result_span else tds[3].get_text(strip=True)

        # 메모리/시간
        memory_text = tds[4].get_text(strip=True)
        time_text = tds[5].get_text(strip=True)

        # 언어 + 소스 링크
        lang_cell = tds[6]
        lang_anchor = lang_cell.find('a')
        language = lang_anchor.get_text(strip=True) if lang_anchor else lang_cell.get_text(strip=True)
        source_href = None
        if lang_anchor and lang_anchor.has_attr('href') and lang_anchor['href'].startswith('/source/'):
            source_href = urljoin('https://www.acmicpc.net', lang_anchor['href'])
        else:
            # 혹시 첫 a가 언어가 아닐 수 있으니 /source/ 포함한 링크를 다시 탐색
            src_a = lang_cell.find('a', href=True)
            if src_a and '/source/' in src_a['href']:
                source_href = urljoin('https://www.acmicpc.net', src_a['href'])

        # 코드 길이
        code_len_text = tds[7].get_text(strip=True)
        # code_len_text는 원본 그대로 두고, StatusItem.from_raw에서 정수화

        # 제출 시간 (절대시간은 title에 존재)
        time_anchor = tds[8].find('a')
        submitted_at = time_anchor.get('title') if time_anchor and time_anchor.has_attr('title') else tds[8].get_text(strip=True)

        item = StatusItem.from_raw(
            submission_id=submission_id,
            user_id=user_id,
            problem_no=problem_no,
            result=result_text,
            memory_text=memory_text,
            time_text=time_text,
            language=language,
            source_url=source_href,
            code_len_text=code_len_text,
            submitted_at=submitted_at,
        )

        results.append(item)

    # 다음 페이지 링크
    next_a = soup.select_one('a#next_page')
    next_url = urljoin('https://www.acmicpc.net', next_a['href']) if next_a and next_a.has_attr('href') else None

    return results, next_url


def crawl_status(start_url: str, output_jsonl: str = 'status.jsonl', max_pages: Optional[int] = None, use_cache: bool = True, show_progress: bool = True) -> None:
    visited = set()
    current_url: Optional[str] = start_url
    total_records = 0
    started_at = time.time()

    with open(output_jsonl, 'w', encoding='utf-8') as out:
        page_count = 0
        while current_url:
            if current_url in visited:
                break
            visited.add(current_url)

            if show_progress:
                print(f"[crawl] page={page_count + 1} url={current_url}")

            html, from_cache = fetch_boj(current_url, use_cache=use_cache)
            if show_progress:
                src = 'cache' if from_cache else 'web'
                print(f"[fetch] source={src}")
            records, next_url = parse_status_page(html)

            for rec in records:
                out.write(json.dumps(rec.to_json_dict(), ensure_ascii=False) + '\n')
            total_records += len(records)

            if show_progress:
                elapsed = time.time() - started_at
                print(f"[parse] records={len(records)} total={total_records} elapsed={elapsed:.2f}s")

            page_count += 1
            if max_pages is not None and page_count >= max_pages:
                break

            current_url = next_url
            if current_url:
                time.sleep(0.5)
                if show_progress:
                    print(f"[next] url={current_url}")
            else:
                if show_progress:
                    print("[done] no more pages")

if __name__ == "__main__":
    # 시작 URL
    start_url = 'https://www.acmicpc.net/status?contest_id=1378'

    # 테스트용: 현재 페이지를 캐시에 저장하고 전체 페이지를 순회하며 JSONL 작성
    # 캐시 파일명: cache/<주소.html> (URL 전체를 퍼센트 인코딩 후 .html 확장자)
    crawl_status(start_url=start_url, output_jsonl='status.jsonl', max_pages=None, use_cache=True)
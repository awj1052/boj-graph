import os
import json
import time
import requests
import dotenv
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from domain import Submission


class CacheStrategy(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str):
        pass


class FileCacheStrategy(CacheStrategy):
    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, url: str) -> str:
        encoded = quote(url, safe='')
        return os.path.join(self.cache_dir, f'{encoded}.html')

    def get(self, key: str) -> Optional[str]:
        cache_path = self._get_cache_path(key)
        if os.path.isfile(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def set(self, key: str, value: str):
        cache_path = self._get_cache_path(key)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(value)


class NoCacheStrategy(CacheStrategy):
    def get(self, key: str) -> Optional[str]:
        return None

    def set(self, key: str, value: str):
        pass


class HttpClient:
    def __init__(self, bojautologin: str, cache_strategy: CacheStrategy):
        self.bojautologin = bojautologin
        self.cache_strategy = cache_strategy

    def fetch(self, url: str) -> Tuple[str, bool]:
        cached = self.cache_strategy.get(url)
        if cached:
            return cached, True

        if not self.bojautologin:
            raise ValueError("BOJ_AUTO_LOGIN cookie is required")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'bojautologin={self.bojautologin};'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

        self.cache_strategy.set(url, html)
        return html, False


class StatusPageParser:
    @staticmethod
    def parse(html: str) -> Tuple[List[Submission], Optional[str]]:
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.select('table#status-table tbody tr')
        submissions = []

        for tr in rows:
            tds = tr.find_all('td')
            if len(tds) < 9:
                continue

            submission = StatusPageParser._parse_row(tds)
            if submission:
                submissions.append(submission)

        next_url = StatusPageParser._extract_next_url(soup)
        return submissions, next_url

    @staticmethod
    def _parse_row(tds) -> Optional[Submission]:
        try:
            submission_id = tds[0].get_text(strip=True)

            user_anchor = tds[1].find('a')
            user_id = user_anchor.get_text(strip=True) if user_anchor else tds[1].get_text(strip=True)

            problem_anchor = tds[2].find('a')
            problem_no = problem_anchor.get_text(strip=True) if problem_anchor else tds[2].get_text(strip=True)

            result_span = tds[3].find('span')
            result_text = result_span.get_text(strip=True) if result_span else tds[3].get_text(strip=True)

            memory_text = tds[4].get_text(strip=True)
            time_text = tds[5].get_text(strip=True)

            lang_cell = tds[6]
            lang_anchor = lang_cell.find('a')
            language = lang_anchor.get_text(strip=True) if lang_anchor else lang_cell.get_text(strip=True)

            source_url = StatusPageParser._extract_source_url(lang_cell)
            code_len_text = tds[7].get_text(strip=True)

            time_anchor = tds[8].find('a')
            submitted_at = time_anchor.get('title') if time_anchor and time_anchor.has_attr('title') else tds[8].get_text(strip=True)

            return Submission.from_raw(
                submission_id=submission_id,
                user_id=user_id,
                problem_no=problem_no,
                result=result_text,
                memory_text=memory_text,
                time_text=time_text,
                language=language,
                source_url=source_url,
                code_len_text=code_len_text,
                submitted_at=submitted_at
            )
        except Exception:
            return None

    @staticmethod
    def _extract_source_url(lang_cell) -> Optional[str]:
        lang_anchor = lang_cell.find('a')
        if lang_anchor and lang_anchor.has_attr('href') and lang_anchor['href'].startswith('/source/'):
            return urljoin('https://www.acmicpc.net', lang_anchor['href'])

        src_a = lang_cell.find('a', href=True)
        if src_a and '/source/' in src_a['href']:
            return urljoin('https://www.acmicpc.net', src_a['href'])
        return None

    @staticmethod
    def _extract_next_url(soup) -> Optional[str]:
        next_a = soup.select_one('a#next_page')
        if next_a and next_a.has_attr('href'):
            return urljoin('https://www.acmicpc.net', next_a['href'])
        return None


class BojCrawler:
    def __init__(self, http_client: HttpClient, parser: StatusPageParser):
        self.http_client = http_client
        self.parser = parser
        self.progress_callback: Optional[Callable[[str], None]] = None

    def set_progress_callback(self, callback: Callable[[str], None]):
        self.progress_callback = callback

    def _log(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)

    def crawl(self, start_url: str, output_path: str, max_pages: Optional[int] = None):
        visited = set()
        current_url = start_url
        total_records = 0
        started_at = time.time()

        with open(output_path, 'w', encoding='utf-8') as out:
            page_count = 0
            while current_url:
                if current_url in visited:
                    break
                visited.add(current_url)

                self._log(f"[페이지 {page_count + 1}] 크롤링 중: {current_url}")

                html, from_cache = self.http_client.fetch(current_url)
                source = 'cache' if from_cache else 'web'
                self._log(f"[가져오기] 소스: {source}")

                submissions, next_url = self.parser.parse(html)

                for submission in submissions:
                    out.write(json.dumps(submission.to_dict(), ensure_ascii=False) + '\n')
                total_records += len(submissions)

                elapsed = time.time() - started_at
                self._log(f"[파싱 완료] 레코드: {len(submissions)}개, 총: {total_records}개, 경과시간: {elapsed:.2f}초")

                page_count += 1
                if max_pages is not None and page_count >= max_pages:
                    self._log("[완료] 최대 페이지 수에 도달했습니다.")
                    break

                current_url = next_url
                if current_url:
                    time.sleep(0.5)
                else:
                    self._log("[완료] 모든 페이지 크롤링이 완료되었습니다.")


class CrawlerFactory:
    @staticmethod
    def create(bojautologin: Optional[str] = None, use_cache: bool = True) -> BojCrawler:
        if bojautologin is None:
            bojautologin = CrawlerFactory._load_from_env()

        if not bojautologin:
            raise ValueError("BOJ_AUTO_LOGIN 쿠키 값이 필요합니다.")

        cache_strategy = FileCacheStrategy() if use_cache else NoCacheStrategy()
        http_client = HttpClient(bojautologin, cache_strategy)
        parser = StatusPageParser()

        return BojCrawler(http_client, parser)

    @staticmethod
    def _load_from_env() -> Optional[str]:
        try:
            env_values = dotenv.dotenv_values('.env')
            return env_values.get('BOJ_AUTO_LOGIN', '')
        except:
            return None

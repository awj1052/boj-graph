## boj-graph

백준 온라인 저지(BOJ) 대회용 상태 페이지를 크롤링해 시간대별 제출 결과를 시각화하는 작은 도구 모음입니다.

- 대회 상태 페이지(예: `https://www.acmicpc.net/status?contest_id=XXXX`)를 수집해 `status.jsonl`로 저장
- 선택적으로 `status.csv`로 변환
- 문제별(예: A, B, C, ...) 시간 구간(기본 3분) 막대 그래프 이미지를 `images/status_*.png`로 생성
- 프리즈 구간 이후의 정답은 파란색(blue)으로 표시해 공개/프리즈 이후 결과를 구분

### 예시 산출물
- `images/status_A.png`, `images/status_B.png`, ... 가 생성됩니다. 저장된 샘플 이미지를 참고하세요.


## 기술 스택
- Python 3.9+ (권장 3.10+)
- Requests: 웹 요청
- BeautifulSoup4: HTML 파싱
- python-dotenv: `.env`에서 BOJ 쿠키 로드
- matplotlib: 그래프 생성
- 표준 라이브러리: `dataclasses`, `json`, `csv`, `datetime`, `collections`, `typing`

설치 예시:
```bash
pip install requests beautifulsoup4 python-dotenv matplotlib
```


## 설치 및 준비
1) 저장소 클론
```bash
git clone <this-repo>
cd boj-graph
```

2) Python 의존성 설치
```bash
pip install -r requirements.txt  # 파일이 없다면 아래 명령으로 대체
pip install requests beautifulsoup4 python-dotenv matplotlib
```

3) 로그인 쿠키 준비(.env)
- BOJ에 로그인한 뒤 브라우저 개발자 도구에서 `bojautologin` 쿠키 값을 확인합니다.
- 루트 디렉터리에 `.env` 파일을 만들어 다음과 같이 저장합니다:
```env
BOJ_AUTO_LOGIN=여기에_bojautologin_쿠키값
```

주의: 일부 대회의 상태 페이지는 로그인/권한이 필요합니다. 쿠키가 없거나 권한이 없으면 수집 결과가 비어 있거나 403이 발생할 수 있습니다.


## 사용 방법
### 1) 대회 상태 수집(JSONL 생성)
기본 예시(스크립트에 내장된 URL 사용):
```bash
python scrapping.py
```
- 기본 시작 URL: `https://www.acmicpc.net/status?contest_id=1378`
- 결과: `status.jsonl` 생성, 원본 HTML은 `cache/`에 저장(중복 요청 방지)

다른 대회를 수집하려면(파워셸/리눅스 공통 한 줄 예시):
```bash
python -c "from scrapping import crawl_status; crawl_status('https://www.acmicpc.net/status?contest_id=XXXX', output_jsonl='status.jsonl', max_pages=None, use_cache=True)"
```
- `max_pages`로 페이지 수를 제한할 수 있습니다(기본 무제한).

### 2) JSONL → CSV (선택)
```bash
python jsonl_to_csv.py status.jsonl --out status.csv
```
- 컬럼 선택 예시: `--fields submission_id,user_id,problem_no,result,submitted_at`
- 구분자 변경: `--delimiter ';'`

### 3) 그래프 생성
```bash
python make_graph.py status.jsonl \
  --start "2024-09-28 14:00:00" \
  --end   "2024-09-28 17:00:00" \
  --freeze "2024-09-28 16:30:00" \
  --minute 3 \
  --problems A,B,C,D,E,F,G,H,I,J,K,L,M,N,O
```
- `--start`, `--end`: 공통 x축 구간 지정(미지정 시 데이터로부터 추정)
- `--freeze`: 프리즈 시작 시각. 이후 정답은 파란색(blue)으로 표기
- `--minute`: 집계 간격(분)
- `--problems`: 이미지 생성할 문제 목록(쉼표 구분)
- 출력: `images/status_<문제>.png`

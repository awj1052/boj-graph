## boj-graph

<img width="1500" height="400" alt="status_C" src="https://github.com/user-attachments/assets/28ad9cc1-afb9-461f-891a-43ad8f0e9314" />

백준 온라인 저지(BOJ) 대회용 상태 페이지를 크롤링해 시간대별 제출 결과를 시각화하는 도구입니다.

- 대회 상태 페이지를 수집해 `status.jsonl`로 저장
- 선택적으로 `status.csv`로 변환
- 문제별 시간 구간 막대 그래프 이미지를 `images/status_*.png`로 생성
- 프리즈 구간 이후의 제출은 파란색으로 표시

## 기술 스택

- Python 3.9+
- Requests, BeautifulSoup4, python-dotenv, matplotlib, PyQt5

```bash
pip install -r requirements.txt
```

## 프로젝트 구조

```
boj-graph/
├── domain/              # 도메인 모델
│   └── models.py        # Submission, BinData
├── services/            # 비즈니스 로직
│   ├── crawler.py       # 크롤링 (Strategy 패턴)
│   ├── graph_builder.py # 그래프 생성 (Builder 패턴)
│   └── converter.py     # JSONL→CSV 변환
├── gui/                 # PyQt5 GUI
│   ├── main_window.py
│   └── widgets.py
├── cli/                 # CLI 진입점
│   ├── crawl.py
│   ├── graph.py
│   └── convert.py
└── main.py              # GUI 실행
```

## 설정

### BOJ 쿠키 설정

`.env` 파일 생성:

```env
BOJ_AUTO_LOGIN=your_bojautologin_cookie_value
```

BOJ에 로그인 후 브라우저 개발자 도구에서 `bojautologin` 쿠키 값을 확인하세요.

## 사용 방법

### GUI 실행

```bash
python main.py
```

GUI는 4개 탭으로 구성:
- **크롤링**: 대회 상태 페이지 수집
- **그래프 생성**: 문제별 시각화
- **CSV 변환**: JSONL을 CSV로 변환
- **이미지 뷰어**: 생성된 그래프 확인

### CLI 사용

#### 1. 크롤링

```bash
python cli/crawl.py https://www.acmicpc.net/status?contest_id=1379
```

옵션:
- `-o, --output`: 출력 파일 경로 (기본: status.jsonl)
- `-c, --cookie`: BOJ_AUTO_LOGIN 쿠키 값
- `-m, --max-pages`: 최대 페이지 수
- `--no-cache`: 캐시 사용 안 함

#### 2. 그래프 생성

```bash
python cli/graph.py status.jsonl \
  --start "2024-09-28 19:00:00" \
  --end "2024-09-28 22:00:00" \
  --freeze "2024-09-28 21:30:00" \
  --minute 3 \
  --problems A,B,C,D,E,F,G,H,I,J,K,L,M,N,O
```

옵션:
- `--start`: 시작 시간
- `--end`: 종료 시간
- `--freeze`: 프리즈 시작 시간
- `--minute`: 집계 간격 (분)
- `--problems`: 문제 목록 (쉼표 구분)
- `-o, --output-dir`: 출력 디렉터리 (기본: images)

#### 3. CSV 변환

```bash
python cli/convert.py status.jsonl -o status.csv
```

옵션:
- `-o, --output`: 출력 파일
- `--fields`: 포함할 필드 (쉼표 구분)
- `-d, --delimiter`: CSV 구분자

## 아키텍처

### 계층 구조
- **Domain Layer**: 비즈니스 엔티티 및 규칙
- **Service Layer**: 비즈니스 로직 및 조정
- **Presentation Layer**: GUI 및 CLI 인터페이스

### 의존성 방향
```
GUI/CLI → Services → Domain
```

## 디자인 패턴

### Strategy 패턴
크롤링 시 캐시 전략을 런타임에 선택 가능:
- `FileCacheStrategy`: 파일 기반 캐싱
- `NoCacheStrategy`: 캐시 사용 안 함

### Builder 패턴
그래프 생성 시 복잡한 설정을 체이닝으로 구성:

```python
GraphBuilder() \
    .with_submissions(submissions) \
    .with_time_range(start, end) \
    .with_freeze_time(freeze) \
    .with_minute_delta(3) \
    .with_output_path('graph.png') \
    .build()
```

### Factory 패턴
객체 생성을 팩토리로 캡슐화:

```python
crawler = CrawlerFactory.create(bojautologin, use_cache=True)
converter = ConverterFactory.create_jsonl_to_csv(input, output)
```

### Repository 패턴
데이터 접근 로직 추상화:

```python
submissions = SubmissionRepository.load_from_jsonl('status.jsonl')
grouped = SubmissionRepository.group_by_problem(submissions)
```

## 프로그래밍 방식 사용

### 크롤링 예제

```python
from services import CrawlerFactory

crawler = CrawlerFactory.create(bojautologin='your_cookie', use_cache=True)
crawler.set_progress_callback(lambda msg: print(msg))
crawler.crawl(
    start_url='https://www.acmicpc.net/status?contest_id=1379',
    output_path='status.jsonl',
    max_pages=None
)
```

### 그래프 생성 예제

```python
from services import GraphBuilder, SubmissionRepository
import os

os.makedirs('images', exist_ok=True)

submissions = SubmissionRepository.load_from_jsonl('status.jsonl')
grouped = SubmissionRepository.group_by_problem(submissions)

for problem_no, problem_submissions in grouped.items():
    GraphBuilder() \
        .with_submissions(problem_submissions) \
        .with_time_range('2024-09-28 19:00:00', '2024-09-28 22:00:00') \
        .with_freeze_time('2024-09-28 21:30:00') \
        .with_minute_delta(3) \
        .with_output_path(f'images/status_{problem_no}.png') \
        .build()
```

### CSV 변환 예제

```python
from services import ConverterFactory

converter = ConverterFactory.create_jsonl_to_csv(
    input_path='status.jsonl',
    output_path='status.csv',
    fields=['submission_id', 'user_id', 'problem_no', 'result', 'submitted_at'],
    delimiter=','
)
converter.convert()
```

## 주의사항

- 일부 대회 페이지는 로그인/권한이 필요합니다
- 쿠키가 없거나 권한이 없으면 403 또는 빈 결과가 발생할 수 있습니다
- 캐시는 `cache/` 디렉터리에 저장됩니다

## 라이선스

MIT

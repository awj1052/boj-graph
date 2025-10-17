# EXE 빌드 가이드

## 사전 준비

1. PyInstaller 설치:
```bash
pip install pyinstaller
```

## 빌드 방법

### 방법 1: spec 파일 사용 (권장)

```bash
pyinstaller boj_graph.spec
```

생성된 파일 위치: `dist/BOJ-Graph.exe`

### 방법 2: Python 스크립트 사용

```bash
python build_exe.py
```

### 방법 3: 직접 명령어 실행

```bash
pyinstaller main.py ^
    --name=BOJ-Graph ^
    --onefile ^
    --windowed ^
    --collect-all matplotlib ^
    --collect-all PyQt5 ^
    --hidden-import=PyQt5 ^
    --hidden-import=matplotlib ^
    --hidden-import=bs4 ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    --clean
```

## 빌드 옵션 설명

- `--name=BOJ-Graph`: 실행 파일 이름
- `--onefile`: 단일 실행 파일로 생성
- `--windowed`: 콘솔 창 숨김 (GUI만 표시)
- `--collect-all`: 모든 관련 파일 포함
- `--hidden-import`: 동적으로 import되는 모듈 명시
- `--clean`: 빌드 전 캐시 정리

## 주의사항

### 파일 크기
- 단일 실행 파일은 크기가 큽니다 (약 100-200MB)
- 모든 dependency가 포함되기 때문입니다

### .env 파일
- `.env` 파일은 EXE에 포함되지 않습니다
- EXE와 같은 디렉터리에 `.env` 파일을 배치하세요

### 바이러스 백신 경고
- 일부 백신 프로그램이 오진할 수 있습니다
- 이는 PyInstaller로 만든 실행 파일의 일반적인 현상입니다

## 배포

빌드 후 다음 파일들을 함께 배포:
```
BOJ-Graph.exe
.env.example  (사용자가 .env로 이름 변경)
README.md
```

## 테스트

빌드 후 다른 환경에서 테스트:
1. Python이 설치되지 않은 컴퓨터에서 실행
2. `.env` 파일 설정 확인
3. 모든 기능(크롤링, 그래프 생성, CSV 변환) 테스트

## 문제 해결

### 실행 파일이 실행되지 않음
```bash
pyinstaller --debug=all boj_graph.spec
```
디버그 모드로 빌드하여 오류 확인

### 특정 모듈이 누락됨
spec 파일의 `hiddenimports`에 모듈 추가

### 용량이 너무 큼
`--onedir` 옵션 사용 (폴더로 배포)
```bash
pyinstaller --onedir boj_graph.spec
```

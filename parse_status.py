
from bs4 import BeautifulSoup
import sys
import datetime

def parse_submission_status(html_content):
    """
    HTML content를 분석하여 가장 작은 제출 번호와 (제출 시간, 결과) 튜플 리스트를 반환합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # status-table ID를 가진 테이블 찾기
    status_table = soup.find('table', id='status-table')
    if not status_table:
        print("Error: <table id='status-table'> not found.", file=sys.stderr)
        return None, []

    # thead를 제외한 tbody의 tr들만 가져오기
    table_rows = status_table.select('tbody tr')
    
    results = []
    min_submission_id = float('inf')

    for row in table_rows:
        cells = row.find_all('td')
        
        # 각 row에 충분한 cell이 있는지 확인
        if len(cells) < 9:
            continue

        # 데이터 추출
        try:
            submission_id = int(cells[0].text.strip())
            # 결과 (채점 현황)
            result = cells[3].text.strip()
            # 제출한 시간 (data-timestamp 속성을 날짜/시간으로 변환)
            time_cell = cells[8]
            element_with_timestamp = time_cell.find(attrs={"data-timestamp": True})
            if element_with_timestamp:
                ts = int(element_with_timestamp['data-timestamp'])
                submission_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            else: # Fallback for other cases
                submission_time = time_cell.text.strip()

            # 가장 작은 제출 번호 업데이트
            if submission_id < min_submission_id:
                min_submission_id = submission_id
            
            results.append((submission_time, result))
        except (ValueError, TypeError, KeyError) as e:
            # 숫자 변환 오류, 태그/속성 부재 등의 경우 해당 row는 건너뜁니다.
            print(f"Skipping a row due to parsing error: {e}", file=sys.stderr)
            continue

    if min_submission_id == float('inf'):
        min_submission_id = None # 제출 내역이 하나도 없는 경우

    return min_submission_id, results

if __name__ == "__main__":
    file_path = 'test.html'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        min_id, analysis_results = parse_submission_status(html)
        
        if min_id is not None:
            print(f"가장 작은 제출 번호: {min_id}")
            print("--- 분석 결과 ---")
            for time, status in analysis_results:
                print(f"({time}, {status})")

    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


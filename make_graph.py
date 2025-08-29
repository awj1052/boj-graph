import os
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def parse_datetime(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')


def classify_result(result_text: str) -> str:
    if result_text == '맞았습니다!!':
        return 'green'
    if result_text in ('틀렸습니다', '출력 형식이 잘못되었습니다'):
        return 'red'
    if result_text == '시간 초과':
        return 'orange'
    if result_text in ('메모리 초과', '출력 초과', '런타임 에러', '컴파일 에러'):
        return 'dark_grey'
    return 'dark_grey'


def read_status_jsonl(path: str) -> List[Dict]:
    records: List[Dict] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(obj)
            except Exception:
                continue
    return records


def build_bins(records: List[Dict], minute_delta: int = 3, freeze_dt: Optional[datetime] = None) -> Tuple[Dict[datetime, Dict[str, int]], datetime, datetime]:
    binned = defaultdict(lambda: {'green': 0, 'red': 0, 'orange': 0, 'dark_grey': 0, 'blue': 0})
    times: List[datetime] = []

    for rec in records:
        try:
            dt = parse_datetime(rec.get('submitted_at', ''))
        except Exception:
            continue
        times.append(dt)
        bin_key = dt.replace(minute=(dt.minute // minute_delta) * minute_delta, second=0, microsecond=0)
        cat = classify_result(str(rec.get('result', '')))
        # 프리즈타임 이후의 맞았습니다!!는 blue로 표시
        if freeze_dt is not None and dt >= freeze_dt and cat == 'green':
            cat = 'blue'
        binned[bin_key][cat] += 1

    if not times:
        now = datetime.now()
        return binned, now, now

    start_time = min(times)
    end_time = max(times) + timedelta(minutes=minute_delta)
    return binned, start_time, end_time


def plot_bins_to_file(binned_data: Dict[datetime, Dict[str, int]], start_time: datetime, end_time: datetime, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(15, 4))
    fig.set_facecolor('#28343B')
    ax.set_facecolor('#28343B')

    sorted_bins = sorted(binned_data.items())

    max_positive_count = 0
    max_negative_count = 0
    for _, counts in sorted_bins:
        max_positive_count = max(max_positive_count, counts['green'] + counts['blue'])
        negative_sum = counts['red'] + counts['orange'] + counts['dark_grey']
        max_negative_count = max(max_negative_count, negative_sum)

    for time_bin, counts in sorted_bins:
        bar_width = timedelta(minutes=3)
        if counts['blue'] > 0:
            ax.bar(time_bin, counts['blue'], color='skyblue', width=bar_width, align='edge')
        if counts['green'] > 0:
            ax.bar(time_bin, counts['green'], color='lime', width=bar_width, align='edge')
        if counts['red'] > 0:
            ax.bar(time_bin, -counts['red'], color='red', width=bar_width, align='edge')
        if counts['orange'] > 0:
            ax.bar(time_bin, -counts['orange'], bottom=-counts['red'], color='orange', width=bar_width, align='edge')
        if counts['dark_grey'] > 0:
            bottom_position = -(counts['red'] + counts['orange'])
            ax.bar(time_bin, -counts['dark_grey'], bottom=bottom_position, color='dimgrey', width=bar_width, align='edge')

    ax.axhline(0, color='grey', linewidth=2.5)
    ax.set_ylim(-(max_negative_count + 1), max_positive_count + 1)
    if max_positive_count == 0 and max_negative_count == 0:
        ax.set_ylim(-3, 3)

    ax.set_xlim(start_time, end_time)

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    plt.tight_layout()
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    plt.savefig(out_path, transparent=True)
    plt.close(fig)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_path', nargs='?', default='status.jsonl')
    parser.add_argument('--start', help='공통 시작 시간 YYYY-MM-DD HH:MM:SS', default='2024-09-28 14:00:00')
    parser.add_argument('--end', help='공통 종료 시간 YYYY-MM-DD HH:MM:SS', default='2024-09-28 17:00:00')
    parser.add_argument('--freeze', help='프리즈 시작 시간 YYYY-MM-DD HH:MM:SS', default='2024-09-28 16:30:00')
    parser.add_argument('--minute', type=int, default=3, help='집계 간격(분)')
    parser.add_argument('--problems', help='생성할 문제 번호 목록(쉼표 구분, 예: A,B,C)', default='A,B,C,D,E,F,G,H,I,J,K,L,M,N,O')
    args = parser.parse_args()

    in_path = args.in_path
    minute_delta = args.minute

    ensure_dir('images')

    all_records = read_status_jsonl(in_path)

    # 전역 시간 범위 계산
    all_times: List[datetime] = []
    for rec in all_records:
        try:
            all_times.append(parse_datetime(str(rec.get('submitted_at', ''))))
        except Exception:
            continue

    if args.start:
        global_start = parse_datetime(args.start)
    else:
        global_start = min(all_times) if all_times else datetime.now()

    if args.end:
        global_end = parse_datetime(args.end)
    else:
        global_end = (max(all_times) + timedelta(minutes=minute_delta)) if all_times else (global_start + timedelta(minutes=minute_delta))

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for rec in all_records:
        prob = str(rec.get('problem_no', ''))
        if not prob:
            continue
        grouped[prob].append(rec)

    # 대상 문제 목록 결정: 지정된 경우 그것만, 아니면 데이터에 존재하는 문제 전부
    if args.problems:
        target_problems = [p.strip() for p in args.problems.split(',') if p.strip()]
    else:
        target_problems = list(grouped.keys())

    # 프리즈타임 파싱
    freeze_dt: Optional[datetime] = None
    if args.freeze:
        try:
            freeze_dt = parse_datetime(args.freeze)
        except Exception:
            freeze_dt = None

    for problem_no in target_problems:
        records = grouped.get(problem_no, [])
        binned, _start_unused, _end_unused = build_bins(records, minute_delta=minute_delta, freeze_dt=freeze_dt)
        safe_name = problem_no.replace('/', '_')
        out_path = os.path.join('images', f'status_{safe_name}.png')
        plot_bins_to_file(binned, global_start, global_end, out_path)


if __name__ == '__main__':
    main()
import os
import json
import csv


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


DEFAULT_FIELDS = [
    'submission_id',
    'user_id',
    'problem_no',
    'result',
    'memory_kb',
    'time_ms',
    'language',
    'source_url',
    'code_length',
    'submitted_at',
]


def read_jsonl(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def to_str(value):
    if value is None:
        return ''
    return str(value)


def convert_jsonl_to_csv(in_path: str, out_path: str, fields=None, delimiter: str = ',') -> None:
    if fields is None:
        fields = DEFAULT_FIELDS
    ensure_parent_dir(out_path)
    # Windows에서 CSV 줄바꿈 문제 방지: newline=''
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter)
        writer.writerow(fields)
        for obj in read_jsonl(in_path):
            row = [to_str(obj.get(col)) for col in fields]
            writer.writerow(row)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_path', nargs='?', default='status.jsonl', help='입력 JSONL 경로')
    parser.add_argument('--out', default='status.csv', help='출력 CSV 경로')
    parser.add_argument('--fields', default=','.join(DEFAULT_FIELDS), help='CSV 컬럼 목록(쉼표 구분)')
    parser.add_argument('--delimiter', default=',', help='CSV 구분자')
    args = parser.parse_args()

    fields = [c.strip() for c in args.fields.split(',') if c.strip()]
    convert_jsonl_to_csv(args.in_path, args.out, fields=fields, delimiter=args.delimiter)


if __name__ == '__main__':
    main()



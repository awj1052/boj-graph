import argparse
import os
from services import GraphBuilder, SubmissionRepository


def main():
    parser = argparse.ArgumentParser(description='BOJ Graph Generator')
    parser.add_argument('input', nargs='?', default='status.jsonl', help='Input JSONL file')
    parser.add_argument('--start', default='2024-09-28 19:00:00', help='Start time')
    parser.add_argument('--end', default='2024-09-28 22:00:00', help='End time')
    parser.add_argument('--freeze', default='2024-09-28 21:30:00', help='Freeze time')
    parser.add_argument('--minute', type=int, default=3, help='Minute delta')
    parser.add_argument('--problems', default='A,B,C,D,E,F,G,H,I,J,K,L,M,N,O', help='Problem list')
    parser.add_argument('-o', '--output-dir', default='images', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    all_submissions = SubmissionRepository.load_from_jsonl(args.input)
    grouped = SubmissionRepository.group_by_problem(all_submissions)

    problems = [p.strip() for p in args.problems.split(',') if p.strip()]

    for problem_no in problems:
        if problem_no not in grouped:
            continue

        print(f"Generating graph for problem {problem_no}...")

        submissions = grouped[problem_no]
        safe_name = problem_no.replace('/', '_')
        output_path = os.path.join(args.output_dir, f'status_{safe_name}.png')

        GraphBuilder() \
            .with_submissions(submissions) \
            .with_time_range(args.start, args.end) \
            .with_freeze_time(args.freeze) \
            .with_minute_delta(args.minute) \
            .with_output_path(output_path) \
            .build()

    print("Graph generation completed")


if __name__ == '__main__':
    main()

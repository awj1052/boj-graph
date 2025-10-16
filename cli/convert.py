import argparse
from services import ConverterFactory


def main():
    parser = argparse.ArgumentParser(description='JSONL to CSV Converter')
    parser.add_argument('input', nargs='?', default='status.jsonl', help='Input JSONL file')
    parser.add_argument('-o', '--output', default='status.csv', help='Output CSV file')
    parser.add_argument('--fields', help='Comma-separated field names')
    parser.add_argument('-d', '--delimiter', default=',', help='CSV delimiter')
    args = parser.parse_args()

    fields = None
    if args.fields:
        fields = [f.strip() for f in args.fields.split(',') if f.strip()]

    converter = ConverterFactory.create_jsonl_to_csv(
        args.input,
        args.output,
        fields,
        args.delimiter
    )
    converter.convert()

    print(f"Conversion completed: {args.output}")


if __name__ == '__main__':
    main()

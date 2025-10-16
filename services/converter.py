import os
import json
import csv
from typing import List, Optional, Generator, Any


class JsonlReader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read(self) -> Generator[dict, None, None]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue


class CsvWriter:
    DEFAULT_FIELDS = [
        'submission_id', 'user_id', 'problem_no', 'result',
        'memory_kb', 'time_ms', 'language', 'source_url',
        'code_length', 'submitted_at'
    ]

    def __init__(self, file_path: str, fields: Optional[List[str]] = None, delimiter: str = ','):
        self.file_path = file_path
        self.fields = fields or self.DEFAULT_FIELDS
        self.delimiter = delimiter

    def write(self, data: Generator[dict, None, None]):
        self._ensure_parent_dir()

        with open(self.file_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=self.delimiter)
            writer.writerow(self.fields)

            for record in data:
                row = [self._to_str(record.get(field)) for field in self.fields]
                writer.writerow(row)

    def _ensure_parent_dir(self):
        parent = os.path.dirname(os.path.abspath(self.file_path))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)

    @staticmethod
    def _to_str(value: Any) -> str:
        return '' if value is None else str(value)


class FileConverter:
    def __init__(self, reader: JsonlReader, writer: CsvWriter):
        self.reader = reader
        self.writer = writer

    def convert(self):
        data = self.reader.read()
        self.writer.write(data)


class ConverterFactory:
    @staticmethod
    def create_jsonl_to_csv(input_path: str, output_path: str,
                           fields: Optional[List[str]] = None,
                           delimiter: str = ',') -> FileConverter:
        reader = JsonlReader(input_path)
        writer = CsvWriter(output_path, fields, delimiter)
        return FileConverter(reader, writer)

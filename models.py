from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal, ClassVar, Set, Union


def _only_digits_to_int_or_none(text: str) -> Optional[int]:
    if text is None:
        return None
    digits = ''.join(ch for ch in str(text) if ch.isdigit())
    return int(digits) if digits else None


@dataclass
class StatusItem:
    submission_id: int
    user_id: str
    problem_no: str
    result: Union[Literal[
        '맞았습니다!!',
        '틀렸습니다',
        '시간 초과',
        '메모리 초과',
        '출력 초과',
        '출력 형식이 잘못되었습니다',
        '런타임 에러',
        '컴파일 에러',
    ], str]
    memory_kb: Optional[int]
    time_ms: Optional[int]
    language: Union[Literal[
        'PyPy3',
        'C++20',
        'Rust 2021',
        'Python 3',
        'C#',
        'Java 15',
        'Assembly (64bit)',
        'Fortran',
        'C99',
        'Ruby',
        'Kotlin (JVM)',
        'Swift',
        'Text',
        'node.js',
        'Go',
        'D',
        'C++17 (Clang)',
        'OCaml',
        # 아래는 상태 테이블에서 자주 보이는 표기 추가
        'C++17',
        'Java 8',
        'Java 11',
    ], str]
    source_url: Optional[str]
    code_length: int
    submitted_at: str

    ALLOWED_RESULTS: ClassVar[Set[str]] = {
        '맞았습니다!!',
        '틀렸습니다',
        '시간 초과',
        '메모리 초과',
        '출력 초과',
        '출력 형식이 잘못되었습니다',
        '런타임 에러',
        '컴파일 에러',
    }

    ALLOWED_LANGUAGES: ClassVar[Set[str]] = {
        'PyPy3', 'C++20', 'Rust 2021', 'Python 3', 'C#', 'Java 15',
        'Assembly (64bit)', 'Fortran', 'C99', 'Ruby', 'Kotlin (JVM)', 'Swift',
        'Text', 'node.js', 'Go', 'D', 'C++17 (Clang)', 'OCaml',
        'C++17', 'Java 8', 'Java 11',
    }

    @classmethod
    def from_raw(
        cls,
        *,
        submission_id: str,
        user_id: str,
        problem_no: str,
        result: str,
        memory_text: str,
        time_text: str,
        language: str,
        source_url: Optional[str],
        code_len_text: str,
        submitted_at: str,
    ) -> "StatusItem":
        sub_id_int = _only_digits_to_int_or_none(submission_id)
        if sub_id_int is None:
            raise ValueError(f"Invalid submission_id: {submission_id}")

        memory_kb = _only_digits_to_int_or_none(memory_text)
        time_ms = _only_digits_to_int_or_none(time_text)
        code_length = _only_digits_to_int_or_none(code_len_text) or 0

        result_clean = str(result or "")

        language_clean = str(language or "")

        return cls(
            submission_id=sub_id_int,
            user_id=str(user_id or ""),
            problem_no=str(problem_no or ""),
            result=result_clean,
            memory_kb=memory_kb,
            time_ms=time_ms,
            language=language_clean,
            source_url=source_url if source_url else None,
            code_length=code_length,
            submitted_at=str(submitted_at or ""),
        )

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            'submission_id': self.submission_id,
            'user_id': self.user_id,
            'problem_no': self.problem_no,
            'result': self.result,
            'memory_kb': self.memory_kb,
            'time_ms': self.time_ms,
            'language': self.language,
            'source_url': self.source_url,
            'code_length': self.code_length,
            'submitted_at': self.submitted_at,
        }



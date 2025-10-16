import os
from datetime import datetime, timedelta
from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QFormLayout, QSpinBox,
    QCheckBox, QMessageBox, QFileDialog, QComboBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

from services import CrawlerFactory, GraphBuilder, SubmissionRepository, ConverterFactory


class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, task_fn):
        super().__init__()
        self.task_fn = task_fn

    def run(self):
        try:
            self.task_fn(self.progress.emit)
            self.finished.emit(True, "작업이 완료되었습니다.")
        except Exception as e:
            self.finished.emit(False, f"작업 중 오류가 발생했습니다: {str(e)}")


class CrawlerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: Optional[WorkerThread] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        settings_group = self._create_settings_group()
        layout.addWidget(settings_group)

        crawl_button = QPushButton("크롤링 시작")
        crawl_button.clicked.connect(self._start_crawling)
        layout.addWidget(crawl_button)

        layout.addWidget(QLabel("진행 상황:"))
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(200)
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)

    def _create_settings_group(self) -> QGroupBox:
        group = QGroupBox("크롤링 설정")
        layout = QFormLayout(group)

        self.bojautologin_input = QLineEdit()
        self.bojautologin_input.setPlaceholderText("BOJ 자동 로그인 쿠키 값 (비어있으면 .env에서 로드)")
        self.bojautologin_input.setEchoMode(QLineEdit.Password)

        self.url_input = QLineEdit("https://www.acmicpc.net/status?contest_id=1379")
        self.output_input = QLineEdit("status.jsonl")

        self.max_pages_input = QSpinBox()
        self.max_pages_input.setMaximum(9999)
        self.max_pages_input.setValue(0)
        self.max_pages_input.setSpecialValueText("무제한")

        self.use_cache_checkbox = QCheckBox("캐시 사용")
        self.use_cache_checkbox.setChecked(True)

        layout.addRow("BOJ 쿠키:", self.bojautologin_input)
        layout.addRow("대회 URL:", self.url_input)
        layout.addRow("출력 파일:", self.output_input)
        layout.addRow("최대 페이지:", self.max_pages_input)
        layout.addRow("", self.use_cache_checkbox)

        return group

    def _start_crawling(self):
        url = self.url_input.text().strip()
        output_file = self.output_input.text().strip()
        bojautologin = self.bojautologin_input.text().strip() or None
        max_pages = self.max_pages_input.value() if self.max_pages_input.value() > 0 else None
        use_cache = self.use_cache_checkbox.isChecked()

        if not url:
            QMessageBox.warning(self, "경고", "URL을 입력해주세요.")
            return
        if not output_file:
            QMessageBox.warning(self, "경고", "출력 파일명을 입력해주세요.")
            return

        self.progress_text.clear()
        self.progress_text.append("크롤링을 시작합니다...")

        def task(progress_callback):
            crawler = CrawlerFactory.create(bojautologin, use_cache)
            crawler.set_progress_callback(progress_callback)
            crawler.crawl(url, output_file, max_pages)

        self.worker = WorkerThread(task)
        self.worker.progress.connect(self.progress_text.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success: bool, message: str):
        self.progress_text.append(message)
        if success:
            QMessageBox.information(self, "완료", message)
        else:
            QMessageBox.critical(self, "오류", message)


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: Optional[WorkerThread] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        file_group = self._create_file_group()
        layout.addWidget(file_group)

        time_group = self._create_time_group()
        layout.addWidget(time_group)

        problem_group = self._create_problem_group()
        layout.addWidget(problem_group)

        graph_button = QPushButton("그래프 생성")
        graph_button.clicked.connect(self._start_graph_generation)
        layout.addWidget(graph_button)

        layout.addWidget(QLabel("진행 상황:"))
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(200)
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)

    def _create_file_group(self) -> QGroupBox:
        group = QGroupBox("입력 파일")
        layout = QHBoxLayout(group)

        self.input_file = QLineEdit("status.jsonl")
        browse_button = QPushButton("찾아보기")
        browse_button.clicked.connect(self._browse_file)

        layout.addWidget(self.input_file)
        layout.addWidget(browse_button)

        return group

    def _create_time_group(self) -> QGroupBox:
        group = QGroupBox("시간 설정")
        layout = QFormLayout(group)

        self.start_time_input = QLineEdit("2024-09-28 19:00:00")
        self.end_time_input = QLineEdit("2024-09-28 22:00:00")
        self.freeze_time_input = QLineEdit("2024-09-28 21:30:00")

        self.minute_delta_input = QSpinBox()
        self.minute_delta_input.setMinimum(1)
        self.minute_delta_input.setMaximum(60)
        self.minute_delta_input.setValue(3)

        auto_detect_button = QPushButton("데이터에서 시간 자동 감지")
        auto_detect_button.clicked.connect(self._auto_detect_time_range)

        layout.addRow("시작 시간:", self.start_time_input)
        layout.addRow("종료 시간:", self.end_time_input)
        layout.addRow("프리즈 시간:", self.freeze_time_input)
        layout.addRow("집계 간격(분):", self.minute_delta_input)
        layout.addRow("", auto_detect_button)

        return group

    def _create_problem_group(self) -> QGroupBox:
        group = QGroupBox("문제 설정")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("문제 목록 (쉼표로 구분):"))
        self.problems_input = QLineEdit("A,B,C,D,E,F,G,H,I,J,K,L,M,N,O")
        layout.addWidget(self.problems_input)

        return group

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "JSONL 파일 선택", "", "JSONL files (*.jsonl);;All files (*.*)"
        )
        if file_path:
            self.input_file.setText(file_path)

    def _auto_detect_time_range(self):
        input_file = self.input_file.text().strip()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.warning(self, "경고", "입력 파일이 존재하지 않습니다.")
            return

        try:
            submissions = SubmissionRepository.load_from_jsonl(input_file)
            if not submissions:
                QMessageBox.warning(self, "경고", "JSONL 파일에 데이터가 없습니다.")
                return

            all_times = []
            for submission in submissions:
                try:
                    dt = datetime.strptime(submission.submitted_at, '%Y-%m-%d %H:%M:%S')
                    all_times.append(dt)
                except:
                    continue

            if not all_times:
                QMessageBox.warning(self, "경고", "유효한 시간 데이터가 없습니다.")
                return

            min_time = min(all_times)
            max_time = max(all_times)

            start_time = min_time.replace(minute=0, second=0, microsecond=0)
            if min_time.minute >= 30:
                start_time = start_time.replace(hour=min_time.hour)
            else:
                start_time = start_time.replace(hour=max(0, min_time.hour - 1))

            end_hour = max_time.hour + 1 if max_time.minute > 0 or max_time.second > 0 else max_time.hour
            end_time = max_time.replace(hour=min(23, end_hour), minute=0, second=0, microsecond=0)
            if end_hour > 23:
                end_time = end_time + timedelta(days=1)

            total_hours = (end_time - start_time).total_seconds() / 3600
            freeze_time = end_time - timedelta(minutes=30) if total_hours >= 1 else None

            self.start_time_input.setText(start_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.end_time_input.setText(end_time.strftime('%Y-%m-%d %H:%M:%S'))
            if freeze_time:
                self.freeze_time_input.setText(freeze_time.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                self.freeze_time_input.setText('')

            message = f"시간 범위를 자동으로 감지했습니다.\n시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n종료: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            if freeze_time:
                message += f"\n프리즈: {freeze_time.strftime('%Y-%m-%d %H:%M:%S')}"

            QMessageBox.information(self, "완료", message)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"시간 감지 중 오류가 발생했습니다: {str(e)}")

    def _start_graph_generation(self):
        input_file = self.input_file.text().strip()
        start_time = self.start_time_input.text().strip()
        end_time = self.end_time_input.text().strip()
        freeze_time = self.freeze_time_input.text().strip()
        minute_delta = self.minute_delta_input.value()
        problems_text = self.problems_input.text().strip()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.warning(self, "경고", "입력 파일이 존재하지 않습니다.")
            return
        if not problems_text:
            QMessageBox.warning(self, "경고", "문제 목록을 입력해주세요.")
            return

        problems = [p.strip() for p in problems_text.split(',') if p.strip()]

        self.progress_text.clear()
        self.progress_text.append("그래프 생성을 시작합니다...")

        def task(progress_callback):
            os.makedirs('images', exist_ok=True)
            progress_callback("JSONL 파일을 읽는 중...")

            all_submissions = SubmissionRepository.load_from_jsonl(input_file)
            grouped = SubmissionRepository.group_by_problem(all_submissions)

            generated = 0
            for problem_no in problems:
                if problem_no not in grouped:
                    continue

                progress_callback(f"문제 {problem_no} 그래프 생성 중...")
                submissions = grouped[problem_no]

                safe_name = problem_no.replace('/', '_')
                output_path = os.path.join('images', f'status_{safe_name}.png')

                GraphBuilder() \
                    .with_submissions(submissions) \
                    .with_time_range(start_time, end_time) \
                    .with_freeze_time(freeze_time) \
                    .with_minute_delta(minute_delta) \
                    .with_output_path(output_path) \
                    .build()

                generated += 1

            if generated == 0:
                raise ValueError("생성된 그래프가 없습니다.")

        self.worker = WorkerThread(task)
        self.worker.progress.connect(self.progress_text.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success: bool, message: str):
        self.progress_text.append(message)
        if success:
            QMessageBox.information(self, "완료", message)
        else:
            QMessageBox.critical(self, "오류", message)


class ConverterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        file_group = self._create_file_group()
        layout.addWidget(file_group)

        field_group = self._create_field_group()
        layout.addWidget(field_group)

        convert_button = QPushButton("CSV로 변환")
        convert_button.clicked.connect(self._convert_to_csv)
        layout.addWidget(convert_button)

        layout.addWidget(QLabel("변환 결과:"))
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def _create_file_group(self) -> QGroupBox:
        group = QGroupBox("파일 설정")
        layout = QFormLayout(group)

        self.convert_input = QLineEdit("status.jsonl")
        self.convert_output = QLineEdit("status.csv")

        self.convert_delimiter = QComboBox()
        self.convert_delimiter.addItems([",", ";", "\t"])

        layout.addRow("입력 JSONL:", self.convert_input)
        layout.addRow("출력 CSV:", self.convert_output)
        layout.addRow("구분자:", self.convert_delimiter)

        return group

    def _create_field_group(self) -> QGroupBox:
        group = QGroupBox("필드 설정")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("포함할 필드 (쉼표로 구분):"))
        self.fields_input = QLineEdit(
            "submission_id,user_id,problem_no,result,memory_kb,time_ms,language,source_url,code_length,submitted_at"
        )
        layout.addWidget(self.fields_input)

        return group

    def _convert_to_csv(self):
        input_file = self.convert_input.text().strip()
        output_file = self.convert_output.text().strip()
        delimiter = self.convert_delimiter.currentText()
        fields_text = self.fields_input.text().strip()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.warning(self, "경고", "입력 파일이 존재하지 않습니다.")
            return
        if not output_file:
            QMessageBox.warning(self, "경고", "출력 파일명을 입력해주세요.")
            return

        fields = [f.strip() for f in fields_text.split(',') if f.strip()] if fields_text else None

        try:
            converter = ConverterFactory.create_jsonl_to_csv(input_file, output_file, fields, delimiter)
            converter.convert()

            message = f"CSV 변환 완료: {output_file}"
            self.result_text.setText(message)
            QMessageBox.information(self, "완료", message)
        except Exception as e:
            error_msg = f"CSV 변환 중 오류가 발생했습니다: {str(e)}"
            self.result_text.setText(error_msg)
            QMessageBox.critical(self, "오류", error_msg)


class ViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("이미지:"))

        self.image_combo = QComboBox()
        self.refresh_images()
        select_layout.addWidget(self.image_combo)

        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh_images)
        select_layout.addWidget(refresh_button)

        layout.addLayout(select_layout)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(600, 200)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.image_label)

        view_button = QPushButton("이미지 보기")
        view_button.clicked.connect(self._view_image)
        layout.addWidget(view_button)

    def refresh_images(self):
        self.image_combo.clear()
        if os.path.exists('images'):
            for filename in os.listdir('images'):
                if filename.endswith('.png'):
                    self.image_combo.addItem(filename)

    def _view_image(self):
        if self.image_combo.count() == 0:
            QMessageBox.information(self, "정보", "표시할 이미지가 없습니다.")
            return

        filename = self.image_combo.currentText()
        if not filename:
            return

        image_path = os.path.join('images', filename)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("이미지를 로드할 수 없습니다.")
        else:
            self.image_label.setText("이미지 파일이 없습니다.")

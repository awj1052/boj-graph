import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtGui import QFont

from .widgets import CrawlerWidget, GraphWidget, ConverterWidget, ViewerWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('BOJ Graph Tool')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        tab_widget.addTab(CrawlerWidget(), "크롤링")
        tab_widget.addTab(GraphWidget(), "그래프 생성")
        tab_widget.addTab(ConverterWidget(), "CSV 변환")
        tab_widget.addTab(ViewerWidget(), "이미지 뷰어")


def run_gui():
    app = QApplication(sys.argv)

    font = QFont()
    font.setPointSize(9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

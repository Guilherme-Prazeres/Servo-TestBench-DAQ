import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi
from pathlib import Path

from core.com_controller import COMController
from core.manual_controller import ManualController
from core.telemetry_controller import TelemetryController
from core.graph_controller import GraphController
from core.test_controller import TestController
from core.state_controller import StateController

# --- PyInstaller Path Fix ---
def get_base_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as compiled executable
        return Path(sys._MEIPASS)
    else:
        # Running as a normal Python script
        return Path(__file__).resolve().parent

MAIN_DIR = get_base_path()
UI_DIR = MAIN_DIR / "UI"

class AppWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_file_path = str(UI_DIR / "BEST_mainUI.ui")
        loadUi(ui_file_path, self)
        
        self.setFixedSize(1280, 720)

        self.state_controller = StateController()
        self.com_controller = COMController(self, self.state_controller)

        self.manual_controller = ManualController(self, self.com_controller)
        self.graph_controller = GraphController(self, self.state_controller)
        self.telemetry_controller = TelemetryController(self, self.com_controller, self.graph_controller, self.state_controller)
        self.test_controller = TestController(self, self.com_controller)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
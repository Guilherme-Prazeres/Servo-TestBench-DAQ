import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from UI.BEST_mainUI import Ui_MainWindow
from core.com_controller import COMController
from core.manual_controller import ManualController
from core.telemetry_controller import TelemetryController
from core.graph_controller import GraphController

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.com_controller = COMController(self.ui)
        self.manual_controller = ManualController(self.ui, self.com_controller)
        self.graph_controller = GraphController(self.ui)
        self.telemetry_controller = TelemetryController(self.ui, self.com_controller, self.graph_controller)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
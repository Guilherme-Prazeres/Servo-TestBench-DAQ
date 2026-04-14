import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

# Create a separate class for the signals
class SerialSignals(QObject):
    # This signal will carry the string data received from the Arduino
    data_received = pyqtSignal(str)

class COMController:
    def __init__(self, ui):
        self.ui = ui
        self.serial_connection = None
        self.signals = SerialSignals()
        
        self.ui.COM_disconnect_button.setEnabled(False)
        self.update_ports()
        
        self.ui.COM_refresh_button.clicked.connect(self.update_ports)
        
        self.ui.COM_connect_button.clicked.connect(self.connect)
        self.ui.COM_disconnect_button.clicked.connect(self.disconnect)

        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_serial_data)

    def update_ports(self):
        self.ui.COM_port_ComboBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.COM_port_ComboBox.addItem(port.device)

    def update_ports(self):
        self.ui.COM_port_ComboBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.COM_port_ComboBox.addItem(port.device)

    def connect(self):
        port = self.ui.COM_port_ComboBox.currentText()
        if not port:
            return
        
        try:
            self.serial_connection = serial.Serial(port, 115200, timeout=0) # timeout=0 for non-blocking read
            self.ui.COM_connect_button.setText("Connected")
            self.ui.COM_connect_button.setEnabled(False)
            self.ui.COM_disconnect_button.setEnabled(True)
            self.ui.COM_port_ComboBox.setEnabled(False)
            
            # Start checking for data every 20 milliseconds (50Hz)
            self.read_timer.start(20)
            
        except serial.SerialException as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"Erro ao conectar: {str(e)}")
            msg.setWindowTitle("Erro de Conexão")
            msg.exec()

    def disconnect(self):
        self.read_timer.stop() # Stop reading
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        self.ui.COM_connect_button.setText("Conectar")
        self.ui.COM_connect_button.setEnabled(True)
        self.ui.COM_disconnect_button.setEnabled(False)
        self.ui.COM_port_ComboBox.setEnabled(True)

    def send_command(self, command):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                formatted_message = f"{command}\n"
                self.serial_connection.write(formatted_message.encode('utf-8'))
            except Exception as e:
                print(f"Erro ao enviar dado: {e}")

    def read_serial_data(self):
        """Reads incoming data from Arduino and emits a signal line by line."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                # Read all available lines in the buffer
                while self.serial_connection.in_waiting > 0:
                    # Read line and decode. We use errors='ignore' to prevent crashes on corrupted bytes
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        # Broadcast the received line to anyone listening
                        self.signals.data_received.emit(line)
            except Exception as e:
                print(f"Erro ao ler serial: {e}")
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

class COMController:
    """"Lida com a comunicação com a maquina"""
    def __init__(self, ui, state_controller):
        self.ui = ui
        self.state_controller = state_controller
        self.serial_connection = None
        
        self.ui.COM_disconnect_button.setEnabled(False)
        self.update_ports()
        
        self.ui.COM_refresh_button.clicked.connect(self.update_ports)
        self.ui.COM_connect_button.clicked.connect(self.connect)
        self.ui.COM_disconnect_button.clicked.connect(self.disconnect)


        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_serial_data)

        self.handshake_timer = QTimer()
        self.handshake_timer.timeout.connect(self.send_handshake)
        
        # Listen to the StateController to update the UI buttons and timers
        self.state_controller.state_changed.connect(self.handle_init_COM)

    def handle_init_COM(self, new_state):
        """Reacts to state changes to manage UI and timers."""
        if new_state == "ACK_CONNECT":
            self.handshake_timer.stop()
            
        elif new_state == "INIT_BEGIN":
            self.ui.COM_connect_button.setText("Inicializando...")
            # Set background to yellow and text to black
            self.ui.COM_connect_button.setStyleSheet("background-color: yellow; color: black;")
            
        elif new_state == "INIT_COMPLETE":
            self.ui.COM_connect_button.setText("Rodando")
            # Set background to green and text to white
            self.ui.COM_connect_button.setStyleSheet("background-color: green; color: white;")
            self.send_command("RUNNING")
            
        elif new_state == "RUNNING":
            self.ui.COM_connect_button.setText("Rodando")
            # Ensure it stays green if the state updates to RUNNING directly
            self.ui.COM_connect_button.setStyleSheet("background-color: green; color: white;")

    def send_handshake(self):
        if self.serial_connection and self.serial_connection.is_open:
            print("Sending handshake")
            self.serial_connection.write(b'C')

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
            self.serial_connection = serial.Serial(port, 115200, timeout=0)
            self.ui.COM_connect_button.setText("Conectando...")
            
            self.read_timer.start(20)
            self.handshake_timer.start(500)

            self.ui.COM_connect_button.setEnabled(False)
            self.ui.COM_disconnect_button.setEnabled(True)
            self.ui.COM_port_ComboBox.setEnabled(False)
            
        except serial.SerialException as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"Erro ao conectar: {str(e)}")
            msg.setWindowTitle("Erro de Conexão")
            msg.exec()

    def disconnect(self):
        self.read_timer.stop()
        self.handshake_timer.stop()
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        self.ui.COM_connect_button.setText("Conectar")
        self.ui.COM_connect_button.setStyleSheet("background-color: #003cb5; color: white;")
        self.ui.COM_connect_button.setEnabled(True)
        self.ui.COM_disconnect_button.setEnabled(False)
        self.ui.COM_port_ComboBox.setEnabled(True)
        
        self.state_controller.update_state("DISCONNECTED")

    def send_command(self, command):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                formatted_message = f"{command}\n"
                self.serial_connection.write(formatted_message.encode('utf-8'))
            except Exception as e:
                print(f"Erro ao enviar dado: {e}")

    def read_serial_data(self):
        """Reads incoming data and passes it straight to the StateController."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                while self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        # Direct the raw string to the state controller
                        self.state_controller.process_incoming_data(line)
                        
            except Exception as e:
                print(f"Erro ao ler serial: {e}")
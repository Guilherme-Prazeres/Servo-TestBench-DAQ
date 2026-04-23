from PyQt6.QtCore import QObject, pyqtSignal

class StateController(QObject):
    """
    Acompanha o estado da máquina e processa o fluxo de dados.
    """
    # Signal emitted when the FSM state changes
    state_changed = pyqtSignal(str)
    
    # Signal emitted when new telemetry arrives so other controllers can react
    telemetry_updated = pyqtSignal(float, float, float)

    def __init__(self):
        super().__init__()
        self.current_state = "DISCONNECTED"
        
        self.latest_torque = 0.0
        self.latest_current = 0.0
        self.latest_voltage = 0.0

    def process_incoming_data(self, raw_string):
        """
        Parses the incoming string from Arduino: "STATE,torque,current,voltage"
        or just "STATE" during initialization handshakes.
        """
        parts = raw_string.split(',')
        
        if len(parts) > 0:
            # 1. Always extract and update the state first
            new_state = parts[0].strip()
            self.update_state(new_state)
            
            # 2. If the string contains telemetry (length == 4), process it
            if len(parts) == 4:
                try:
                    torque = float(parts[1])
                    current = float(parts[2])
                    voltage = float(parts[3])
                    self.update_telemetry(torque, current, voltage)
                except ValueError:
                    print(f"Erro ao converter telemetria: {raw_string}")

    def update_state(self, new_state):
        """Updates the state and emits a signal only if it changed."""
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(self.current_state)
            print(f"[CURRENT STATE]: {self.current_state}")

    def update_telemetry(self, torque, current, voltage):
        """Stores the absolute latest data points and broadcasts them."""
        self.latest_torque = torque
        self.latest_current = current
        self.latest_voltage = voltage
        
        # Broadcast to any UI elements, plots, or loggers listening
        self.telemetry_updated.emit(torque, current, voltage)
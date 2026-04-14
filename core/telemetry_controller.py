class TelemetryController:
    def __init__(self, ui, com_controller, graph_controller):
        self.ui = ui
        self.com_controller = com_controller
        self.graph_controller = graph_controller
        
        self.com_controller.signals.data_received.connect(self.parse_and_update)

    def parse_and_update(self, data_string):
        parts = data_string.split(',')
        
        if len(parts) == 4 and parts[0] == "0":
            try:
                torque = float(parts[1])
                current = float(parts[2])
                voltage = float(parts[3])
                
                self.ui.metricTorque_valuesLabel.setText(f"{torque:.2f}")
                self.ui.metricCorrente_valueLabel.setText(f"{current:.1f}")
                self.ui.metricVoltage_valueLabel.setText(f"{voltage:.2f}")
                
                self.graph_controller.update_plots(torque, current, voltage)
                
            except ValueError:
                pass
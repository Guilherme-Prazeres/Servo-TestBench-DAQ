import numpy as np

class TelemetryController:
    def __init__(self, ui, com_controller, graph_controller, state_controller):
        self.ui = ui
        self.com_controller = com_controller
        self.graph_controller = graph_controller
        self.state_controller = state_controller

        self.is_paused = False
        self.ui.pause_button.clicked.connect(self.pause)

        self.ui.taraBalanca_button.clicked.connect(self.tare_scale)
        
        # Connect to the new StateController signals
        self.state_controller.telemetry_updated.connect(self.update_telemetry)
        self.state_controller.state_changed.connect(self.handle_state_change)

        self.pulling_torques = []
        self.pulling_currents = []

    def _generate_card_html(self, value, unit, unit_color):
        """Helper function to generate the Rich Text HTML for the metric cards."""
        return f"""
        <div style="text-align: center;">
          <span style="font-size: 24px; font-weight: 800; color: #FFFFFF;">{value:.2f}</span>
          <span style="font-size: 12px; font-weight: bold; color: {unit_color};"> {unit}</span>
        </div>
        """

    def _update_max_labels(self, meanTorque, meanCurr):
        """Helper function to update the Max Torque and Current labels."""
        self.ui.maxTorqueTestValue_label.setText(f"""
        <html><head/><body><p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">MAX TORQUE:</span><span style=" font-size:12px; font-weight:700; color:#191a1b;">-------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{meanTorque:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">kg.cm</span></p><p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">MAX CORRENTE:</span><span style=" font-size:12px; font-weight:700; color:#191a1b;">----</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{meanCurr:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">A</span></p></body></html>"""   
        )

    def pause(self):
        if self.com_controller.serial_connection and self.com_controller.serial_connection.is_open:
            if not self.is_paused:
                self.com_controller.send_command("IDLE")
                self.ui.pause_button.setText("Pausado")
                self.ui.taraBalanca_button.setEnabled(False)
            else:
                self.com_controller.send_command("RUNNING")
                self.ui.pause_button.setText("Pausar")
                self.ui.taraBalanca_button.setEnabled(True)
            self.is_paused = not self.is_paused
        else:
            print("Cannot pause: Arduino is not connected.")

    def tare_scale(self):
        if self.com_controller.serial_connection and self.com_controller.serial_connection.is_open:
            # print("Sending Tare Command to Arduino...")
            self.com_controller.send_command("TARE") 
        else:
            print("Cannot tare: Arduino is not connected.")

    def handle_state_change(self, new_state):
        """Reacts to changes in the FSM state."""
        if new_state == "STARTING":
            # Reset arrays and labels when a new test starts
            self.pulling_torques.clear()
            self.pulling_currents.clear()
            self._update_max_labels(0.0, 0.0)

        elif new_state == "IDLE":
            # Force the button into the "Paused" state
            self.is_paused = True
            self.ui.pause_button.setText("Pausado")
            self.ui.taraBalanca_button.setEnabled(False)

        elif new_state == "RUNNING":
            self.is_paused = False
            self.ui.pause_button.setText("Pausar")
            self.ui.taraBalanca_button.setEnabled(True)

    def update_telemetry(self, torque, current, voltage):
        """Called every time new telemetry data arrives from the StateController."""
        
        if self.state_controller.current_state == "IDLE":
            return

        # 1. Update UI Metric Cards
        torque_html = self._generate_card_html(torque, "kg.cm", "#FFC0CB")
        self.ui.metricTorque_valuesLabel.setText(torque_html)
        
        current_html = self._generate_card_html(current, "A", "#144E85")
        self.ui.metricCorrente_valueLabel.setText(current_html)
        
        voltage_html = self._generate_card_html(voltage, "V", "#188121")
        self.ui.metricVoltage_valueLabel.setText(voltage_html)
        
        # 2. Update the graphs
        self.graph_controller.update_plots(torque, current, voltage)

        # 3. Pulling logic check
        # We can safely check current_state here because the StateController 
        # updates the state BEFORE emitting telemetry_updated.
        if self.state_controller.current_state == "PULLING":
            self.pulling_torques.append(torque)
            self.pulling_currents.append(current)
            
            top_100_torques = sorted(self.pulling_torques, reverse=True)[:300]
            top_100_currents = sorted(self.pulling_currents, reverse=True)[:300]
            
            meanTorque = np.mean(top_100_torques) if top_100_torques else 0.0
            meanCurr = np.mean(top_100_currents) if top_100_currents else 0.0

            self._update_max_labels(meanTorque, meanCurr)
import numpy as np
import math

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

        # Arrays to store top values during PULLING
        self.pulling_torques = []
        self.pulling_currents = []
        self.pulling_voltages = [] # NEW: Added to track voltage

    def _generate_card_html(self, value, unit, unit_color):
        """Helper function to generate the Rich Text HTML for the metric cards."""
        return f"""
        <div style="text-align: center;">
          <span style="font-size: 24px; font-weight: 800; color: #FFFFFF;">{value:.2f}</span>
          <span style="font-size: 12px; font-weight: bold; color: {unit_color};"> {unit}</span>
        </div>
        """

    def _update_max_labels(self, meanTorque, meanCurr, meanVolt, resistance, kt, kv, power):
        """Helper function to update the Max Torque and Current labels."""
        # UPDATED: Replaced empty {} with formatting variables to properly inject the calculated values
        self.ui.maxTorqueTestValue_label.setText(f"""
        <html><head/><body>
        <p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">MAX TORQUE:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{meanTorque:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">kg.cm</span></p>
        <p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">MAX CORRENTE:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">----</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{meanCurr:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">A</span></p>
        <p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">TENSÃO:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">-------------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{meanVolt:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">V</span></p>
        <p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">RESISTÊNCIA:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">--------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{resistance:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">ohm</span></p>
        <p align="justify"><span style=" font-size:16pt; font-weight:700; color:#d9dcd6;">K</span><span style=" font-size:16pt; font-weight:700; color:#d9dcd6; vertical-align:sub;">t</span><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">------------------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{kt:.4f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">N.m/A</span></p>
        <p align="justify"><span style=" font-size:16pt; font-weight:700; color:#d9dcd6;">K</span><span style=" font-size:16pt; font-weight:700; color:#d9dcd6; vertical-align:sub;">v</span><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">------------------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{kv:.0f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">RPM/V</span></p>
        <p align="justify"><span style=" font-size:12px; font-weight:700; color:#d9dcd6;">POWER:</span><span style=" font-size:12px; font-weight:700; color:#22282a;">-------------</span><span style=" font-size:23px; font-weight:800; color:#ffffff;">{power:.2f} </span><span style=" font-size:16px; font-weight:700; color:#00d2ff;">W</span></p>
        </body></html>
        """)

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
            self.com_controller.send_command("TARE") 
        else:
            print("Cannot tare: Arduino is not connected.")

    def handle_state_change(self, new_state):
        """Reacts to changes in the FSM state."""
        if new_state == "STARTING":
            # Reset arrays and labels when a new test starts
            self.pulling_torques.clear()
            self.pulling_currents.clear()
            self.pulling_voltages.clear() # Reset voltages
            self._update_max_labels(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0) # Reset all 7 labels

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
        if self.state_controller.current_state == "PULLING":
            self.pulling_torques.append(torque)
            self.pulling_currents.append(current)
            self.pulling_voltages.append(voltage) # Track pulling voltage
            
            # Retrieve the top 300 values
            top_300_torques = sorted(self.pulling_torques, reverse=True)[:150]
            top_300_currents = sorted(self.pulling_currents, reverse=True)[:150]
            top_300_voltages = sorted(self.pulling_voltages, reverse=True)[:150]
            
            # Calculate Means
            meanTorque = np.mean(top_300_torques) if top_300_torques else 0.0
            meanCurr = np.mean(top_300_currents) if top_300_currents else 0.0
            meanVolt = np.mean(top_300_voltages) if top_300_voltages else 0.0

            # --- CALCULATE NEW METRICS ---
            
            # 1. Resistance (Ohms) = V / I 
            # We add a safety check (meanCurr > 0) to avoid division by zero crashes
            resistance = (meanVolt / meanCurr) if meanCurr > 0.0 else 0.0

            # 2. Kt (Torque Constant in N.m/A)
            # Conversion: 1 kg.cm = 0.0980665 N.m
            torque_nm = meanTorque * 0.0980665
            kt = (torque_nm / meanCurr) if meanCurr > 0.0 else 0.0

            # 3. Kv (Motor Velocity Constant in RPM/V)
            # Derived from Kt using the standard formula: Kv = 60 / (2 * PI * Kt)
            kv = (60.0 / (2 * math.pi * kt)) if kt > 0.0 else 0.0

            # 4. Power (Electrical Power in Watts) = V * I
            power = meanVolt * meanCurr

            # Update the UI
            self._update_max_labels(meanTorque, meanCurr, meanVolt, resistance, kt, kv, power)
class ManualController:
    def __init__(self, ui, com_controller):
        self.ui = ui
        self.com_controller = com_controller
        
        # Configure the slider limits (0 to 100%)
        self.ui.ManualControl_dial.setMinimum(0)
        self.ui.ManualControl_dial.setMaximum(100)
        self.ui.ManualControl_dial.setValue(0)
        
        # Connect slider signal (triggers ONLY when the user releases the mouse)
        self.ui.ManualControl_dial.sliderMoved.connect(self.on_slider_released)
        
        # Connect button signals
        # Mapping based on the button text in your UI file:
        # ManualControl_100_button -> "0%"
        # ManualControl_50_button -> "50%"
        # ManualControl_0_button -> "100%"
        self.ui.ManualControl_100_button.clicked.connect(lambda: self.set_and_send(0.0))
        self.ui.ManualControl_50_button.clicked.connect(lambda: self.set_and_send(0.5))
        self.ui.ManualControl_0_button.clicked.connect(lambda: self.set_and_send(1.0))

    def on_slider_released(self):
        # Convert slider value (0-100) to a float between 0.0 and 1.0
        float_value = self.ui.ManualControl_dial.value() / 100.0
        self.send_to_arduino(float_value)

    def set_and_send(self, float_value):
        # Update the UI slider visually
        slider_value = int(float_value * 100)
        self.ui.ManualControl_dial.setValue(slider_value)
        # Send the value
        self.send_to_arduino(float_value)

    def send_to_arduino(self, value):
        # Format the string as "0,<value>". Example: "0,0.50"
        command = f"SERVO,{value:.2f}"
        self.com_controller.send_command(command)
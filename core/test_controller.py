class TestController:
    def __init__(self, ui, com_controller):
        self.ui = ui
        self.com_controller = com_controller
        
        # 1. Define your list of available tests here
        # IMPORTANT: Make sure the order here matches the page order in Qt Designer!
        # Page 0 = MAX_TORQUE_TEST
        # Page 1 = FATIGUE_TEST
        # Page 2 = DISCHARGE_TEST
        available_tests = [
            "MAX_TORQUE_TEST",
            "FATIGUE_TEST",      
            "DISCHARGE_TEST"
        ]
        
        # 2. Clear any default/placeholder items from the .ui file
        self.ui.TEST_comboBox.clear()
        
        # 3. Populate the ComboBox with your list
        self.ui.TEST_comboBox.addItems(available_tests)

        # --- NEW CODE: Connect the combo box to the stacked widget ---
        self.ui.TEST_comboBox.currentIndexChanged.connect(self.change_test_view)

        # Connect the button click signals to our methods
        self.ui.Test_init_button.clicked.connect(self.start_test)
        
        # --- NEW CODE: Set initial state ---
        # Force the StackWidget to show the correct page on startup
        self.change_test_view(self.ui.TEST_comboBox.currentIndex())

    def start_test(self):
        # 1. Get the currently selected text from the combo box
        selected_test = self.ui.TEST_comboBox.currentText().strip()
        
        # 2. Check if a valid test is selected
        if not selected_test:
            return
        
        # 3. Send the command via the COM controller
        try:
            self.com_controller.send_command(selected_test) 
        except Exception as e:
            print(f"Failed to send test command: {e}")

    # --- NEW METHOD ---
    def change_test_view(self, index):
        """Switches the StackWidget page when the ComboBox changes."""
        
        # If your StackedWidget pages in Qt Designer exactly match 
        # the order of your `available_tests` list, this is all you need:
        self.ui.results_test_StackWidget.setCurrentIndex(index)
        
        test_name = self.ui.TEST_comboBox.itemText(index)
        
        if test_name == "MAX_TORQUE_TEST":
            self.ui.results_test_StackWidget.setCurrentIndex(0) # Put correct page index here
        elif test_name == "FATIGUE_TEST":
            self.ui.results_test_StackWidget.setCurrentIndex(1)
        elif test_name == "DISCHARGE_TEST":
            self.ui.results_test_StackWidget.setCurrentIndex(2 )
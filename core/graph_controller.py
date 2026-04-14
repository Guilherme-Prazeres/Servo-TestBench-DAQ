import pyqtgraph as pg

class GraphController:
    def __init__(self, ui):
        self.ui = ui
        
        self.ui.graphicsView.hide()
        self.ui.graphicsView_2.hide()
        self.ui.graphicsView_3.hide()

        self.plot_torque = pg.PlotWidget(title="Torque (N)")
        self.plot_current = pg.PlotWidget(title="Corrente (mA)")
        self.plot_voltage = pg.PlotWidget(title="Tensão (V)")

        self.ui.verticalLayout_8.addWidget(self.plot_torque)
        self.ui.verticalLayout_8.addWidget(self.plot_current)
        self.ui.verticalLayout_8.addWidget(self.plot_voltage)

        self.plot_torque.showGrid(x=True, y=True)
        self.plot_current.showGrid(x=True, y=True)
        self.plot_voltage.showGrid(x=True, y=True)

        self.curve_torque = self.plot_torque.plot(pen='y')
        self.curve_current = self.plot_current.plot(pen='r')
        self.curve_voltage = self.plot_voltage.plot(pen='c')

        self.data_len = 1000
        self.x_data = list(range(self.data_len))
        self.torque_data = [0.0] * self.data_len
        self.current_data = [0.0] * self.data_len
        self.voltage_data = [0.0] * self.data_len

    def update_plots(self, torque, current, voltage):
        self.torque_data = self.torque_data[1:] + [torque]
        self.current_data = self.current_data[1:] + [current]
        self.voltage_data = self.voltage_data[1:] + [voltage]

        self.curve_torque.setData(self.x_data, self.torque_data)
        self.curve_current.setData(self.x_data, self.current_data)
        self.curve_voltage.setData(self.x_data, self.voltage_data)
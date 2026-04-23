import pyqtgraph as pg
from PyQt6.QtWidgets import QFileDialog
import csv
import os
import numpy as np

class GraphController:
    def __init__(self, ui, state_controller):
        self.ui = ui
        self.state_controller = state_controller

        self.ui.graphicsView.hide()
        self.ui.graphicsView_2.hide()
        self.ui.graphicsView_3.hide()
        
        self.ui.graphic_resetPlots.clicked.connect(self.reset_plots)
        self.ui.exportar_button.clicked.connect(self.export_csv)
        
        self.connected = False

        # --- Axis config: (min, max, label, unit, pen color) ---
        self.axis_config = {
            "torque":  {"min": 0, "max": 6,  "label": "Torque",   "unit": "kg·cm", "pen": pg.mkPen('#FFC0CB', width=2)},
            "current": {"min": 0, "max": 5,"label": "Corrente", "unit": "A",  "pen": pg.mkPen("#144E85", width=2)},
            "voltage": {"min": 0, "max": 8,   "label": "Tensão",   "unit": "V",   "pen": pg.mkPen("#188121", width=2)},
        }

        self.data_len = 1200
        self.x_data = np.arange(self.data_len)
        self.torque_data  = np.zeros(self.data_len)
        self.current_data = np.zeros(self.data_len)
        self.voltage_data = np.zeros(self.data_len)

        self.plot_torque  = self._build_plot("torque")
        self.plot_current = self._build_plot("current")
        self.plot_voltage = self._build_plot("voltage")
        
        for plot in [self.plot_torque, self.plot_current, self.plot_voltage]:
            self.ui.verticalLayout_8.addWidget(plot)

        cfg = self.axis_config
        self.curve_torque  = self.plot_torque.plot(pen=cfg["torque"]["pen"])
        self.curve_current = self.plot_current.plot(pen=cfg["current"]["pen"])
        self.curve_voltage = self.plot_voltage.plot(pen=cfg["voltage"]["pen"])

        # plot.enableAutoRange()

        # Store proxies as attributes so they aren't garbage collected
        self._proxy_torque  = self._add_crosshair(self.plot_torque,  self.curve_torque,  lambda: self.torque_data,  "Torque (N·m)")
        self._proxy_current = self._add_crosshair(self.plot_current, self.curve_current, lambda: self.current_data, "Corrente (mA)")
        self._proxy_voltage = self._add_crosshair(self.plot_voltage, self.curve_voltage, lambda: self.voltage_data, "Tensão (V)")

    def export_csv(self):
        """Opens a file dialog to choose save location and exports all 3 graphs to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Exportar dados como CSV",
            os.path.expanduser("~/dados_sensores.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        # Ensure .csv extension
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Torque [kgcm]", "Corrente [A]", "Tensão [V]"])
            for i in range(self.data_len):
                writer.writerow([
                    i + 1,
                    round(float(self.torque_data[i]),  5),
                    round(float(self.current_data[i]), 5),
                    round(float(self.voltage_data[i]), 5),
                ])


    # ------------------------------------------------------------------ #
    def _build_plot(self, key):
        cfg = self.axis_config[key]
        plot = pg.PlotWidget()

        # Dark background
        plot.setBackground("#121314")

        # Grid
        plot.showGrid(x=True, y=True, alpha=0.25)

        # Axis labels
        label_style = {'color': '#AAAACC', 'font-size': '11px'}
        plot.setLabel('left',   cfg["label"], units=cfg["unit"], **label_style)

        # Title
        plot.setTitle(
            f'<span style="color:#CCCCFF; font-size:13px; font-weight:600;">'
            f'{cfg["label"]} ({cfg["unit"]})</span>'
        )

        # Default Y range
        plot.setYRange(cfg["min"], cfg["max"], padding=0.05)

        # Style the axes
        for ax in ('left', 'bottom'):
            plot.getAxis(ax).setPen(pg.mkPen('#555577'))
            plot.getAxis(ax).setTextPen(pg.mkPen('#AAAACC'))

        # Thin border
        plot.getViewBox().setBorder(pg.mkPen('#333355', width=1))

        # Disable mouse interaction (keeps it clean for live data)
        # plot.setMouseEnabled(x=False, y=False)
        # plot.hideButtons()

        return plot
    
    def _add_crosshair(self, plot, curve, data_ref, label):
        vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#FFFFFF44'))
        hLine = pg.InfiniteLine(angle=0,  movable=False, pen=pg.mkPen('#FFFFFF44'))
        plot.addItem(vLine)
        plot.addItem(hLine)

        value_label = pg.TextItem(anchor=(0, 1), color='#FFFFFF')
        plot.addItem(value_label)

        def mouse_moved(evt):
            # Check connection state live, every time the mouse moves
            if self.state_controller.current_state == "DISCONNECTED":
                return 
            
            pos = evt[0]
            if plot.sceneBoundingRect().contains(pos):
                try:
                    mp = plot.getViewBox().mapSceneToView(pos)
                    x = int(np.clip(mp.x(), 0, self.data_len - 1))
                    y = data_ref()[x]
                    vLine.setPos(mp.x())
                    hLine.setPos(y)
                    value_label.setPos(mp.x(), y)
                    value_label.setText(f"{label}: {y:.3f}  | max: {data_ref().max():.3f}")
                except ValueError:
                    pass

        proxy = pg.SignalProxy(plot.scene().sigMouseMoved, rateLimit=60, slot=mouse_moved)
        return proxy

    # ------------------------------------------------------------------ #
    def _update_y_axis(self, plot, data, key):
        """
        Keeps the Y axis at the configured [min, max] unless the live data
        exceeds max — then it expands. Snaps back as soon as data fits again.
        """
        cfg = self.axis_config[key]
        data_max = data.max()
        data_min = data.min()

        y_min = min(cfg["min"], data_min)
        y_max = max(cfg["max"], data_max)

        # Add a small headroom (5 %) so the line never touches the top edge
        headroom = (y_max - y_min) * 0.05 if y_max != y_min else 0.5
        plot.setYRange(y_min, y_max + headroom, padding=0)

    # ------------------------------------------------------------------ #
    def update_plots(self, torque, current, voltage):
        self.torque_data  = np.roll(self.torque_data,  -1)
        self.current_data = np.roll(self.current_data, -1)
        self.voltage_data = np.roll(self.voltage_data, -1)

        self.torque_data[-1]  = torque
        self.current_data[-1] = current
        self.voltage_data[-1] = voltage

        self.curve_torque.setData(self.x_data, self.torque_data)
        self.curve_current.setData(self.x_data, self.current_data)
        self.curve_voltage.setData(self.x_data, self.voltage_data)

        # Dynamic but anchored axis scaling
        self._update_y_axis(self.plot_torque,  self.torque_data,  "torque")
        self._update_y_axis(self.plot_current, self.current_data, "current")
        self._update_y_axis(self.plot_voltage, self.voltage_data, "voltage")

    # ------------------------------------------------------------------ #
    def reset_plots(self):
        self.torque_data.fill(0.0)
        self.current_data.fill(0.0)
        self.voltage_data.fill(0.0)

        self.curve_torque.setData(self.x_data, self.torque_data)
        self.curve_current.setData(self.x_data, self.current_data)
        self.curve_voltage.setData(self.x_data, self.voltage_data)

        # Snap axes back to defaults on reset
        for key, plot in [("torque",  self.plot_torque),
                           ("current", self.plot_current),
                           ("voltage", self.plot_voltage)]:
            cfg = self.axis_config[key]
            plot.setYRange(cfg["min"], cfg["max"], padding=0.05)
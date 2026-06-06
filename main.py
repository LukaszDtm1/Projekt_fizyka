import sys
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSlider, QLabel, QPushButton, QGroupBox)
from PyQt6.QtCore import QTimer, Qt


#Klasa Silnika Fizycznego
class SimulationCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#f0f2f5')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#f0f2f5')
        super().__init__(self.fig)
        self.setParent(parent)

        # Parametry Fizyczne
        self.N_max = 20
        self.N = 10
        self.m = 1.0
        self.k = 25.0
        self.damping = 0.05
        self.dt = 0.01
        self.substeps = 2

        self.spring_template = self._generate_spring_template(coils=6, width=0.25)

        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-4, 4)
        self.ax.set_title('Symulator Fali: Kule i Sprężyny 3D', fontsize=12, fontweight='bold', pad=10)
        self.ax.set_xlabel('Położenie')
        self.ax.set_ylabel('Amplituda')
        self.ax.grid(True, linestyle='--', color='white', linewidth=1.5, zorder=0)

        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#bdc3c7')
        self.ax.spines['bottom'].set_color('#bdc3c7')

        self.spring_lines = [self.ax.plot([], [], '-', color='#7f8c8d', lw=1.5, zorder=1, animated=True)[0] for _ in
                             range(self.N_max)]
        self.shadows = self.ax.scatter([], [], s=450, color='black', alpha=0.15, zorder=2, animated=True)
        self.spheres = self.ax.scatter([], [], s=400, color='#e74c3c', edgecolors='#c0392b', linewidths=1.5, zorder=3,
                                       animated=True)
        self.highlights = self.ax.scatter([], [], s=60, color='white', alpha=0.7, zorder=4, animated=True)

        # ruch myszką
        self.dragging = False
        self.active_idx = None
        self.mouse_y = 0.0

        self.bg = None
        self.mpl_connect('draw_event', self.on_draw_event)

        self.mpl_connect('button_press_event', self.on_press)
        self.mpl_connect('motion_notify_event', self.on_motion)
        self.mpl_connect('button_release_event', self.on_release)

        self.reset_simulation()

    def _generate_spring_template(self, coils, width):
        t = np.linspace(0, 1, coils * 15)
        x = t + 0.04 * np.cos(2 * np.pi * coils * t)
        y = width * np.sin(2 * np.pi * coils * t)
        return np.column_stack((x, y))

    def _get_transformed_spring(self, start, end):
        delta = end - start
        dist = np.linalg.norm(delta)
        if dist < 1e-4: return np.array([start, end])

        angle = np.arctan2(delta[1], delta[0])

        scaled = self.spring_template.copy()
        scaled[:, 0] *= dist

        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])

        return np.dot(scaled, rot.T) + start

    def on_draw_event(self, event):
        self.bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)

    def reset_simulation(self):
        self.x = np.linspace(0, 10, self.N)
        self.y = np.zeros(self.N)
        self.v = np.zeros(self.N)
        for ln in self.spring_lines:
            ln.set_data([], [])

        self.bg = None
        self.draw_idle()

    def step_physics(self):
        for _ in range(self.substeps):
            left_y = np.roll(self.y, 1)
            left_y[0] = 0
            right_y = np.roll(self.y, -1)
            right_y[-1] = 0

            F = self.k * (right_y - self.y) - self.k * (self.y - left_y)
            a = (F / self.m) - (self.damping * self.v)

            self.v += a * self.dt
            self.y += self.v * self.dt

            self.y[0], self.y[-1] = 0, 0

            if self.dragging and self.active_idx is not None and self.active_idx < len(self.y):
                self.y[self.active_idx] = self.mouse_y
                self.v[self.active_idx] = 0

    def update_view(self):
        if self.bg is None:
            return

        #Przywróć czyste tło
        self.fig.canvas.restore_region(self.bg)

        pts = np.c_[self.x, self.y]

        #Aktualizacja pozycji danych
        self.spheres.set_offsets(pts)
        self.shadows.set_offsets(pts + np.array([0.08, -0.12]))
        self.highlights.set_offsets(pts + np.array([-0.06, 0.08]))

        #rysowanie sprężyn
        for i in range(self.N - 1):
            spring_pts = self._get_transformed_spring(pts[i], pts[i + 1])
            self.spring_lines[i].set_data(spring_pts[:, 0], spring_pts[:, 1])
            self.ax.draw_artist(self.spring_lines[i])

        #rysowanie kulek
        self.ax.draw_artist(self.shadows)
        self.ax.draw_artist(self.spheres)
        self.ax.draw_artist(self.highlights)

        #dawanie nowej klatki na ekran
        self.fig.canvas.blit(self.ax.bbox)
        self.fig.canvas.flush_events()

    # sterowanie myszą
    def on_press(self, event):
        if event.inaxes == self.ax:
            self.dragging = True
            dists = np.sqrt((self.x - event.xdata) ** 2 + (self.y - event.ydata) ** 2)
            if np.min(dists) < 0.8:
                self.active_idx = np.argmin(dists)
                self.mouse_y = event.ydata

    def on_motion(self, event):
        if self.dragging and event.inaxes == self.ax:
            self.mouse_y = event.ydata

    def on_release(self, event):
        self.dragging = False
        self.active_idx = None


# GUI
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulacja Oscylatora - Projekt Zaliczeniowy")
        self.setMinimumSize(1000, 650)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Wykres
        self.canvas = SimulationCanvas(self, width=7, height=5, dpi=100)
        main_layout.addWidget(self.canvas, stretch=4)

        # Panel Sterowania
        control_panel = QWidget()
        control_panel.setFixedWidth(280)
        control_layout = QVBoxLayout(control_panel)
        main_layout.addWidget(control_panel, stretch=1)

        # Parametry
        param_group = QGroupBox("Parametry Układu")
        param_vbox = QVBoxLayout(param_group)

        self.lbl_N = QLabel(f"Liczba mas: {self.canvas.N}")
        self.slider_N = QSlider(Qt.Orientation.Horizontal)
        self.slider_N.setRange(4, 20)
        self.slider_N.setValue(self.canvas.N)
        self.slider_N.valueChanged.connect(self.change_N)
        param_vbox.addWidget(self.lbl_N)
        param_vbox.addWidget(self.slider_N)

        self.lbl_m = QLabel(f"Masa (m): {self.canvas.m:.1f}")
        self.slider_m = QSlider(Qt.Orientation.Horizontal)
        self.slider_m.setRange(1, 50)
        self.slider_m.setValue(int(self.canvas.m * 10))
        self.slider_m.valueChanged.connect(self.change_m)
        param_vbox.addWidget(self.lbl_m)
        param_vbox.addWidget(self.slider_m)

        self.lbl_k = QLabel(f"Sprężystość (k): {self.canvas.k:.0f}")
        self.slider_k = QSlider(Qt.Orientation.Horizontal)
        self.slider_k.setRange(5, 100)
        self.slider_k.setValue(int(self.canvas.k))
        self.slider_k.valueChanged.connect(self.change_k)
        param_vbox.addWidget(self.lbl_k)
        param_vbox.addWidget(self.slider_k)

        control_layout.addWidget(param_group)

        # Przyciski
        action_group = QGroupBox("Sterowanie")
        action_vbox = QVBoxLayout(action_group)

        self.btn_pulse = QPushButton("Generuj Falę")
        self.btn_pulse.setStyleSheet("background-color: #2ecc71; color: white; padding: 8px; border-radius: 4px;")
        self.btn_pulse.clicked.connect(self.trigger_pulse)
        action_vbox.addWidget(self.btn_pulse)

        self.btn_reset = QPushButton("Reset (Zatrzymaj)")
        self.btn_reset.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 4px;")
        self.btn_reset.clicked.connect(self.reset_sim)
        action_vbox.addWidget(self.btn_reset)

        control_layout.addWidget(action_group)
        control_layout.addStretch()

        # Zegar animacji
        self.timer = QTimer()
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.animation_loop)
        self.timer.start()

    def change_N(self, value):
        self.lbl_N.setText(f"Liczba mas: {value}")
        self.canvas.N = value
        self.canvas.reset_simulation()

    def change_m(self, value):
        real_val = value / 10.0
        self.lbl_m.setText(f"Masa (m): {real_val:.1f}")
        self.canvas.m = real_val

    def change_k(self, value):
        self.lbl_k.setText(f"Sprężystość (k): {value:.0f}")
        self.canvas.k = float(value)

    def trigger_pulse(self):
        pulse = 3.5 * np.exp(-((self.canvas.x - 2.0) ** 2) / 0.4)
        self.canvas.y += pulse

    def reset_sim(self):
        self.canvas.reset_simulation()

    def animation_loop(self):
        self.canvas.step_physics()
        self.canvas.update_view()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QGroupBox { font-weight: bold; border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 15px; padding-top: 15px; color: #2c3e50; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
        QLabel { color: #34495e; font-size: 12px; margin-top: 5px;}
        QPushButton { font-weight: bold; border: none; }
        QPushButton:hover { opacity: 0.8; }
        QSlider::groove:horizontal { border: 1px solid #999999; height: 6px; background: #ecf0f1; margin: 2px 0; border-radius: 3px; }
        QSlider::handle:horizontal { background: #3498db; border: 1px solid #2980b9; width: 14px; margin: -4px 0; border-radius: 7px; }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
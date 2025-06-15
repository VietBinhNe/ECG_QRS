import sys
import serial
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class ECGDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hiển thị sóng ECG")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: white;")

        self.serial_port = serial.Serial('COM12', 38400, timeout=1)  # Thay 'COM12' bằng cổng của bạn
        self.sampling_rate = 200
        self.display_samples = 2000
        self.first_10s_samples = 2000

        self.raw_data = []
        self.filtered_data = []
        self.qrs_flags = []
        self.first_10s_raw = []
        self.first_10s_filtered = []
        self.first_10s_qrs = []
        self.is_running = True
        self.first_10s_collected = False
        self.qrs_display_enabled = False
        self.frame_count = 0
        self.wait_for_qrs = False
        self.qrs_buffer = []
        self.expected_qrs_indices = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.plot_widget1 = pg.PlotWidget(title="Sóng ECG liên tục (Đã lọc)")
        self.plot_widget1.setBackground('w')
        self.plot_widget1.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget1.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget1.setYRange(-2048, 2048)
        self.plot_widget1.setXRange(0, 10)
        self.plot_widget1.getAxis('left').setTextPen('black')
        self.plot_widget1.getAxis('bottom').setTextPen('black')
        self.plot_data1 = self.plot_widget1.plot(pen='b')
        self.qrs_plot1 = self.plot_widget1.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)
        self.main_layout.addWidget(self.plot_widget1)

        self.button_layout = QHBoxLayout()
        self.pause_button = QPushButton("Dừng")
        self.pause_button.setStyleSheet("background-color: lightgray; color: black;")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.button_layout.addWidget(self.pause_button)

        self.detect_button = QPushButton("Detect")
        self.detect_button.setStyleSheet("background-color: lightgray; color: black;")
        self.detect_button.setEnabled(False)
        self.detect_button.clicked.connect(self.detect_qrs)
        self.button_layout.addWidget(self.detect_button)
        self.main_layout.addLayout(self.button_layout)

        self.plot_widget2 = pg.PlotWidget(title="10 giây đầu (Chưa lọc)")
        self.plot_widget2.setBackground('w')
        self.plot_widget2.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget2.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget2.setYRange(0, 4096)
        self.plot_widget2.setXRange(0, 10)
        self.plot_widget2.getAxis('left').setTextPen('black')
        self.plot_widget2.getAxis('bottom').setTextPen('black')
        self.plot_data2 = self.plot_widget2.plot(pen='r')
        self.qrs_plot2 = self.plot_widget2.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)
        self.main_layout.addWidget(self.plot_widget2)

        self.plot_widget3 = pg.PlotWidget(title="10 giây đầu (Đã lọc)")
        self.plot_widget3.setBackground('w')
        self.plot_widget3.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget3.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget3.setYRange(-2048, 2048)
        self.plot_widget3.setXRange(0, 10)
        self.plot_widget3.getAxis('left').setTextPen('black')
        self.plot_widget3.getAxis('bottom').setTextPen('black')
        self.plot_data3 = self.plot_widget3.plot(pen='g')
        self.qrs_plot3 = self.plot_widget3.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)
        self.main_layout.addWidget(self.plot_widget3)

        self.debug_layout = QHBoxLayout()
        self.debug_label = QLabel("Thông tin gỡ lỗi:")
        self.debug_label.setStyleSheet("color: black; font-size: 14px;")
        self.debug_layout.addWidget(self.debug_label)

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMinimumHeight(100)
        self.debug_text.setStyleSheet("color: black; font-size: 12px; background-color: lightgray;")
        self.debug_layout.addWidget(self.debug_text)
        self.main_layout.addLayout(self.debug_layout)

        self.hr_layout = QHBoxLayout()
        self.hr_label = QLabel("Nhịp tim: N/A bpm")
        self.hr_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_label)

        self.hr_state_label = QLabel("Trạng thái nhịp tim: N/A")
        self.hr_state_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_state_label)
        self.main_layout.addLayout(self.hr_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)

        self.buffer = bytearray()

    def toggle_pause(self):
        if self.is_running:
            self.is_running = False
            self.pause_button.setText("Tiếp tục")
        else:
            self.is_running = True
            self.pause_button.setText("Dừng")

    def detect_qrs(self):
        self.qrs_display_enabled = True
        self.update_plots()
        qrs_indices = np.where(np.array(self.first_10s_qrs) == 1)[0]
        self.debug_text.append(f"DEBUG: QRS indices displayed: {qrs_indices.tolist()}")

    def update_data(self):
        if not self.is_running:
            return

        while self.serial_port.in_waiting > 0:
            self.buffer.extend(self.serial_port.read(self.serial_port.in_waiting))

            while len(self.buffer) > 0:
                if len(self.buffer) >= 6 and self.buffer[:6] == b"DEBUG:":
                    newline_idx = self.buffer.find(b"\n")
                    if newline_idx == -1:
                        break

                    debug_msg = self.buffer[:newline_idx].decode('utf-8', errors='ignore')
                    self.buffer = self.buffer[newline_idx + 1:]
                    self.debug_text.append(debug_msg)
                    self.debug_text.verticalScrollBar().setValue(self.debug_text.verticalScrollBar().maximum())

                    if debug_msg.startswith("DEBUG:TOTAL"):
                        self.wait_for_qrs = True
                        self.qrs_buffer = []
                        self.debug_text.append("DEBUG: Starting to collect QRS flags after processing")
                    elif debug_msg.startswith("DEBUG:QRS_INDICES:"):
                        indices_str = debug_msg[len("DEBUG:QRS_INDICES:"):-1]
                        if indices_str:
                            indices = [int(x) for x in indices_str.split(',') if x]
                            self.expected_qrs_indices.extend(indices)
                            self.debug_text.append(f"DEBUG:Received QRS indices: {self.expected_qrs_indices}")
                    continue

                if self.buffer[0] != 0xAA:
                    self.buffer.pop(0)
                    continue

                if len(self.buffer) < 323:
                    break

                if self.buffer[322] != 0xBB:
                    self.buffer.pop(0)
                    continue

                frame = self.buffer[:323]
                calculated_checksum = sum(frame[1:321]) % 256
                received_checksum = frame[321]

                if calculated_checksum != received_checksum:
                    self.debug_text.append(f"DEBUG: Checksum error! Calculated: {calculated_checksum}, Received: {received_checksum}")
                    self.buffer = self.buffer[323:]
                    continue

                self.buffer = self.buffer[323:]

                raw_values = []
                bandpass_values = []
                qrs_flags = []
                for i in range(64):
                    idx = 1 + i * 2
                    value = (frame[idx] << 8) | frame[idx + 1]
                    raw_values.append(value)
                for i in range(64):
                    idx = 129 + i * 2
                    value = (frame[idx] << 8) | frame[idx + 1]
                    if value & 0x8000:
                        value -= 65536
                    bandpass_values.append(value)
                for i in range(64):
                    idx = 257 + i
                    qrs_flags.append(frame[idx])

                self.raw_data.extend(raw_values)
                self.filtered_data.extend(bandpass_values)
                self.qrs_flags.extend(qrs_flags)

                if len(self.raw_data) > self.display_samples:
                    self.raw_data = self.raw_data[-self.display_samples:]
                    self.filtered_data = self.filtered_data[-self.display_samples:]
                    self.qrs_flags = self.qrs_flags[-self.display_samples:]

                if not self.first_10s_collected:
                    self.first_10s_raw.extend(raw_values)
                    self.first_10s_filtered.extend(bandpass_values)
                    self.first_10s_qrs.extend([0] * len(qrs_flags))
                    if len(self.first_10s_raw) % 200 == 0:
                        self.debug_text.append(f"DEBUG: Sample QRS flags at sample {len(self.first_10s_raw)}: {qrs_flags[:10]}")
                    if len(self.first_10s_raw) >= self.first_10s_samples:
                        self.first_10s_collected = True
                        self.first_10s_raw = self.first_10s_raw[:self.first_10s_samples]
                        self.first_10s_filtered = self.first_10s_filtered[:self.first_10s_samples]
                        self.first_10s_qrs = [0] * self.first_10s_samples
                        self.debug_text.append(f"DEBUG: First 10 seconds collected. Length of first_10s_qrs: {len(self.first_10s_qrs)}")
                        self.wait_for_qrs = True
                        self.qrs_buffer = []

                if self.wait_for_qrs:
                    self.qrs_buffer.extend(qrs_flags)
                    if len(self.qrs_buffer) >= self.first_10s_samples:
                        self.first_10s_qrs = self.qrs_buffer[:self.first_10s_samples]
                        self.wait_for_qrs = False
                        self.detect_button.setEnabled(True)
                        self.qrs_display_enabled = True
                        self.debug_text.append(f"DEBUG: Collected QRS flags. Length of first_10s_qrs: {len(self.first_10s_qrs)}")
                        qrs_indices = np.where(np.array(self.first_10s_qrs) == 1)[0]
                        self.debug_text.append(f"DEBUG: QRS indices after collecting flags: {qrs_indices.tolist()}")
                        if self.expected_qrs_indices:
                            if sorted(list(qrs_indices)) == sorted(self.expected_qrs_indices):
                                self.debug_text.append("DEBUG: QRS indices match STM32 output")
                            else:
                                self.debug_text.append(f"DEBUG: QRS indices mismatch! Expected: {self.expected_qrs_indices}, Received: {qrs_indices.tolist()}")
                        for idx in qrs_indices:
                            if idx < len(self.first_10s_filtered):
                                self.debug_text.append(f"DEBUG:QRS_SIGNAL_VALUE:{idx}:{self.first_10s_filtered[idx]}")
                        self.update_heart_rate()
                        self.update_plots()

        self.update_plots()

    def update_heart_rate(self):
        qrs_count = sum(self.first_10s_qrs)
        duration_seconds = self.first_10s_samples / self.sampling_rate
        heart_rate = (qrs_count / duration_seconds) * 60
        self.hr_label.setText(f"Nhịp tim: {int(heart_rate)} bpm")

        rr_intervals = []
        last_peak = -1
        for i in range(len(self.first_10s_qrs)):
            if self.first_10s_qrs[i] == 1:
                if last_peak != -1:
                    rr_intervals.append(i - last_peak)
                last_peak = i
        if len(rr_intervals) > 1:
            rr_mean = np.mean(rr_intervals)
            rr_std = np.std(rr_intervals)
            if rr_std / rr_mean < 0.1:
                self.hr_state_label.setText("Trạng thái nhịp tim: Đều")
            else:
                self.hr_state_label.setText("Trạng thái nhịp tim: Không đều")
        else:
            self.hr_state_label.setText("Trạng thái nhịp tim: N/A")

    def update_plots(self):
        if len(self.filtered_data) > 0:
            time_axis = np.linspace(0, 10, len(self.filtered_data))
            self.plot_data1.setData(time_axis, self.filtered_data)
            self.qrs_plot1.setData([], [])

        if self.first_10s_collected:
            time_axis_10s = np.linspace(0, 10, len(self.first_10s_raw))
            self.plot_data2.setData(time_axis_10s, self.first_10s_raw)
            self.qrs_plot2.setData([], [])

            time_axis_10s = np.linspace(0, 10, len(self.first_10s_filtered))
            self.plot_data3.setData(time_axis_10s, self.first_10s_filtered)
            if self.qrs_display_enabled:
                qrs_indices_10s = np.where(np.array(self.first_10s_qrs) == 1)[0]
                qrs_timestamps_10s = time_axis_10s[qrs_indices_10s]
                qrs_values_10s = np.array(self.first_10s_filtered)[qrs_indices_10s]
                self.qrs_plot3.setData(qrs_timestamps_10s, qrs_values_10s)
            else:
                self.qrs_plot3.setData([], [])

    def closeEvent(self, event):
        self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ECGDisplay()
    window.show()
    sys.exit(app.exec_())
import sys
import serial
import numpy as np
import os
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QTextEdit, QScrollArea
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from qrs_detector import QRSDetector

class ECGDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hiển thị sóng ECG")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: white;")

        self.serial_port = None
        self.sampling_rate = 200
        self.display_samples = 2000  # 10 giây * 200 Hz cho khung liên tục
        self.first_120s_samples = 24000  # 120 giây * 200 Hz

        self.raw_data = []
        self.filtered_data = []
        self.qrs_flags = []
        self.first_120s_raw = []
        self.first_120s_filtered = []
        self.first_120s_qrs = []
        self.is_running = False
        self.first_120s_collected = False
        self.qrs_display_enabled = False
        self.frame_count = 0
        self.buffer = bytearray()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Panel thông tin bệnh nhân
        self.patient_panel = QWidget()
        self.patient_panel.setStyleSheet("background-color: lightgray; padding: 10px;")
        self.patient_layout = QVBoxLayout(self.patient_panel)
        self.patient_layout.setSpacing(10)

        self.name_label = QLabel("Tên bệnh nhân:")
        self.name_label.setStyleSheet("color: black; font-size: 14px;")
        self.patient_layout.addWidget(self.name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên bệnh nhân")
        self.name_input.setStyleSheet("background-color: white; color: black; font-size: 12px;")
        self.patient_layout.addWidget(self.name_input)

        self.id_label = QLabel("ID bệnh nhân:")
        self.id_label.setStyleSheet("color: black; font-size: 14px;")
        self.patient_layout.addWidget(self.id_label)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Nhập ID bệnh nhân")
        self.id_input.setStyleSheet("background-color: white; color: black; font-size: 12px;")
        self.patient_layout.addWidget(self.id_input)

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: lightblue; color: black; font-size: 14px;")
        self.start_button.clicked.connect(self.start_acquisition)
        self.patient_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Dừng")
        self.pause_button.setStyleSheet("background-color: #B0E0E6; color: black; font-size: 14px;")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)
        self.patient_layout.addWidget(self.pause_button)

        self.detect_button = QPushButton("Detect")
        self.detect_button.setStyleSheet("background-color: #B0E0E6; color: black; font-size: 14px;")
        self.detect_button.setEnabled(False)
        self.detect_button.clicked.connect(self.detect_qrs)
        self.patient_layout.addWidget(self.detect_button)

        self.patient_layout.addStretch()
        self.main_layout.addWidget(self.patient_panel, 1)  # Panel bệnh nhân chiếm 1/9

        # Panel chính cho biểu đồ
        self.plot_control_panel = QWidget()
        self.plot_control_layout = QVBoxLayout(self.plot_control_panel)

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
        self.plot_control_layout.addWidget(self.plot_widget1)

        # Sử dụng QScrollArea cho plot_widget2 với thanh cuộn ngang
        self.scroll_area2 = QScrollArea()
        self.scroll_area2.setWidgetResizable(True)
        self.plot_widget2 = pg.PlotWidget(title="120 giây đầu (Chưa lọc)")
        self.plot_widget2.setBackground('w')
        self.plot_widget2.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget2.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget2.setYRange(0, 4096)
        self.plot_widget2.getAxis('left').setTextPen('black')
        self.plot_widget2.getAxis('bottom').setTextPen('black')
        self.plot_data2 = self.plot_widget2.plot(pen='r')
        self.qrs_plot2 = self.plot_widget2.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)
        self.scroll_area2.setWidget(self.plot_widget2)
        self.plot_control_layout.addWidget(self.scroll_area2)

        # Sử dụng QScrollArea cho plot_widget3 với thanh cuộn ngang
        self.scroll_area3 = QScrollArea()
        self.scroll_area3.setWidgetResizable(True)
        self.plot_widget3 = pg.PlotWidget(title="120 giây đầu (Đã lọc)")
        self.plot_widget3.setBackground('w')
        self.plot_widget3.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget3.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget3.setYRange(-2048, 2048)  # Giữ phạm vi cố định
        self.plot_widget3.getAxis('left').setTextPen('black')
        self.plot_widget3.getAxis('bottom').setTextPen('black')
        self.plot_data3 = self.plot_widget3.plot(pen='g')
        self.qrs_plot3 = self.plot_widget3.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)
        self.scroll_area3.setWidget(self.plot_widget3)
        self.plot_control_layout.addWidget(self.scroll_area3)

        self.debug_layout = QHBoxLayout()
        self.debug_label = QLabel("Thông tin gỡ lỗi:")
        self.debug_label.setStyleSheet("color: black; font-size: 14px;")
        self.debug_layout.addWidget(self.debug_label)

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMinimumHeight(100)
        self.debug_text.setStyleSheet("color: black; font-size: 12px; background-color: lightgray;")
        self.debug_layout.addWidget(self.debug_text)
        self.plot_control_layout.addLayout(self.debug_layout)

        self.hr_layout = QHBoxLayout()
        self.hr_label = QLabel("Nhịp tim: N/A bpm")
        self.hr_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_label)

        self.hr_state_label = QLabel("Trạng thái nhịp tim: N/A")
        self.hr_state_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_state_label)
        self.plot_control_layout.addLayout(self.hr_layout)

        self.main_layout.addWidget(self.plot_control_panel, 8)  # Panel biểu đồ chiếm 8/9

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.qrs_detector = QRSDetector()

    def start_acquisition(self):
        if not self.name_input.text() or not self.id_input.text():
            self.debug_text.append("ERROR: Vui lòng nhập tên và ID bệnh nhân!")
            return

        try:
            self.serial_port = serial.Serial('COM12', 38400, timeout=1)
            self.is_running = True
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.timer.start(50)
            self.debug_text.append("DEBUG: Bắt đầu thu thập dữ liệu...")
        except Exception as e:
            self.debug_text.append(f"ERROR: Không thể mở cổng serial: {str(e)}")

    def toggle_pause(self):
        if self.is_running:
            self.is_running = False
            self.pause_button.setText("Tiếp tục")
        else:
            self.is_running = True
            self.pause_button.setText("Dừng")

    def detect_qrs(self):
        if len(self.first_120s_filtered) == self.first_120s_samples:
            self.qrs_detector.init()
            self.first_120s_qrs = self.qrs_detector.detect(np.array(self.first_120s_filtered))
            self.qrs_display_enabled = True
            self.update_plots()
            qrs_indices = np.where(np.array(self.first_120s_qrs) == 1)[0]
            self.debug_text.append(f"DEBUG: QRS indices displayed: {qrs_indices.tolist()}")
            self.update_heart_rate()
            self.save_patient_data()

    def update_data(self):
        if not self.is_running or not self.serial_port:
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
                    continue

                if self.buffer[0] != 0xAA:
                    self.buffer.pop(0)
                    continue

                if len(self.buffer) < 259:
                    break

                if self.buffer[258] != 0xBB:
                    self.buffer.pop(0)
                    continue

                frame = self.buffer[:259]
                calculated_checksum = sum(frame[1:257]) % 256
                received_checksum = frame[257]

                if calculated_checksum != received_checksum:
                    self.debug_text.append(f"DEBUG: Checksum error! Calculated: {calculated_checksum}, Received: {received_checksum}")
                    self.buffer = self.buffer[259:]
                    continue

                self.buffer = self.buffer[259:]

                raw_values = []
                bandpass_values = []
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

                self.raw_data.extend(raw_values)
                self.filtered_data.extend(bandpass_values)

                if len(self.raw_data) > self.display_samples:
                    self.raw_data = self.raw_data[-self.display_samples:]
                    self.filtered_data = self.filtered_data[-self.display_samples:]

                if not self.first_120s_collected:
                    self.first_120s_raw.extend(raw_values)
                    self.first_120s_filtered.extend(bandpass_values)
                    if len(self.first_120s_raw) >= self.first_120s_samples:
                        self.first_120s_collected = True
                        self.first_120s_raw = self.first_120s_raw[:self.first_120s_samples]
                        self.first_120s_filtered = self.first_120s_filtered[:self.first_120s_samples]
                        self.first_120s_qrs = [0] * self.first_120s_samples
                        self.detect_button.setEnabled(True)
                        self.debug_text.append(f"DEBUG: First 120 seconds collected. Length of first_120s_filtered: {len(self.first_120s_filtered)}")

        self.update_plots()

    def update_heart_rate(self):
        qrs_count = sum(self.first_120s_qrs)
        duration_seconds = self.first_120s_samples / self.sampling_rate
        heart_rate = (qrs_count / duration_seconds) * 60
        self.hr_label.setText(f"Nhịp tim: {int(heart_rate)} bpm")

        rr_intervals = []
        last_peak = -1
        for i in range(len(self.first_120s_qrs)):
            if self.first_120s_qrs[i] == 1:
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
            time_axis = np.linspace(max(0, len(self.filtered_data) - self.display_samples) / 200, 
                                min(10, len(self.filtered_data) / 200), 
                                min(len(self.filtered_data), self.display_samples))
            self.plot_data1.setData(time_axis, self.filtered_data[-self.display_samples:])
            self.qrs_plot1.setData([], [])

        if self.first_120s_collected:
            # Khung raw (chưa lọc) - Hiển thị toàn bộ 120 giây
            time_axis_120s_raw = np.linspace(0, 120, len(self.first_120s_raw))
            self.plot_widget2.setXRange(0, 15)  # Mặc định hiển thị 15 giây đầu
            self.plot_data2.setData(time_axis_120s_raw, self.first_120s_raw)
            self.qrs_plot2.setData([], [])

            # Khung đã lọc - Hiển thị toàn bộ 120 giây
            time_axis_120s_filtered = np.linspace(0, 120, len(self.first_120s_filtered))
            self.plot_widget3.setXRange(0, 15)  # Mặc định hiển thị 15 giây đầu
            self.plot_data3.setData(time_axis_120s_filtered, self.first_120s_filtered)
            if self.qrs_display_enabled:
                qrs_indices_120s = np.where(np.array(self.first_120s_qrs) == 1)[0]
                qrs_timestamps_120s = time_axis_120s_filtered[qrs_indices_120s]
                qrs_values_120s = np.array(self.first_120s_filtered)[qrs_indices_120s]
                self.qrs_plot3.setData(qrs_timestamps_120s, qrs_values_120s)
                # Loại bỏ autoRange để giữ tỷ lệ cố định
                # self.plot_widget3.autoRange()  # Comment hoặc xóa dòng này
            else:
                self.qrs_plot3.setData([], [])

    def save_patient_data(self):
        patient_name = self.name_input.text()
        patient_id = self.id_input.text()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("GUI/patients", exist_ok=True)
        filename = f"GUI/patients/patient_{patient_id}_{timestamp}.txt"

        qrs_count = sum(self.first_120s_qrs)
        duration_seconds = self.first_120s_samples / self.sampling_rate
        heart_rate = (qrs_count / duration_seconds) * 60
        # Tỷ lệ QRS detect đúng: Giả định dựa trên nhịp tim trung bình (60-100 bpm)
        expected_qrs_count = (60 / 60) * duration_seconds  # Giả định nhịp tim 60 bpm
        qrs_accuracy_ratio = qrs_count / max(1, expected_qrs_count) if qrs_count > 0 else 0
        rr_intervals = []
        last_peak = -1
        for i in range(len(self.first_120s_qrs)):
            if self.first_120s_qrs[i] == 1:
                if last_peak != -1:
                    rr_intervals.append(i - last_peak)
                last_peak = i
        hr_state = "Đều" if len(rr_intervals) > 1 and np.std(rr_intervals) / np.mean(rr_intervals) < 0.1 else "Không đều"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=====================================\n")
            f.write("         Báo Cáo ECG Bệnh Nhân       \n")
            f.write("=====================================\n")
            f.write(f"Tên bệnh nhân: {patient_name}\n")
            f.write(f"ID bệnh nhân: {patient_id}\n")
            f.write(f"Thời gian ghi: {timestamp}\n")
            f.write("-------------------------------------\n")
            f.write(f"Thời gian thu thập: {int(duration_seconds)} giây\n")
            f.write(f"Tần số lấy mẫu: {self.sampling_rate} Hz\n")
            f.write(f"Số mẫu: {self.first_120s_samples}\n")
            f.write("-------------------------------------\n")
            f.write(f"Kết quả QRS Detection:\n")
            f.write(f"  Số đỉnh QRS: {qrs_count}\n")
            f.write(f"  Nhịp tim: {int(heart_rate)} bpm\n")
            f.write(f"  Tỷ lệ QRS detect đúng: {qrs_accuracy_ratio:.6f}\n")
            f.write(f"  Trạng thái nhịp tim: {hr_state}\n")
            f.write("-------------------------------------\n")
            f.write("Dữ liệu 120 giây sau lọc:\n")
            f.write("  Giá trị: " + ", ".join(map(str, self.first_120s_filtered)) + "\n")
            f.write("  Đỉnh QRS (thời gian giây): " + ", ".join(map(str, np.where(np.array(self.first_120s_qrs) == 1)[0] / self.sampling_rate)) + "\n")
            f.write("=====================================\n")

        self.debug_text.append(f"DEBUG: Đã lưu báo cáo vào {filename}")

    def closeEvent(self, event):
        if self.serial_port:
            self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ECGDisplay()
    window.show()
    sys.exit(app.exec_())
import sys
import serial
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QTextEdit, QScrollArea
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class ECGDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hiển thị sóng ECG")
        self.setGeometry(100, 100, 1200, 800)

        # Set white background for the main window
        self.setStyleSheet("background-color: white;")

        # Configure UART port
        self.serial_port = serial.Serial('COM12', 115200, timeout=1)  # Replace 'COM12' with your port
        self.sampling_rate = 200  # Hz (based on TIM2 calculation: ~199.2 Hz, approximated to 200 Hz)
        self.display_samples = 2000  # Display 10 seconds of continuous data (200 Hz * 10 seconds)
        self.first_10s_samples = 2000  # 10 seconds of data for plots 2 and 3

        # Data for the plots
        self.raw_data = []  # Raw data (ADC)
        self.filtered_data = []  # Filtered data (bandpass)
        self.qrs_flags = []  # QRS flags received from UART
        self.first_10s_raw = []  # First 10 seconds of raw data
        self.first_10s_filtered = []  # First 10 seconds of filtered data
        self.first_10s_qrs = []  # First 10 seconds of QRS flags
        self.is_running = True  # Running/paused state
        self.first_10s_collected = False  # Flag to check if first 10 seconds are collected
        self.qrs_display_enabled = False  # Flag to control QRS display on plot 3
        self.frame_count = 0  # Counter to track frames for synchronization
        self.wait_for_qrs = False  # Flag to wait for QRS flags after first 10 seconds
        self.qrs_buffer = []  # Buffer to store QRS flags after first 10 seconds

        # Create the interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Plot 1: Continuous filtered signal
        self.plot_widget1 = pg.PlotWidget(title="Sóng ECG liên tục (Đã lọc)")
        self.plot_widget1.setBackground('w')  # White background
        self.plot_widget1.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget1.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget1.setYRange(-2048, 2048)  # Range for filtered signal
        self.plot_widget1.setXRange(0, 10)  # 10 seconds
        self.plot_widget1.getAxis('left').setTextPen('black')
        self.plot_widget1.getAxis('bottom').setTextPen('black')
        self.plot_data1 = self.plot_widget1.plot(pen='b')  # ECG line
        self.qrs_plot1 = self.plot_widget1.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)  # QRS points
        self.layout.addWidget(self.plot_widget1)

        # Button layout for Pause/Continue and Detect
        self.button_layout = QHBoxLayout()
        self.pause_button = QPushButton("Dừng")
        self.pause_button.setStyleSheet("background-color: lightgray; color: black;")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.button_layout.addWidget(self.pause_button)

        self.detect_button = QPushButton("Detect")
        self.detect_button.setStyleSheet("background-color: lightgray; color: black;")
        self.detect_button.clicked.connect(self.detect_qrs)
        self.button_layout.addWidget(self.detect_button)

        self.layout.addLayout(self.button_layout)

        # Plot 2: First 10 seconds of raw data
        self.plot_widget2 = pg.PlotWidget(title="10 giây đầu (Chưa lọc)")
        self.plot_widget2.setBackground('w')  # White background
        self.plot_widget2.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget2.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget2.setYRange(0, 4096)
        self.plot_widget2.setXRange(0, 10)
        self.plot_widget2.getAxis('left').setTextPen('black')
        self.plot_widget2.getAxis('bottom').setTextPen('black')
        self.plot_data2 = self.plot_widget2.plot(pen='r')  # ECG line
        self.qrs_plot2 = self.plot_widget2.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)  # QRS points
        self.layout.addWidget(self.plot_widget2)

        # Plot 3: First 10 seconds of filtered data
        self.plot_widget3 = pg.PlotWidget(title="10 giây đầu (Đã lọc)")
        self.plot_widget3.setBackground('w')  # White background
        self.plot_widget3.setLabel('left', 'Giá trị (ADC)', color='black')
        self.plot_widget3.setLabel('bottom', 'Thời gian (giây)', color='black')
        self.plot_widget3.setYRange(-2048, 2048)
        self.plot_widget3.setXRange(0, 10)
        self.plot_widget3.getAxis('left').setTextPen('black')
        self.plot_widget3.getAxis('bottom').setTextPen('black')
        self.plot_data3 = self.plot_widget3.plot(pen='g')  # ECG line
        self.qrs_plot3 = self.plot_widget3.plot(pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=10)  # QRS points
        self.layout.addWidget(self.plot_widget3)

        # Debug text area
        self.debug_layout = QHBoxLayout()
        self.debug_label = QLabel("Thông tin gỡ lỗi:")
        self.debug_label.setStyleSheet("color: black; font-size: 14px;")
        self.debug_layout.addWidget(self.debug_label)

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFixedHeight(100)
        self.debug_text.setStyleSheet("color: black; font-size: 12px; background-color: lightgray;")
        self.debug_layout.addWidget(self.debug_text)

        self.layout.addLayout(self.debug_layout)

        # Heart rate and state display
        self.hr_layout = QHBoxLayout()
        self.hr_label = QLabel("Nhịp tim: N/A bpm")
        self.hr_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_label)

        self.hr_state_label = QLabel("Trạng thái nhịp tim: N/A")
        self.hr_state_label.setStyleSheet("color: black; font-size: 14px;")
        self.hr_layout.addWidget(self.hr_state_label)

        self.layout.addLayout(self.hr_layout)

        # Timer to update data
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)  # Update every 50ms

        # Buffer to read UART data
        self.buffer = bytearray()

    def toggle_pause(self):
        if self.is_running:
            self.is_running = False
            self.pause_button.setText("Tiếp tục")
        else:
            self.is_running = True
            self.pause_button.setText("Dừng")

    def detect_qrs(self):
        # Enable QRS display on plot 3
        self.qrs_display_enabled = True
        self.update_plots()
        # Debug: Print first_10s_qrs to check QRS flags
        qrs_indices = np.where(np.array(self.first_10s_qrs) == 1)[0]
        self.debug_text.append(f"DEBUG: QRS indices in first_10s_qrs: {qrs_indices}")

    def update_data(self):
        if not self.is_running:
            return

        # Read data from UART
        while self.serial_port.in_waiting > 0:
            self.buffer.extend(self.serial_port.read(self.serial_port.in_waiting))

            # Process the buffer
            while len(self.buffer) > 0:
                # Check for debug messages (starting with "DEBUG:")
                if len(self.buffer) >= 6 and self.buffer[:6] == b"DEBUG:":
                    # Find the end of the debug message (newline)
                    newline_idx = self.buffer.find(b"\n")
                    if newline_idx == -1:
                        break  # Wait for more data

                    # Extract and process the debug message
                    debug_msg = self.buffer[:newline_idx].decode('utf-8', errors='ignore')
                    self.buffer = self.buffer[newline_idx + 1:]

                    # Display the debug message
                    self.debug_text.append(debug_msg)
                    # Auto-scroll to the bottom
                    self.debug_text.verticalScrollBar().setValue(self.debug_text.verticalScrollBar().maximum())

                    # Check if this message indicates QRS processing is complete
                    if debug_msg.startswith("DEBUG:TOTAL:"):
                        self.wait_for_qrs = True  # Start collecting QRS flags
                        self.qrs_buffer = []  # Reset QRS buffer
                        self.debug_text.append("DEBUG: Starting to collect QRS flags after processing")
                    continue

                # Check for data frame: Start byte (0xAA) to End byte (0xBB)
                if self.buffer[0] != 0xAA:
                    self.buffer.pop(0)
                    continue

                # Check frame length: Start byte (1) + 64 raw (2 bytes each) + 64 bandpass (2 bytes each) + 64 QRS flags (1 byte each) + End byte (1) = 322 bytes
                if len(self.buffer) < 322:
                    break

                # Check end byte
                if self.buffer[321] != 0xBB:
                    self.buffer.pop(0)
                    continue

                # Extract data from frame
                frame = self.buffer[:322]
                self.buffer = self.buffer[322:]

                # Parse data: 64 raw samples (2 bytes each) + 64 bandpass samples (2 bytes each) + 64 QRS flags (1 byte each)
                raw_values = []
                bandpass_values = []
                qrs_flags = []
                for i in range(64):
                    idx = 1 + i * 2  # Start position of each raw sample
                    value = (frame[idx] << 8) | frame[idx + 1]
                    raw_values.append(value)
                for i in range(64):
                    idx = 129 + i * 2  # Start position of each bandpass sample
                    value = (frame[idx] << 8) | frame[idx + 1]
                    if value & 0x8000:  # Check sign bit
                        value -= 65536  # Convert to negative
                    bandpass_values.append(value)
                for i in range(64):
                    idx = 257 + i  # Start position of QRS flags
                    qrs_flags.append(frame[idx])

                # Store continuous data
                self.raw_data.extend(raw_values)
                self.filtered_data.extend(bandpass_values)
                self.qrs_flags.extend(qrs_flags)

                # Limit data for continuous display (plot 1)
                if len(self.raw_data) > self.display_samples:
                    self.raw_data = self.raw_data[-self.display_samples:]
                    self.filtered_data = self.filtered_data[-self.display_samples:]
                    self.qrs_flags = self.qrs_flags[-self.display_samples:]

                # Store first 10 seconds for plots 2 and 3
                if not self.first_10s_collected:
                    self.first_10s_raw.extend(raw_values)
                    self.first_10s_filtered.extend(bandpass_values)
                    # Temporarily store zeros for QRS flags until we receive the correct ones
                    self.first_10s_qrs.extend([0] * len(qrs_flags))
                    # Debug: Print a sample of qrs_flags to verify
                    if len(self.first_10s_raw) % 200 == 0:  # Every 200 samples
                        self.debug_text.append(f"DEBUG: Sample QRS flags at sample {len(self.first_10s_raw)}: {qrs_flags[:10]}")
                    if len(self.first_10s_raw) >= self.first_10s_samples:
                        self.first_10s_collected = True
                        # Trim to exactly 2000 samples to ensure synchronization
                        self.first_10s_raw = self.first_10s_raw[:self.first_10s_samples]
                        self.first_10s_filtered = self.first_10s_filtered[:self.first_10s_samples]
                        self.first_10s_qrs = [0] * self.first_10s_samples  # Reset QRS flags
                        self.debug_text.append(f"DEBUG: First 10 seconds collected. Length of first_10s_qrs: {len(self.first_10s_qrs)}")
                        self.wait_for_qrs = True  # Start waiting for QRS flags
                        self.qrs_buffer = []  # Reset QRS buffer

                # Collect QRS flags after first 10 seconds
                if self.wait_for_qrs:
                    self.qrs_buffer.extend(qrs_flags)
                    # Check if we have collected enough QRS flags (2000 samples)
                    if len(self.qrs_buffer) >= self.first_10s_samples:
                        self.first_10s_qrs = self.qrs_buffer[:self.first_10s_samples]
                        self.wait_for_qrs = False  # Stop collecting QRS flags
                        self.debug_text.append(f"DEBUG: Collected QRS flags. Length of first_10s_qrs: {len(self.first_10s_qrs)}")
                        # Debug: Print initial QRS indices
                        qrs_indices = np.where(np.array(self.first_10s_qrs) == 1)[0]
                        self.debug_text.append(f"DEBUG: QRS indices after collecting flags: {qrs_indices}")
                        self.update_heart_rate()

        self.update_plots()

    def update_heart_rate(self):
        # Calculate number of QRS peaks in first_10s_qrs
        qrs_count = sum(self.first_10s_qrs)
        # Calculate heart rate (bpm) = (number of beats / duration in seconds) * 60
        duration_seconds = self.first_10s_samples / self.sampling_rate  # 10 seconds
        heart_rate = (qrs_count / duration_seconds) * 60
        self.hr_label.setText(f"Nhịp tim: {int(heart_rate)} bpm")

        # Determine heart rate state (simplified: check variability of RR intervals)
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
            if rr_std / rr_mean < 0.1:  # Low variability -> regular
                self.hr_state_label.setText("Trạng thái nhịp tim: Đều")
            else:
                self.hr_state_label.setText("Trạng thái nhịp tim: Không đều")
        else:
            self.hr_state_label.setText("Trạng thái nhịp tim: N/A")

    def update_plots(self):
        # Update plot 1: Continuous filtered signal
        if len(self.filtered_data) > 0:
            time_axis = np.linspace(0, 10, len(self.filtered_data))
            self.plot_data1.setData(time_axis, self.filtered_data)
            self.qrs_plot1.setData([], [])  # No QRS display on plot 1

        # Update plot 2: First 10 seconds of raw data
        if self.first_10s_collected:
            time_axis_10s = np.linspace(0, 10, len(self.first_10s_raw))
            self.plot_data2.setData(time_axis_10s, self.first_10s_raw)
            self.qrs_plot2.setData([], [])  # No QRS display on plot 2

        # Update plot 3: First 10 seconds of filtered data
        if self.first_10s_collected:
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
        # Close UART port when exiting
        self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ECGDisplay()
    window.show()
    sys.exit(app.exec_())
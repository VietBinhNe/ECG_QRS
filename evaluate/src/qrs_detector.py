import numpy as np

class QRSDetector:
    def __init__(self):
        self.MIN_DISTANCE = 40  # Khoảng cách tối thiểu giữa các đỉnh QRS (200 ms tại 200 Hz)
        self.MAX_PEAKS = 50
        self.STATIC_THRESHOLD_FACTOR = 2.0  # Hệ số nhân cho ngưỡng động
        self.MIN_AMPLITUDE_FACTOR = 1.5  # Hệ số nhân cho biên độ tối thiểu
        self.PEAK_WINDOW = 2
        self.PEAK_REFINE_WINDOW = 10
        self.peak_count = 0

    def init(self):
        self.peak_count = 0

    def detect(self, signal):
        qrs_flags = np.zeros(len(signal), dtype=np.uint8)
        self.init()

        # Bước 1: Tính giá trị trung bình và độ lệch chuẩn để tạo ngưỡng động
        signal_mean = np.mean(signal)
        signal_std = np.std(signal)
        dynamic_threshold = max(100, self.STATIC_THRESHOLD_FACTOR * signal_std)  # Ngưỡng động
        min_amplitude = max(150, self.MIN_AMPLITUDE_FACTOR * signal_std)  # Biên độ tối thiểu

        # Bước 2: Phát hiện đỉnh tiềm năng
        potential_peaks = []
        potential_values = []
        i = 0
        while i < len(signal):
            adjusted_signal = signal[i] - signal_mean
            if adjusted_signal > dynamic_threshold and adjusted_signal > 0 and len(potential_peaks) < self.MAX_PEAKS:
                is_peak = True
                for j in range(1, self.PEAK_WINDOW + 1):
                    if i >= j and adjusted_signal < (signal[i - j] - signal_mean):
                        is_peak = False
                        break
                    if i + j < len(signal) and adjusted_signal < (signal[i + j] - signal_mean):
                        is_peak = False
                        break
                if is_peak:
                    potential_peaks.append(i)
                    potential_values.append(adjusted_signal)
                    i += self.PEAK_WINDOW
                else:
                    i += 1
            else:
                i += 1

        # Bước 3: Hậu xử lý để loại bỏ FP
        if len(potential_peaks) > 1:
            valid_peaks = [potential_peaks[0]]
            for i in range(1, len(potential_peaks)):
                if potential_peaks[i] - valid_peaks[-1] >= self.MIN_DISTANCE:
                    valid_peaks.append(potential_peaks[i])
            potential_peaks = valid_peaks

        # Bước 4: Lọc đỉnh dựa trên biên độ tối thiểu
        for peak_idx in potential_peaks:
            if potential_values[potential_peaks.index(peak_idx)] > min_amplitude and self.peak_count < self.MAX_PEAKS:
                qrs_flags[peak_idx] = 1
                self.peak_count += 1

        return qrs_flags
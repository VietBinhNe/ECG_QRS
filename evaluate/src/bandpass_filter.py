import numpy as np

class BandpassFilter:
    def __init__(self):
        self.LOWPASS_WINDOW_SIZE = 5
        self.HIGHPASS_WINDOW_SIZE = 64
        self.lowpass_buffer = np.zeros(self.LOWPASS_WINDOW_SIZE, dtype=np.int32)
        self.highpass_buffer = np.zeros(self.HIGHPASS_WINDOW_SIZE, dtype=np.int32)
        self.lowpass_index = 0
        self.highpass_index = 0

    def init(self):
        self.lowpass_buffer.fill(0)
        self.highpass_buffer.fill(0)
        self.lowpass_index = 0
        self.highpass_index = 0

    def apply(self, new_sample):
        # Low-pass filter (~40 Hz cutoff)
        self.lowpass_buffer[1:] = self.lowpass_buffer[:-1]
        self.lowpass_buffer[0] = new_sample
        lowpass = np.sum(self.lowpass_buffer) * 384 // 1024  # (lowpass * 384) >> 10

        # High-pass filter (~0.5 Hz cutoff)
        self.highpass_buffer[1:] = self.highpass_buffer[:-1]
        self.highpass_buffer[0] = lowpass
        lowpass_average = np.sum(self.highpass_buffer) // 128  # lowpass_average >>= 7
        highpass = lowpass - lowpass_average

        # Overflow control
        if highpass > 32767:
            highpass = 32767
        if highpass < -32768:
            highpass = -32768

        return highpass

def apply_bandpass_filter(signal):
    filter = BandpassFilter()
    filter.init()
    filtered_signal = [filter.apply(int(sample)) for sample in signal]
    return np.array(filtered_signal)
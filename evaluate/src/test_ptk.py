import numpy as np
import matplotlib.pyplot as plt
from qrs_detector import QRSDetector

def load_from_file(filename='results/ecg_data.txt'):
    """Doc du lieu tu file txt."""
    with open(filename, 'r') as f:
        data = [int(line.strip()) for line in f if line.strip()]
    return np.array(data)

def resample_signal(signal, original_fs, target_fs, num_samples):
    return signal[:num_samples]  

def normalize_signal(signal, target_range=(0, 4095)):
    min_val, max_val = np.min(signal), np.max(signal)
    return ((signal - min_val) / (max_val - min_val)) * (target_range[1] - target_range[0]) + target_range[0]

def plot_signals(time_axis, original_signal, filtered_signal, qrs_indices_detected, title, filename):
    plt.figure(figsize=(12, 10))
    plt.subplot(2, 1, 1)
    plt.plot(time_axis, original_signal, label='Tin hieu goc tu board', color='blue', alpha=0.7)
    plt.title(f'{title} - Tin hieu goc')
    plt.ylabel('Gia tri (ADC)')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(time_axis, filtered_signal, label='Tin hieu da loc', color='orange', alpha=0.7)
    
    # Them marker cho cac dinh QRS da phat hien
    for det_idx in qrs_indices_detected:
        plt.plot(time_axis[det_idx], filtered_signal[det_idx], 'go', label='QRS phat hien' if 'QRS phat hien' not in plt.gca().get_legend_handles_labels()[1] else "", markersize=8)
    
    plt.title(f'{title} - Tin hieu da loc voi QRS')
    plt.xlabel('Thoi gian (giay)')
    plt.ylabel('Gia tri (ADC)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def main():
    # Duong dan va thong so
    data_file = 'results/ecg_data.txt'
    sample_duration = 10  # 10 giay
    target_fs = 200      # Tan so lay mau (du lieu tu board da la 200 Hz)
    num_samples = int(sample_duration * target_fs)

    # Doc du lieu tu file
    original_signal = load_from_file(data_file)
    if len(original_signal) != num_samples:
        print(f"Canh bao: So mau ({len(original_signal)}) khong khop voi {num_samples} mau (10 giay).")
        if len(original_signal) > num_samples:
            original_signal = original_signal[:num_samples]  # Cat ngan neu qua dai
        else:
            original_signal = np.pad(original_signal, (0, num_samples - len(original_signal)), 'constant')  # Bo sung neu thieu
            print(f"Da bo sung du lieu den {num_samples} mau.")
    print(f"Tin hieu goc tu file (dau 10 mau): {original_signal[:10]}")

    # Tai lay mau (chi de giu dong nhat, khong thuc su thay doi)
    resampled_signal = resample_signal(original_signal, target_fs, target_fs, num_samples)

    # Chuan hoa tin hieu
    normalized_signal = normalize_signal(resampled_signal)
    print(f"Tin hieu sau chuan hoa (dau 10 mau): {normalized_signal[:10]}")

    # Luu tin hieu chuan hoa vao file
    with open('results/normalized_board_signal.txt', 'w') as f:
        for value in normalized_signal:
            f.write(f"{value}\n")

    # Ap dung QRS detector
    qrs_detector = QRSDetector()
    qrs_detector.STATIC_THRESHOLD_FACTOR = 0.5  # Giam de tang TP
    qrs_detector.MIN_AMPLITUDE_FACTOR = 0.3    # Giam de tang TP
    qrs_detector.MIN_DISTANCE = 30             # Dieu chinh khoang cach toi thieu
    qrs_flags = qrs_detector.detect(normalized_signal)
    qrs_indices_detected = np.where(qrs_flags == 1)[0]
    print(f"So dinh QRS phat hien: {len(qrs_indices_detected)}")

    # Ve bieu do tin hieu
    time_axis = np.linspace(0, sample_duration, len(resampled_signal))
    plot_signals(time_axis, resampled_signal, normalized_signal, qrs_indices_detected,
                 'Phat hien QRS tu du lieu board',
                 'results/ptk_signal_comparison.png')

    print("Danh gia hoan tat. Kiem tra thu muc 'results/' de xem ket qua.")

if __name__ == '__main__':
    main()
import wfdb
import numpy as np
import scipy.signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from bandpass_filter import apply_bandpass_filter
from qrs_detector import QRSDetector

def resample_signal(signal, original_fs, target_fs, num_samples):
    """Tai lay mau tin hieu tu original_fs sang target_fs."""
    return scipy.signal.resample(signal, num_samples)

def normalize_signal(signal, target_range=(0, 4095)):
    """Chuan hoa tin hieu ve pham vi 0-4095 nhu du lieu ADC."""
    min_val, max_val = np.min(signal), np.max(signal)
    return ((signal - min_val) / (max_val - min_val)) * (target_range[1] - target_range[0]) + target_range[0]

def calculate_snr(signal, reference_signal):
    """Tinh ti le tin hieu tren nhieu (SNR)."""
    signal_power = np.mean(signal**2)
    noise = signal - reference_signal
    noise_power = np.mean(noise**2)
    if noise_power < 1e-10:  # Nguong nho de tranh chia cho 0
        return float('inf')
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def evaluate_qrs_detection(detected_indices, reference_indices, tolerance=10):
    """Danh gia phat hien QRS so voi chu thich chuan."""
    TP = 0
    FP = 0
    FN = 0
    matched_ref = set()
    tp_indices = []

    for det_idx in detected_indices:
        match_found = False
        for ref_idx in reference_indices:
            if abs(det_idx - ref_idx) <= tolerance:
                TP += 1
                matched_ref.add(ref_idx)
                tp_indices.append(det_idx)
                match_found = True
                break
        if not match_found:
            FP += 1

    FN = len(reference_indices) - len(matched_ref)

    sensitivity = TP / (TP + FN) if (TP + FN) > 0 else 0
    ppv = TP / (TP + FP) if (TP + FP) > 0 else 0

    return TP, FP, FN, sensitivity, ppv, tp_indices

def plot_signals(time_axis, original_signal, filtered_signal, qrs_indices_detected, resampled_qrs_indices, TP, FP, FN, sensitivity, ppv, title, filename):
    """Ve tin hieu goc va da loc trong 2 khung tren duoi, them marker QRS."""
    plt.figure(figsize=(12, 10))
    
    # Khung tren: Tin hieu goc
    plt.subplot(2, 1, 1)
    plt.plot(time_axis, original_signal, label='Tin hieu goc', color='blue', alpha=0.7)
    plt.title(f'{title} - Tin hieu goc')
    plt.ylabel('Gia tri (ADC)')
    plt.legend()
    plt.grid(True)
    
    # Khung duoi: Tin hieu da loc voi marker QRS
    plt.subplot(2, 1, 2)
    plt.plot(time_axis, filtered_signal, label='Tin hieu da loc', color='orange', alpha=0.7)
    
    # Them marker cho TP (xanh), FP (do), FN (den)
    tp_indices = []
    for det_idx in qrs_indices_detected:
        match_found = False
        for ref_idx in resampled_qrs_indices:
            if abs(det_idx - ref_idx) <= 10:
                tp_indices.append(det_idx)
                match_found = True
                break
        if not match_found:
            plt.plot(time_axis[det_idx], filtered_signal[det_idx], 'ro', label='FP' if 'FP' not in plt.gca().get_legend_handles_labels()[1] else "", markersize=8)
    
    for tp_idx in tp_indices:
        plt.plot(time_axis[tp_idx], filtered_signal[tp_idx], 'go', label='TP' if 'TP' not in plt.gca().get_legend_handles_labels()[1] else "", markersize=8)
    
    # Kiem tra FN
    for fn_idx in resampled_qrs_indices:
        is_fn = True
        for tp_idx in tp_indices:
            if abs(fn_idx - tp_idx) <= 10:
                is_fn = False
                break
        if is_fn:
            plt.plot(time_axis[fn_idx], filtered_signal[fn_idx], 'ko', label='FN' if 'FN' not in plt.gca().get_legend_handles_labels()[1] else "", markersize=8)
    
    plt.title(f'{title} - Tin hieu da loc voi QRS')
    plt.xlabel('Thoi gian (giay)')
    plt.ylabel('Gia tri (ADC)')
    plt.legend()
    plt.grid(True)
    
    # Them thong tin chi so len bieu do
    plt.text(0.02, 0.98, f'TP: {TP}, FP: {FP}, FN: {FN}\nSensitivity: {sensitivity:.2f}\nPPV: {ppv:.2f}',
             transform=plt.gca().transAxes, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def plot_frequency_spectrum(original_signal, filtered_signal, fs, filename):
    """Ve pho tan so cua tin hieu goc va da loc trong cung mot figure."""
    plt.figure(figsize=(12, 6))
    
    # Pho tan so cua tin hieu goc
    N = len(original_signal)
    yf = fft(original_signal)
    xf = fftfreq(N, 1 / fs)[:N//2]
    plt.plot(xf, 2.0/N * np.abs(yf[:N//2]), label='Tin hieu goc', alpha=0.7)
    
    # Pho tan so cua tin hieu da loc
    yf = fft(filtered_signal)
    plt.plot(xf, 2.0/N * np.abs(yf[:N//2]), label='Tin hieu da loc', alpha=0.7)
    
    plt.xlabel('Tan so (Hz)')
    plt.ylabel('Bien do')
    plt.title('Pho tan so')
    plt.grid(True)
    plt.legend()
    plt.xlim(0, 100)
    plt.savefig(filename)
    plt.close()

def main():
    # Duong dan va thong so
    data_dir = 'data'
    record_name = '100'
    sample_duration = 10  # 10 giay
    original_fs = 360  # Tan so lay mau cua MIT-BIH
    target_fs = 200   # Tan so muc tieu (theo STM32)
    num_samples = int(sample_duration * target_fs)

    # Doc du lieu MIT-BIH
    try:
        record = wfdb.rdsamp(f'{data_dir}/{record_name}', sampto=int(sample_duration * original_fs))
        signal = record[0][:, 0]  # Lay kenh dau tien
        annotation = wfdb.rdann(f'{data_dir}/{record_name}', 'atr', sampto=int(sample_duration * original_fs))
        qrs_indices = annotation.sample
        print(f"Tin hieu goc dau vao (dau 10 mau): {signal[:10]}")
    except Exception as e:
        print(f"Loi khi tai du lieu MIT-BIH: {e}")
        return

    # Tai lay mau va chuan hoa tin hieu
    resampled_signal = resample_signal(signal, original_fs, target_fs, num_samples)
    resampled_signal = normalize_signal(resampled_signal)
    resampled_qrs_indices = (qrs_indices * target_fs / original_fs).astype(int)
    print(f"Tin hieu sau tai lay mau va chuan hoa (dau 10 mau): {resampled_signal[:10]}")

    # Ap dung bo loc bandpass
    filtered_signal = apply_bandpass_filter(resampled_signal)
    print(f"Tin hieu sau bo loc (dau 10 mau): {filtered_signal[:10]}")

    # Tinh SNR
    snr_filtered = calculate_snr(filtered_signal, resampled_signal)

    # Ap dung QRS detector
    qrs_detector = QRSDetector()
    qrs_detector.STATIC_THRESHOLD_FACTOR = 1.5  # Dieu chinh he so nguong
    qrs_detector.MIN_AMPLITUDE_FACTOR = 1.0    # Dieu chinh he so bien do
    qrs_flags = qrs_detector.detect(filtered_signal)
    qrs_indices_detected = np.where(qrs_flags == 1)[0]

    # Danh gia QRS detection
    TP, FP, FN, sensitivity, ppv, tp_indices = evaluate_qrs_detection(qrs_indices_detected, resampled_qrs_indices)

    # Ve bieu do tin hieu
    time_axis = np.linspace(0, sample_duration, len(resampled_signal))
    plot_signals(time_axis, resampled_signal, filtered_signal, qrs_indices_detected, resampled_qrs_indices, TP, FP, FN, sensitivity, ppv,
                 'So sanh tin hieu ECG goc va da loc (MIT-BIH Record 100)',
                 'results/signal_comparison.png')

    # Ve pho tan so
    plot_frequency_spectrum(resampled_signal, filtered_signal, target_fs, 'results/frequency_spectrum.png')

    # Luu bao cao
    with open('results/evaluation_report.txt', 'w', encoding='utf-8') as f:
        f.write("Bao cao danh gia bo loc Bandpass (0.5-40 Hz)\n")
        f.write("======================================\n")
        f.write(f"Du lieu: MIT-BIH Arrhythmia Database, Record {record_name}\n")
        f.write(f"Thoi gian: {sample_duration} giay\n")
        f.write(f"Tan so lay mau: {target_fs} Hz (tai lay mau tu {original_fs} Hz)\n")
        f.write(f"So mau: {num_samples}\n")
        f.write("\nKet qua dinh luong:\n")
        f.write(f"SNR cua tin hieu da loc: {snr_filtered:.2f} dB\n")
        f.write(f"QRS Detection:\n")
        f.write(f"  True Positives (TP): {TP}\n")
        f.write(f"  False Positives (FP): {FP}\n")
        f.write(f"  False Negatives (FN): {FN}\n")
        f.write(f"  Sensitivity: {sensitivity:.2f}\n")
        f.write(f"  Positive Predictive Value (PPV): {ppv:.2f}\n")
        f.write("\nKet luan:\n")
        if snr_filtered > 0:
            f.write("Bo loc da loai bo nhieu hieu qua, voi SNR duong.\n")
        else:
            f.write("SNR thap, can kiem tra lai bo loc.\n")
        if sensitivity > 0.9 and ppv > 0.9:
            f.write("Bo loc giu tot cac dac trung QRS, voi Sensitivity va PPV cao.\n")
        else:
            f.write("Can dieu chinh bo loc hoac QRS detector de cai thien Sensitivity/PPV.\n")

    print("Danh gia hoan tat. Kiem tra thu muc 'results/' de xem ket qua.")

if __name__ == '__main__':
    main()
import serial
import numpy as np
import matplotlib.pyplot as plt

# Cấu hình cổng UART
SERIAL_PORT = 'COM12'  # Cổng UART của bạn
BAUD_RATE = 115200
SAMPLING_RATE = 200  # Hz
TOTAL_TIME = 10  # Giây
SKIP_TIME = 2  # Giây
SAMPLES_PER_UPDATE = 64  # Số mẫu mỗi gói dữ liệu

# Tính toán số mẫu và gói dữ liệu
total_samples = SAMPLING_RATE * TOTAL_TIME
total_updates = total_samples // SAMPLES_PER_UPDATE  # Số gói dữ liệu cần thu thập
skip_samples = SAMPLING_RATE * SKIP_TIME
skip_updates = skip_samples // SAMPLES_PER_UPDATE  # Số gói dữ liệu cần bỏ qua
display_samples = total_samples - skip_samples
display_updates = total_updates - skip_updates

# Mở cổng UART
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Đã kết nối thành công với cổng {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"Lỗi khi kết nối cổng {SERIAL_PORT}: {e}")
    exit()

# Gửi lệnh 'S' để yêu cầu dữ liệu từ STM32
try:
    ser.write(b'S')
    print("Đã gửi lệnh 'S' để yêu cầu dữ liệu từ STM32")
except Exception as e:
    print(f"Lỗi khi gửi lệnh 'S': {e}")
    ser.close()
    exit()

# Khởi tạo mảng để lưu dữ liệu
data_buffer = np.zeros(total_samples)  # Lưu tín hiệu ADC thô
qrs_flags_buffer = np.zeros(total_samples)  # Lưu cờ QRS
updates_received = 0

# Thu thập dữ liệu
print(f"Đang thu thập dữ liệu trong {TOTAL_TIME} giây ({total_updates} gói dữ liệu)...")
while updates_received < total_updates:
    while ser.in_waiting == 0:
        pass  # Chờ dữ liệu từ UART
    
    line_data = ser.readline().decode('utf-8').strip()
    print(f"Dữ liệu nhận được: {line_data}")

    # Bỏ qua các dòng không phải dữ liệu chính (ví dụ: dòng debug "BP:")
    if "BP:" in line_data:
        continue

    try:
        # Dữ liệu có dạng: "value1,value2,...,value128" (64 giá trị ADC + 64 cờ QRS)
        data = list(map(int, line_data.split(',')))
        if len(data) == 128:  # Kiểm tra số lượng giá trị
            adc_values = data[:SAMPLES_PER_UPDATE]  # 64 giá trị ADC
            qrs_flags = data[SAMPLES_PER_UPDATE:]  # 64 cờ QRS

            # Lưu dữ liệu vào mảng
            start_idx = updates_received * SAMPLES_PER_UPDATE
            end_idx = start_idx + SAMPLES_PER_UPDATE
            data_buffer[start_idx:end_idx] = adc_values
            qrs_flags_buffer[start_idx:end_idx] = qrs_flags
            updates_received += 1
        else:
            print(f"Dữ liệu không đủ 128 giá trị, nhận được {len(data)} giá trị")
    except ValueError as e:
        print(f"Lỗi khi chuyển đổi dữ liệu: {e}")

# Đóng cổng UART
ser.close()
print("Đã đóng kết nối UART")

# Bỏ qua 2 giây đầu tiên
display_data = data_buffer[skip_samples:skip_samples + display_samples]
display_qrs_flags = qrs_flags_buffer[skip_samples:skip_samples + display_samples]

# Tạo mảng thời gian (8 giây)
x_time = np.linspace(SKIP_TIME, TOTAL_TIME, display_samples)

# Tìm vị trí các đỉnh R
qrs_indices = np.where(display_qrs_flags == 1)[0]
qrs_timestamps = x_time[qrs_indices]
qrs_values = display_data[qrs_indices]

# Vẽ biểu đồ
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x_time, display_data, '-', label='ECG Signal', color='blue')  # Sóng thô
ax.plot(qrs_timestamps, qrs_values, 'ro', markersize=10, label='R Peaks')  # Đỉnh R
ax.set_ylim(0, 4095)
ax.set_xlim(SKIP_TIME, TOTAL_TIME)
ax.set_xlabel('Thời gian (giây)')
ax.set_ylabel('Giá trị ADC')
ax.set_title('Dạng sóng ECG với đỉnh R (Giây 2 đến 10)')
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.show()

# Phần mở rộng (dành cho tương lai nếu STM32 gửi thêm dữ liệu trung gian)
# Nếu firmware STM32 được sửa để gửi dữ liệu các giai đoạn lọc (BL, BP, Notch60, v.v.),
# bạn có thể mở rộng code để hiển thị các sóng tương tự như đoạn code trước đó.
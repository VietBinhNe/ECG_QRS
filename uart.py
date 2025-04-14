# import serial
# import time
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation

# # Cấu hình cổng COM
# port = 'COM12'
# baudrate = 115200

# # Mở kết nối UART
# try:
#     ser = serial.Serial(port, baudrate, timeout=1)
#     print(f"Đã kết nối thành công với cổng {port}")
# except serial.SerialException as e:
#     print(f"Lỗi khi kết nối cổng {port}: {e}")
#     exit()

# # Gửi lệnh 'S' để kích hoạt STM32 gửi dữ liệu
# try:
#     ser.write(b'S')
#     print("Đã gửi lệnh 'S' để yêu cầu dữ liệu từ STM32")
# except Exception as e:
#     print(f"Lỗi khi gửi lệnh 'S': {e}")

# # Khởi tạo dữ liệu cho đồ thị
# WINDOW_SIZE = 320  # Số mẫu hiển thị trên đồ thị (5 giây dữ liệu với 64 mẫu/giây)
# SAMPLES_PER_UPDATE = 64  # Số mẫu mỗi lần cập nhật
# WINDOW_TIME = WINDOW_SIZE / 64  # Thời gian hiển thị trên đồ thị (giây)

# data_buffer = np.zeros(WINDOW_SIZE)  # Mảng lưu trữ dữ liệu ADC
# qrs_positions = []  # Lưu vị trí QRS (chỉ số mẫu trong cửa sổ)
# qrs_timestamps = []  # Lưu thời gian QRS (giây)
# qrs_samples = []  # Lưu chỉ số mẫu toàn cục của QRS

# # Cài đặt đồ thị
# fig, ax = plt.subplots(figsize=(10, 6))
# x = np.linspace(0, WINDOW_TIME, WINDOW_SIZE)  # Trục x là thời gian (giây)
# line, = ax.plot(x, data_buffer, '-', label='ECG Signal')
# qrs_markers, = ax.plot([], [], 'ro', markersize=10, label='QRS Peaks')
# ax.set_ylim(0, 4095)
# ax.set_xlim(0, WINDOW_TIME)
# ax.set_xlabel('Thời gian (giây)')
# ax.set_ylabel('Giá trị ADC')
# ax.set_title('Dạng sóng ECG với đỉnh QRS')
# plt.grid(True)
# plt.legend()

# # Biến để theo dõi vị trí mẫu hiện tại
# current_sample_index = 0

# # Hàm cập nhật đồ thị
# def update_plot(frame):
#     global data_buffer, qrs_positions, qrs_timestamps, qrs_samples, current_sample_index
#     while ser.in_waiting > 0:
#         # Đọc một dòng dữ liệu
#         line_data = ser.readline().decode('utf-8').strip()
#         print(f"Dữ liệu nhận được: {line_data}")

#         # Bỏ qua dữ liệu debug (có chứa "BP:")
#         if "BP:" in line_data:
#             continue

#         try:
#             # Dữ liệu gồm 64 mẫu ADC + 64 cờ QRS
#             data = list(map(int, line_data.split(',')))
#             if len(data) == 128:  # 64 mẫu ADC + 64 cờ QRS
#                 adc_values = data[:SAMPLES_PER_UPDATE]  # 64 mẫu ADC
#                 qrs_flags = data[SAMPLES_PER_UPDATE:]   # 64 cờ QRS

#                 # Dịch chuyển dữ liệu cũ và thêm dữ liệu mới
#                 data_buffer[:-SAMPLES_PER_UPDATE] = data_buffer[SAMPLES_PER_UPDATE:]
#                 data_buffer[-SAMPLES_PER_UPDATE:] = adc_values

#                 # Tìm vị trí QRS từ cờ QRS
#                 for i in range(SAMPLES_PER_UPDATE):
#                     if qrs_flags[i] == 1:
#                         # Tính chỉ số mẫu toàn cục của QRS
#                         sample_index = current_sample_index + i
#                         # Tính vị trí QRS trong cửa sổ hiện tại
#                         pos = sample_index % WINDOW_SIZE
#                         # Tính thời gian QRS (giây)
#                         timestamp = (sample_index / 64) * WINDOW_TIME
#                         timestamp = timestamp % WINDOW_TIME  # Đảm bảo thời gian nằm trong cửa sổ
#                         qrs_samples.append(sample_index)
#                         qrs_positions.append(pos)
#                         qrs_timestamps.append(timestamp)
#                         print(f"QRS detected at sample {sample_index}, position in window: {pos}, timestamp: {timestamp}")

#                 current_sample_index += SAMPLES_PER_UPDATE

#                 # Lọc các vị trí QRS ngoài cửa sổ hiển thị
#                 new_samples = []
#                 new_positions = []
#                 new_timestamps = []
#                 for sample, pos, ts in zip(qrs_samples, qrs_positions, qrs_timestamps):
#                     # Tính số mẫu đã trôi qua từ khi QRS được phát hiện
#                     elapsed_samples = current_sample_index - sample
#                     if elapsed_samples < WINDOW_SIZE:
#                         # QRS vẫn nằm trong cửa sổ hiển thị
#                         relative_pos = (WINDOW_SIZE - elapsed_samples) % WINDOW_SIZE
#                         relative_ts = (WINDOW_TIME - (elapsed_samples / 64) * WINDOW_TIME) % WINDOW_TIME
#                         new_samples.append(sample)
#                         new_positions.append(relative_pos)
#                         new_timestamps.append(relative_ts)

#                 qrs_samples = new_samples
#                 qrs_positions = new_positions
#                 qrs_timestamps = new_timestamps

#                 # Cập nhật giá trị y của các điểm QRS
#                 qrs_values = [data_buffer[pos] for pos in qrs_positions]
#                 print(f"QRS samples: {qrs_samples}")
#                 print(f"QRS positions: {qrs_positions}")
#                 print(f"QRS timestamps: {qrs_timestamps}")
#                 print(f"QRS values: {qrs_values}")

#                 # Cập nhật đồ thị
#                 qrs_markers.set_data(qrs_timestamps, qrs_values)
#                 line.set_ydata(data_buffer)
#             else:
#                 print(f"Dữ liệu không đủ 128 giá trị, nhận được {len(data)} giá trị")
#         except ValueError as e:
#             print(f"Lỗi khi chuyển đổi dữ liệu: {e}")
#     return line, qrs_markers

# # Chạy animation
# ani = FuncAnimation(fig, update_plot, interval=100, blit=True)

# # Hiển thị đồ thị
# try:
#     plt.show()
# except KeyboardInterrupt:
#     print("Dừng chương trình")

# # Đóng kết nối UART
# ser.close()
# print("Đã đóng kết nối UART")

import serial
import numpy as np
import matplotlib.pyplot as plt

port = 'COM12'
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Đã kết nối thành công với cổng {port}")
except serial.SerialException as e:
    print(f"Lỗi khi kết nối cổng {port}: {e}")
    exit()

try:
    ser.write(b'S')
    print("Đã gửi lệnh 'S' để yêu cầu dữ liệu từ STM32")
except Exception as e:
    print(f"Lỗi khi gửi lệnh 'S': {e}")

TOTAL_SAMPLES = 384 
SAMPLES_PER_UPDATE = 64  
TOTAL_UPDATES = TOTAL_SAMPLES // SAMPLES_PER_UPDATE  

data_buffer = np.zeros(TOTAL_SAMPLES)  
qrs_flags_buffer = np.zeros(TOTAL_SAMPLES) 
updates_received = 0  

while updates_received < TOTAL_UPDATES:
    while ser.in_waiting == 0:
        pass  
    
    line_data = ser.readline().decode('utf-8').strip()
    print(f"Dữ liệu nhận được: {line_data}")

    if "BP:" in line_data:
        continue

    try:
        data = list(map(int, line_data.split(',')))
        if len(data) == 128:  
            adc_values = data[:SAMPLES_PER_UPDATE]  
            qrs_flags = data[SAMPLES_PER_UPDATE:]   

            start_idx = updates_received * SAMPLES_PER_UPDATE
            end_idx = start_idx + SAMPLES_PER_UPDATE
            data_buffer[start_idx:end_idx] = adc_values
            qrs_flags_buffer[start_idx:end_idx] = qrs_flags
            updates_received += 1
        else:
            print(f"Dữ liệu không đủ 128 giá trị, nhận được {len(data)} giá trị")
    except ValueError as e:
        print(f"Lỗi khi chuyển đổi dữ liệu: {e}")

ser.close()
print("Đã đóng kết nối UART")

START_TIME = 2  
END_TIME = 6    
START_SAMPLE = int(START_TIME * 64)  
END_SAMPLE = int(END_TIME * 64)      
DISPLAY_SAMPLES = END_SAMPLE - START_SAMPLE  

display_data = data_buffer[START_SAMPLE:END_SAMPLE]
display_qrs_flags = qrs_flags_buffer[START_SAMPLE:END_SAMPLE]

x_time = np.linspace(START_TIME, END_TIME, DISPLAY_SAMPLES)  
qrs_indices = np.where(display_qrs_flags == 1)[0]  
qrs_timestamps = x_time[qrs_indices]  
qrs_values = display_data[qrs_indices]  

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x_time, display_data, '-', label='ECG Signal')  
ax.plot(qrs_timestamps, qrs_values, 'ro', markersize=10, label='R Peaks')  
ax.set_ylim(0, 4095)
ax.set_xlim(START_TIME, END_TIME)
ax.set_xlabel('Thời gian (giây)')
ax.set_ylabel('Giá trị ADC')
ax.set_title('Dạng sóng ECG với đỉnh R (Giây 2 đến 6)')
plt.grid(True)
plt.legend()
plt.show()
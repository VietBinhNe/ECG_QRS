import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

port = 'COM12' 
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Connected successfully with port : {port}")
except serial.SerialException as e:
    print(f"Error {port}: {e}")
    exit()

# "S" to trigger STM32
try:
    ser.write(b'S')
    print("Sent S")
except Exception as e:
    print(f"Error': {e}")

WINDOW_SIZE = 256  # 64 * 4 = 256
data_buffer = np.zeros(WINDOW_SIZE)

fig, ax = plt.subplots()
x = np.arange(0, WINDOW_SIZE)  
line, = ax.plot(x, data_buffer, '-')  
ax.set_ylim(0, 4095)  # ADC 12-bit: 0-4095
ax.set_xlabel('Samples')
ax.set_ylabel('ADC Value')
ax.set_title('STM32 ECG Signal')
plt.grid(True)

def update_plot(frame):
    global data_buffer
    if ser.in_waiting > 0:
        line_data = ser.readline().decode('utf-8').strip()
        print(f"Data received: {line_data}")  # Debug

        try:
            data = list(map(int, line_data.split(',')))
            if len(data) == 64: 
                data_buffer[:-64] = data_buffer[64:]  
                data_buffer[-64:] = data  
                line.set_ydata(data_buffer)  
            else:
                print(f"Not enough 64 samples, just {len(data)} sample(s)")
        except ValueError as e:
            print(f"Error: {e}")
    return line,

ani = FuncAnimation(fig, update_plot, interval=100, blit=True)  # 100ms update

try:
    plt.show()
except KeyboardInterrupt:
    print("Stop")

ser.close()
print("Closed UART!")
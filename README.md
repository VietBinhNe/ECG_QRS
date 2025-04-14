<!-- <div style="text-align: center; background-color: #8F98E3; font-family: 'Trebuchet MS', Arial, sans-serif; color: white; padding: 10px; font-size: 25px; font-weight: bold; border-radius: 0 0 0 0; box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.2);">
  Detect QRS peak of ECG wave on STM32y 🫁
</div> -->
# Detect QRS peak of ECG wave on STM32 


### 📑 <font color=Gree><b>0.</b></font> <font color=Gree> Overview </font> </br>

This project implements a real-time QRS detection system for ECG signals using the STM32F411 microcontroller. The system is based on the Pan-Tompkins algorithm, a well-known method for detecting QRS complexes (specifically the R peaks) in ECG signals. The project captures ECG data via ADC, processes it on the STM32F411, and sends the processed data (ADC values and QRS flags) to a Python script for visualization.

The system operates at a sampling rate of 64 Hz, collecting 6 seconds of data (384 samples) and displaying a static plot of the ECG signal from the 2nd to the 6th second (256 samples). The R peaks are marked with red dots on the plot.

Features:
- Real-time QRS detection using the Pan-Tompkins algorithm.

- ECG signal acquisition at 64 Hz using the STM32F411's ADC.

- Signal preprocessing with bandpass filtering, derivative, squaring, and moving-window integration.

- Adaptive thresholding to detect R peaks.

- Data transmission via UART to a Python script for visualization.

- Static visualization of the ECG signal and R peaks from the 2nd to the 6th second.

### ⚙️ <font color=Gree><b> 1. </b></font> <font color=Gree> Hardware Requirements </font> </br>

- STM32F411 Microcontroller

- ECG Sensor: AD8232 

- USB-to-Serial Adapter: For UART communication between STM32 and PC.

- PC with Python Installed: For running the visualization script.

### 💽 <font color=Gree><b> 2. </b></font> <font color=Gree> Software Requirements </font> </br>

- STM32CubeIDE: For compiling and uploading the firmware to the STM32F411.

- Python 3.x: For running the visualization script.

- Required Python Libraries:
  - pyserial: For UART communication.
  - numpy: For numerical operations.
  - matplotlib: For plotting the ECG signal.

### 📖 <font color=Gree><b> 3. </b></font> <font color=Gree> References </font> </br>

- Pan, J., & Tompkins, W. J. (1985). "A Real-Time QRS Detection Algorithm." IEEE Transactions on Biomedical Engineering, Vol. BME-32, No. 3, pp. 230-236.
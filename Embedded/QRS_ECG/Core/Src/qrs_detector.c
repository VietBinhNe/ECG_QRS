/**
 * @file       qrs_detector.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-10
 * @author     Binh Nguyen
 * @brief      Implementation of QRS detection using Pan-Tompkins algorithm on STM32.
 * @note       Processes ADC samples to detect QRS peaks in ECG signals at 64 Hz.
 */

#include "qrs_detector.h"
#include "mylib.h"

/* Private defines ---------------------------------------------------- */
#define QRS_SIGNAL_FACTOR      0.1   /*!< Factor for signal level in threshold calculation */
#define QRS_NOISE_FACTOR       0.5   /*!< Factor for noise level in threshold calculation */
#define QRS_RR_LIMIT_LOW       0.92  /*!< Lower limit for RR interval (92% of average) */
#define QRS_RR_LIMIT_HIGH      1.16  /*!< Upper limit for RR interval (116% of average) */
#define QRS_SEARCHBACK_FACTOR  1.66  /*!< Factor for searchback window (166% of RR average) */

/* Private function prototypes ---------------------------------------- */
static int32_t bandpass_filter(QRSDetector* detector, int32_t new_sample);
static int32_t derivative(QRSDetector* detector, int32_t filtered);
static int32_t squaring(int32_t deriv);
static int32_t moving_window_integration(QRSDetector* detector, int32_t squared);
static void update_thresholds(QRSDetector* detector, int32_t peak, uint8_t is_qrs);
static void update_rr_intervals(QRSDetector* detector, uint32_t rr);
static int32_t calculate_slope(QRSDetector* detector);

/* Function definitions ----------------------------------------------- */
void QRSDetector_Init(QRSDetector* detector)
{
    for (uint8_t i = 0; i < 16; i++) detector->bandpass_buffer[i] = 0;
    for (uint8_t i = 0; i < 5; i++) detector->deriv_buffer[i] = 0;
    for (uint8_t i = 0; i < QRS_WINDOW_SIZE; i++) detector->integ_buffer[i] = 0;

    detector->integ_index = 0;
    detector->signal_level = 0;
    detector->noise_level = 0;
    detector->threshold_i1 = 0;
    detector->threshold_i2 = 0;
    detector->last_peak_time = 0;
    detector->sample_count = 0;
    detector->learning_phase = 1;

    for (uint8_t i = 0; i < 8; i++) detector->rr_intervals[i] = 0;
    detector->rr_index = 0;
    detector->rr_average1 = 0;
    detector->rr_average2 = 0;
    detector->rr_count = 0;

    detector->last_qrs_slope = 0;
}

uint8_t QRSDetector_Process(QRSDetector* detector, uint16_t new_sample)
{
    // Step 1: Preprocessing
    int32_t bandpass = bandpass_filter(detector, new_sample);
    int32_t deriv = derivative(detector, bandpass);
    int32_t squared = squaring(deriv);
    int32_t integrated = moving_window_integration(detector, squared);

    // Debug: Gửi giá trị sau từng bước xử lý
    char debug_msg[100];
    sprintf(debug_msg, "BP:%ld,Deriv:%ld,Sq:%ld,Integ:%ld\n", bandpass, deriv, squared, integrated);
    HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);

    // Step 2: Learning phase (first 2 seconds)
    if (detector->learning_phase) {
        detector->sample_count++;
        if (detector->sample_count < QRS_LEARNING_SAMPLES) {
            if (integrated > detector->signal_level) detector->signal_level = integrated;
            detector->noise_level += integrated;
            return 0;
        } else {
            detector->noise_level /= QRS_LEARNING_SAMPLES;
            detector->signal_level /= 2;
            detector->threshold_i1 = detector->noise_level + QRS_SIGNAL_FACTOR * (detector->signal_level - detector->noise_level);
            detector->threshold_i2 = QRS_NOISE_FACTOR * detector->threshold_i1;
            detector->learning_phase = 0;
            detector->sample_count = 0;

            // Debug: Gửi ngưỡng sau giai đoạn học
            sprintf(debug_msg, "ThreshI1:%ld,ThreshI2:%ld\n", detector->threshold_i1, detector->threshold_i2);
            HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);
        }
    }

    // Step 3: Peak detection
    uint8_t is_qrs = 0;
    if (integrated > detector->threshold_i1) {
        uint32_t time_since_last = detector->sample_count - detector->last_peak_time;

        // Check refractory period
        if (time_since_last < QRS_REFRACTORY_PERIOD) {
            update_thresholds(detector, integrated, 0);
            return 0;
        }

        // T-wave discrimination
        if (time_since_last < QRS_TWAVE_PERIOD && detector->last_qrs_slope > 0) {
            int32_t current_slope = calculate_slope(detector);
            if (current_slope < detector->last_qrs_slope / 2) {
                update_thresholds(detector, integrated, 0);
                return 0;
            }
        }

        // Valid QRS peak
        is_qrs = 1;
        detector->last_qrs_slope = calculate_slope(detector);
        update_thresholds(detector, integrated, 1);
        uint32_t rr = time_since_last;
        update_rr_intervals(detector, rr);
        detector->last_peak_time = detector->sample_count;
    } else if (detector->rr_average1 > 0 &&
               (detector->sample_count - detector->last_peak_time) > (uint32_t)(QRS_SEARCHBACK_FACTOR * detector->rr_average1)) {
        if (integrated > detector->threshold_i2) {
            is_qrs = 1;
            detector->last_qrs_slope = calculate_slope(detector);
            update_thresholds(detector, integrated, 1);
            uint32_t rr = detector->sample_count - detector->last_peak_time;
            update_rr_intervals(detector, rr);
            detector->last_peak_time = detector->sample_count;
        }
    }

    detector->sample_count++;
    return is_qrs;
}

/* Private definitions ----------------------------------------------- */
static int32_t bandpass_filter(QRSDetector* detector, int32_t new_sample)
{
    for (uint8_t i = 15; i > 0; i--) detector->bandpass_buffer[i] = detector->bandpass_buffer[i - 1];
    detector->bandpass_buffer[0] = new_sample;

    // Low-pass filter (cutoff ~11 Hz)
    int32_t lowpass = 2 * detector->bandpass_buffer[0] - detector->bandpass_buffer[12] +
                      detector->bandpass_buffer[0] - 2 * detector->bandpass_buffer[6] + detector->bandpass_buffer[12];

    // High-pass filter (cutoff ~5 Hz)
    int32_t highpass = detector->bandpass_buffer[0] - detector->bandpass_buffer[15] + lowpass;

    return highpass;
}

static int32_t derivative(QRSDetector* detector, int32_t filtered)
{
    for (uint8_t i = 4; i > 0; i--) detector->deriv_buffer[i] = detector->deriv_buffer[i - 1];
    detector->deriv_buffer[0] = filtered;

    int32_t deriv = (1 * detector->deriv_buffer[0] + 2 * detector->deriv_buffer[1] -
                     2 * detector->deriv_buffer[3] - 1 * detector->deriv_buffer[4]) / 8;
    return deriv;
}

static int32_t squaring(int32_t deriv)
{
    return deriv * deriv;
}

static int32_t moving_window_integration(QRSDetector* detector, int32_t squared)
{
    detector->integ_buffer[detector->integ_index] = squared;
    detector->integ_index = (detector->integ_index + 1) % QRS_WINDOW_SIZE;

    int32_t sum = 0;
    for (uint8_t i = 0; i < QRS_WINDOW_SIZE; i++) sum += detector->integ_buffer[i];
    return sum / QRS_WINDOW_SIZE;
}

static void update_thresholds(QRSDetector* detector, int32_t peak, uint8_t is_qrs)
{
    if (is_qrs) {
        detector->signal_level = 0.125 * peak + 0.875 * detector->signal_level;
    } else {
        detector->noise_level = 0.125 * peak + 0.875 * detector->noise_level;
    }

    detector->threshold_i1 = detector->noise_level + QRS_SIGNAL_FACTOR * (detector->signal_level - detector->noise_level);
    detector->threshold_i2 = QRS_NOISE_FACTOR * detector->threshold_i1;
}

static void update_rr_intervals(QRSDetector* detector, uint32_t rr)
{
    detector->rr_intervals[detector->rr_index] = rr;
    detector->rr_index = (detector->rr_index + 1) % 8;
    if (detector->rr_count < 8) detector->rr_count++;

    uint32_t sum1 = 0;
    for (uint8_t i = 0; i < detector->rr_count; i++) sum1 += detector->rr_intervals[i];
    detector->rr_average1 = sum1 / detector->rr_count;

    uint32_t sum2 = 0;
    uint8_t count2 = 0;
    for (uint8_t i = 0; i < detector->rr_count; i++) {
        if (detector->rr_intervals[i] >= (uint32_t)(QRS_RR_LIMIT_LOW * detector->rr_average1) &&
            detector->rr_intervals[i] <= (uint32_t)(QRS_RR_LIMIT_HIGH * detector->rr_average1)) {
            sum2 += detector->rr_intervals[i];
            count2++;
        }
    }
    detector->rr_average2 = (count2 > 0) ? (sum2 / count2) : detector->rr_average1;
}

static int32_t calculate_slope(QRSDetector* detector)
{
    int32_t slope = detector->deriv_buffer[0] - detector->deriv_buffer[2];
    return (slope > 0) ? slope : -slope;
}

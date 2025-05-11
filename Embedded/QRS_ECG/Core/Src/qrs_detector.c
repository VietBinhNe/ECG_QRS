/**
 * @file       qrs_detector.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.1.0
 * @date       2025-05-11
 * @author     Binh Nguyen
 *
 * @brief      Implementation of QRS detection algorithm for STM32 using low static threshold with smart post-processing.
 *
 * @note       This file implements a low static threshold algorithm with smart post-processing for QRS complexes.
 * @example    main.c
 *             Main application using the QRS detector to identify QRS complexes.
 */

/* Includes ----------------------------------------------------------- */
#include "qrs_detector.h"
#include "mylib.h"
#include <stdio.h>
#include <string.h>

/* Private defines ---------------------------------------------------- */
/* None */

/* Private enumerate/structure ---------------------------------------- */
/* None */

/* Private macros ----------------------------------------------------- */
/* None */

/* Public variables --------------------------------------------------- */
/* None */

/* Private variables -------------------------------------------------- */
/* None */

/* Private function prototypes ---------------------------------------- */
/* None */

/* Function definitions ----------------------------------------------- */
void QRSDetector_Init(QRSDetector* detector)
{
    detector->peak_count = 0;
}

void QRSDetector_Detect(QRSDetector* detector, int32_t* signal, uint8_t* qrs_flags)
{
    // Initialize output array
    for (uint16_t i = 0; i < 2000; i++) {
        qrs_flags[i] = 0;
    }

    // Reset detector state
    QRSDetector_Init(detector);

    // Step 1: Calculate the mean of the signal to remove DC component
    int64_t signal_sum = 0;
    for (uint16_t i = 0; i < 2000; i++) {
        signal_sum += signal[i];
    }
    int32_t signal_mean = (int32_t)(signal_sum / 2000);

    // Debug: Send signal mean
    char debug_msg[50];
    sprintf(debug_msg, "DEBUG:MEAN:%ld\n", signal_mean);
    HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);

    // Step 2: Detect potential QRS peaks using static threshold
    uint16_t potential_peaks[2000];
    int32_t potential_values[2000];
    uint16_t potential_count = 0;

    for (uint16_t i = 0; i < 2000; i++) {
        // Remove DC component
        int32_t adjusted_signal = signal[i] - signal_mean;

        // Debug: Send signal every 100 samples
        if (i % 100 == 0) {
            sprintf(debug_msg, "DEBUG:SAMPLE:%u:%ld\n", i, adjusted_signal);
            HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);
        }

        // Step 3: Check if signal exceeds static threshold
        if (adjusted_signal > QRS_STATIC_THRESHOLD && adjusted_signal > 0 && potential_count < QRS_MAX_PEAKS) {
            // Check if this is a local maximum
            int32_t is_peak = 1;
            for (uint16_t j = 1; j <= QRS_PEAK_WINDOW; j++) {
                if (i >= j && adjusted_signal < (signal[i - j] - signal_mean)) {
                    is_peak = 0;
                    break;
                }
                if (i + j < 2000 && adjusted_signal < (signal[i + j] - signal_mean)) {
                    is_peak = 0;
                    break;
                }
            }

            // Step 4: Mark potential QRS peak if it is a local maximum
            if (is_peak) {
                potential_peaks[potential_count] = i;
                potential_values[potential_count] = adjusted_signal;
                potential_count++;

                // Debug: Send potential peak
                sprintf(debug_msg, "DEBUG:POTENTIAL_PEAK:%u:%ld\n", i, adjusted_signal);
                HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);

                // Skip the window to avoid multiple detections
                i += QRS_PEAK_WINDOW;
            }
        }
    }

    // Step 5: Estimate heart rate to determine minimum distance
    uint16_t min_distance = QRS_MIN_DISTANCE; // Default minimum distance (~200ms at 200 Hz)
    if (potential_count > 1) {
        // Calculate average interval between potential peaks
        int32_t total_interval = potential_peaks[potential_count - 1] - potential_peaks[0];
        int32_t avg_interval = total_interval / (potential_count - 1);
        // Use 50% of the average interval as the minimum distance
        min_distance = (uint16_t)(avg_interval / 2);
        if (min_distance < 30) min_distance = 30; // Ensure at least 150ms
        if (min_distance > 60) min_distance = 60; // Cap at 300ms
    }

    // Debug: Send estimated minimum distance
    sprintf(debug_msg, "DEBUG:MIN_DISTANCE:%u\n", min_distance);
    HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);

    // Step 6: Post-process to filter peaks
    for (uint16_t i = 0; i < potential_count; i++) {
        uint16_t start_idx = potential_peaks[i];
        uint16_t end_idx = start_idx + min_distance;
        if (end_idx >= 2000) end_idx = 1999;

        int32_t max_value = potential_values[i];
        uint16_t max_idx = start_idx;

        // Find the peak with highest amplitude within the window
        for (uint16_t j = i + 1; j < potential_count; j++) {
            if (potential_peaks[j] > end_idx) break;

            if (potential_values[j] > max_value) {
                max_value = potential_values[j];
                max_idx = potential_peaks[j];
            }
            i = j; // Skip to the last peak in this window
        }

        // Refine the peak position using the original signal
        uint16_t refine_start = (max_idx < QRS_PEAK_REFINE_WINDOW) ? 0 : max_idx - QRS_PEAK_REFINE_WINDOW;
        uint16_t refine_end = (max_idx + QRS_PEAK_REFINE_WINDOW >= 2000) ? 1999 : max_idx + QRS_PEAK_REFINE_WINDOW;
        int32_t refined_max_value = signal[max_idx] - signal_mean;
        uint16_t refined_max_idx = max_idx;

        for (uint16_t j = refine_start; j <= refine_end; j++) {
            int32_t value = signal[j] - signal_mean;
            if (value > refined_max_value) {
                refined_max_value = value;
                refined_max_idx = j;
            }
        }

        // Mark the QRS peak at the refined position if it meets the amplitude criterion
        if (refined_max_value > QRS_MIN_AMPLITUDE && detector->peak_count < QRS_MAX_PEAKS) {
            qrs_flags[refined_max_idx] = 1;
            detector->peak_count++;

            // Debug: Send final peak
            sprintf(debug_msg, "DEBUG:PEAK:%u:%ld\n", refined_max_idx, refined_max_value);
            HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);
        }
    }

    // Debug: Send total number of detected peaks
    sprintf(debug_msg, "DEBUG:TOTAL:%u\n", detector->peak_count);
    HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);
}

/* End of file -------------------------------------------------------- */

/**
 * @file       qrs_detector.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.8
 * @date       2025-05-06
 * @author     Binh Nguyen
 * @brief      Implementation of QRS detection using Pan-Tompkins algorithm on STM32.
 * @note       Detects QRS peaks on a 10-second filtered ECG signal at 200 Hz.
 */

#include "qrs_detector.h"
#include "mylib.h"

/* Private defines ---------------------------------------------------- */
#define QRS_SIGNAL_FACTOR      0.4    /*!< Factor for signal level in threshold calculation (adjusted for better sensitivity) */
#define QRS_NOISE_FACTOR       0.6    /*!< Factor for noise level in threshold calculation (adjusted for better sensitivity) */
#define QRS_RR_LIMIT_LOW       0.92   /*!< Lower limit for RR interval (92% of average) */
#define QRS_RR_LIMIT_HIGH      1.16   /*!< Upper limit for RR interval (116% of average) */
#define QRS_SEARCHBACK_FACTOR  1.3    /*!< Factor for search-back window (130% of average RR, adjusted for better accuracy) */

/* Private function prototypes ---------------------------------------- */
static int32_t derivative(QRSDetector* detector, int32_t filtered);
static int32_t squaring(int32_t deriv);
static int32_t moving_window_integration(QRSDetector* detector, int32_t squared);
static void update_thresholds(QRSDetector* detector, int32_t peak, uint8_t is_qrs);
static void update_rr_intervals(QRSDetector* detector, uint32_t rr);
static int32_t calculate_slope(QRSDetector* detector);

/* Function definitions ----------------------------------------------- */
void QRSDetector_Init(QRSDetector* detector)
{
    for (uint8_t i = 0; i < 5; i++) {
        detector->deriv_buffer[i] = 0;
    }
    for (uint8_t i = 0; i < QRS_WINDOW_SIZE; i++) {
        detector->integ_buffer[i] = 0;
    }

    detector->integ_index = 0;
    detector->signal_level = 0;
    detector->noise_level = 0;
    detector->threshold_i1 = 0;
    detector->threshold_i2 = 0;
    detector->last_peak_time = 0;
    detector->sample_count = 0;
    detector->learning_phase = 1;

    for (uint8_t i = 0; i < 8; i++) {
        detector->rr_intervals[i] = 0;
    }
    detector->rr_index = 0;
    detector->rr_average1 = 0;
    detector->rr_average2 = 0;
    detector->rr_count = 0;

    detector->last_qrs_slope = 0;
}

void QRSDetector_Detect(QRSDetector* detector, const int32_t* filtered_data, uint8_t* qrs_flags)
{
    // Reset detector state
    QRSDetector_Init(detector);

    uint8_t learning_phase_2 = 0;  // Flag for second learning phase (RR interval initialization)
    uint8_t detected_peaks = 0;    // Counter for detected QRS peaks in learning phase 2

    // Process each sample in the 10-second filtered data
    for (uint32_t i = 0; i < QRS_10S_SAMPLES; i++) {
        int32_t filtered = filtered_data[i];

        // Step 1: Compute derivative
        int32_t deriv = derivative(detector, filtered);

        // Step 2: Square the signal
        int32_t squared = squaring(deriv);

        // Step 3: Apply moving window integration
        int32_t integrated = moving_window_integration(detector, squared);

        // Step 4: Learning phase (first 4 seconds)
        if (detector->learning_phase) {
            detector->sample_count++;
            if (detector->sample_count < QRS_LEARNING_SAMPLES) {
                if (integrated > detector->signal_level) detector->signal_level = integrated;
                detector->noise_level += integrated;
                qrs_flags[i] = 0;
                continue;
            } else {
                detector->noise_level /= QRS_LEARNING_SAMPLES;
                // Do not divide signal_level by 2 to avoid reducing threshold too much
                detector->threshold_i1 = detector->noise_level + QRS_SIGNAL_FACTOR * (detector->signal_level - detector->noise_level);
                detector->threshold_i2 = QRS_NOISE_FACTOR * detector->threshold_i1;
                detector->learning_phase = 0;
                detector->sample_count = 0;
            }
        }

        // Step 5: Peak detection
        uint8_t is_qrs = 0;
        if (integrated > detector->threshold_i1) {
            uint32_t time_since_last = detector->sample_count - detector->last_peak_time;

            // Check refractory period
            if (time_since_last < QRS_REFRACTORY_PERIOD) {
                update_thresholds(detector, integrated, 0);
                qrs_flags[i] = 0;
            } else {
                // T-wave discrimination
                if (time_since_last < QRS_TWAVE_PERIOD && detector->last_qrs_slope > 0) {
                    int32_t current_slope = calculate_slope(detector);
                    if (current_slope < detector->last_qrs_slope / 2) {
                        update_thresholds(detector, integrated, 0);
                        qrs_flags[i] = 0;
                    } else {
                        // Valid QRS peak
                        is_qrs = 1;
                        detector->last_qrs_slope = current_slope;
                        update_thresholds(detector, integrated, 1);
                        uint32_t rr = time_since_last;
                        update_rr_intervals(detector, rr);
                        detector->last_peak_time = detector->sample_count;
                        qrs_flags[i] = 1;

                        // Second learning phase: Initialize RR intervals with first 2 peaks
                        if (!learning_phase_2) {
                            detected_peaks++;
                            if (detected_peaks == 2) {
                                learning_phase_2 = 1;  // Second learning phase complete
                            }
                        }
                    }
                } else {
                    // Valid QRS peak
                    is_qrs = 1;
                    detector->last_qrs_slope = calculate_slope(detector);
                    update_thresholds(detector, integrated, 1);
                    uint32_t rr = time_since_last;
                    update_rr_intervals(detector, rr);
                    detector->last_peak_time = detector->sample_count;
                    qrs_flags[i] = 1;

                    // Second learning phase: Initialize RR intervals with first 2 peaks
                    if (!learning_phase_2) {
                        detected_peaks++;
                        if (detected_peaks == 2) {
                            learning_phase_2 = 1;  // Second learning phase complete
                        }
                    }
                }
            }
        } else if (detector->rr_average1 > 0 &&
                   (detector->sample_count - detector->last_peak_time) > (uint32_t)(QRS_SEARCHBACK_FACTOR * detector->rr_average1)) {
            if (integrated > detector->threshold_i2) {
                is_qrs = 1;
                detector->last_qrs_slope = calculate_slope(detector);
                update_thresholds(detector, integrated, 1);
                uint32_t rr = detector->sample_count - detector->last_peak_time;
                update_rr_intervals(detector, rr);
                detector->last_peak_time = detector->sample_count;
                qrs_flags[i] = 1;
            } else {
                qrs_flags[i] = 0;
            }
        } else {
            qrs_flags[i] = 0;
        }

        detector->sample_count++;
    }
}

/* Private definitions ----------------------------------------------- */
static int32_t derivative(QRSDetector* detector, int32_t filtered)
{
    for (uint8_t i = 4; i > 0; i--) {
        detector->deriv_buffer[i] = detector->deriv_buffer[i - 1];
    }
    detector->deriv_buffer[0] = filtered;

    // Five-point derivative (based on Pan-Tompkins)
    int32_t deriv = (1 / 8) * (-detector->deriv_buffer[4] - 2 * detector->deriv_buffer[3] + 2 * detector->deriv_buffer[1] + detector->deriv_buffer[0]);
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
    for (uint8_t i = 0; i < QRS_WINDOW_SIZE; i++) {
        sum += detector->integ_buffer[i];
    }
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
    if (detector->rr_count < 8) {
        detector->rr_count++;
    }

    uint32_t sum1 = 0;
    for (uint8_t i = 0; i < detector->rr_count; i++) {
        sum1 += detector->rr_intervals[i];
    }
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

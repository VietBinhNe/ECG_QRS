/**
 * @file       qrs_detector.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-10
 * @author     Binh Nguyen
 * @brief      Header file for QRS detection using Pan-Tompkins algorithm on STM32.
 * @note       Implements QRS detection for ECG signals at 64 Hz sampling rate.
 */

#ifndef INC_QRS_DETECTOR_H_
#define INC_QRS_DETECTOR_H_

/* Includes ----------------------------------------------------------- */
#include <stdint.h>

/* Public defines ----------------------------------------------------- */
#define QRS_SAMPLING_RATE      64    /*!< Sampling rate of ADC (64 Hz) */
#define QRS_WINDOW_SIZE        10    /*!< Window size for integration (156 ms at 64 Hz) */
#define QRS_REFRACTORY_PERIOD  12    /*!< Refractory period (187.5 ms at 64 Hz) */
#define QRS_TWAVE_PERIOD       23    /*!< T-wave discrimination period (360 ms at 64 Hz) */
#define QRS_LEARNING_SAMPLES   128   /*!< Samples for learning phase (2 seconds at 64 Hz) */

/* Public enumerate/structure ----------------------------------------- */
typedef struct {
    // Filter states
    int32_t baseline_buffer[64];  /**< Buffer for baseline removal (cutoff ~0.3 Hz) */
    int32_t lowpass_buffer[20];   /**< Buffer for low-pass filter (cutoff ~12 Hz) */
    int32_t highpass_buffer[64];  /**< Buffer for high-pass filter (cutoff ~0.5 Hz) */
    int32_t early_smooth_buffer[5]; /**< Buffer for early smoothing after bandpass */
    int32_t deriv_buffer[5];      /**< Buffer for derivative */
    int32_t smooth_buffer[4];     /**< Buffer for smoothing after squaring */
    int32_t integ_buffer[QRS_WINDOW_SIZE]; /**< Buffer for moving window integration */
    uint8_t integ_index;          /**< Index for integration buffer */

    // Threshold and detection states
    int32_t signal_level;         /**< Running estimate of signal level (SPKI) */
    int32_t noise_level;          /**< Running estimate of noise level (NPKI) */
    int32_t threshold_i1;         /**< Primary threshold for peak detection */
    int32_t threshold_i2;         /**< Secondary threshold for searchback */
    uint32_t last_peak_time;      /**< Time of last detected peak */
    uint32_t sample_count;        /**< Sample counter */
    uint8_t learning_phase;       /**< Flag for learning phase */

    // RR interval tracking
    uint32_t rr_intervals[8];     /**< Last 8 RR intervals */
    uint8_t rr_index;             /**< Index for RR intervals */
    uint32_t rr_average1;         /**< Average of last 8 RR intervals */
    uint32_t rr_average2;         /**< Average of last 8 RR intervals within limits */
    uint8_t rr_count;             /**< Number of RR intervals recorded */

    // Slope for T-wave discrimination
    int32_t last_qrs_slope;       /**< Slope of last QRS for T-wave discrimination */
} QRSDetector;

/* Public function prototypes ----------------------------------------- */
void QRSDetector_Init(QRSDetector* detector);
uint8_t QRSDetector_Process(QRSDetector* detector, uint16_t new_sample);

#endif /* INC_QRS_DETECTOR_H_ */

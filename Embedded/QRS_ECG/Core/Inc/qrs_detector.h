/**
 * @file       qrs_detector.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.4
 * @date       2025-05-06
 * @author     Binh Nguyen
 * @brief      Header file for QRS detection using Pan-Tompkins algorithm on STM32.
 * @note       Implements QRS detection for ECG signals at 200 Hz sampling rate.
 */

#ifndef INC_QRS_DETECTOR_H_
#define INC_QRS_DETECTOR_H_

/* Includes ----------------------------------------------------------- */
#include <stdint.h>

/* Public defines ----------------------------------------------------- */
#define QRS_SAMPLING_RATE      200   /*!< Sampling frequency of ADC (200 Hz) */
#define QRS_WINDOW_SIZE        40    /*!< Size of the integration window (200 ms at 200 Hz) */
#define QRS_REFRACTORY_PERIOD  40    /*!< Refractory period (200 ms at 200 Hz) */
#define QRS_TWAVE_PERIOD       72    /*!< T-wave discrimination period (360 ms at 200 Hz) */
#define QRS_LEARNING_SAMPLES   800   /*!< Number of samples for the learning phase (4 seconds at 200 Hz) */
#define QRS_10S_SAMPLES        2000  /*!< Number of samples for 10 seconds at 200 Hz */

/* Public enumerate/structure ----------------------------------------- */
typedef struct {
    // Filter states for QRS detection
    int32_t deriv_buffer[5];       /*!< Buffer for derivative */
    int32_t integ_buffer[QRS_WINDOW_SIZE]; /*!< Buffer for moving window integration */
    uint8_t integ_index;           /*!< Index for the integration buffer */

    // Threshold and detection states
    int32_t signal_level;         /*!< Signal level estimate (SPKI) */
    int32_t noise_level;          /*!< Noise level estimate (NPKI) */
    int32_t threshold_i1;         /*!< Primary threshold for peak detection */
    int32_t threshold_i2;         /*!< Secondary threshold for search-back */
    uint32_t last_peak_time;      /*!< Time of the last detected peak */
    uint32_t sample_count;        /*!< Sample counter */
    uint8_t learning_phase;       /*!< Flag for the learning phase */

    // RR interval tracking
    uint32_t rr_intervals[8];     /*!< Last 8 RR intervals */
    uint8_t rr_index;             /*!< Index for RR intervals */
    uint32_t rr_average1;         /*!< Average of the last 8 RR intervals */
    uint32_t rr_average2;         /*!< Average of the last 8 RR intervals within limits */
    uint8_t rr_count;             /*!< Number of recorded RR intervals */

    // Slope for T-wave discrimination
    int32_t last_qrs_slope;       /*!< Slope of the last QRS for T-wave discrimination */
} QRSDetector;

/* Public function prototypes ----------------------------------------- */
/**
 * @brief  Initialize the QRS Detector.
 *
 * @param[inout]  detector  Pointer to the QRSDetector structure.
 *
 * @attention  Must be called before using the detector.
 *
 * @return
 *  - None
 */
void QRSDetector_Init(QRSDetector* detector);

/**
 * @brief  Detect QRS peaks on a 10-second filtered signal.
 *
 * @param[inout]  detector      Pointer to the QRSDetector structure.
 * @param[in]     filtered_data Array of 10 seconds of filtered data (2000 samples at 200 Hz).
 * @param[out]    qrs_flags     Array to store QRS flags (0 or 1) for each sample.
 *
 * @attention  Processes the entire 10-second filtered signal at once to detect QRS peaks.
 *
 * @return
 *  - None
 */
void QRSDetector_Detect(QRSDetector* detector, const int32_t* filtered_data, uint8_t* qrs_flags);

#endif /* INC_QRS_DETECTOR_H_ */

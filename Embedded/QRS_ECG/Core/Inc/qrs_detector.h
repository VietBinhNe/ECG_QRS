/**
 * @file       qrs_detector.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.1.0
 * @date       2025-05-11
 * @author     Binh Nguyen
 *
 * @brief      Header file for QRS detection algorithm on STM32.
 *
 * @note       This file provides functions for detecting QRS complexes in ECG signals using low static threshold with smart post-processing.
 * @example    main.c
 *             Main application using the QRS detector to identify QRS complexes.
 */

/* Define to prevent recursive inclusion ------------------------------ */
#ifndef INC_QRS_DETECTOR_H_
#define INC_QRS_DETECTOR_H_

/* Includes ----------------------------------------------------------- */
#include <stdint.h>

/* Public defines ----------------------------------------------------- */
#define QRS_MIN_DISTANCE 80
#define QRS_MAX_PEAKS 50
#define QRS_STATIC_THRESHOLD 600
#define QRS_MIN_AMPLITUDE 1000
#define QRS_PEAK_WINDOW 2
#define QRS_PEAK_REFINE_WINDOW 10

/* Public enumerate/structure ----------------------------------------- */
/**
 * @brief Structure to store data for the QRS Detector.
 */
typedef struct {
    uint16_t peak_count;       /* Number of detected peaks */
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
 * @brief  Detect QRS complexes in the filtered ECG signal.
 *
 * @param[inout]  detector    Pointer to the QRSDetector structure.
 * @param[in]     signal      Array of filtered ECG samples (2000 samples for 10 seconds).
 * @param[out]    qrs_flags   Array to store QRS flags (1 for QRS peak, 0 otherwise).
 *
 * @attention  Processes 2000 samples (10 seconds at 200 Hz) and marks QRS peaks.
 *
 * @return
 *  - None
 */
void QRSDetector_Detect(QRSDetector* detector, int32_t* signal, uint8_t* qrs_flags);

#endif /* INC_QRS_DETECTOR_H_ */
/* End of file -------------------------------------------------------- */

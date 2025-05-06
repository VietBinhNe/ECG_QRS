/**
 * @file       filter.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-09
 * @author     Binh Nguyen
 *
 * @brief      Header file for signal filtering functions on STM32.
 *
 * @note       This file provides a Moving Average Filter and Bandpass Filter for smoothing and filtering ADC signals.
 * @example    main.c
 *             Main application using the filter to smooth ADC data.
 */

/* Define to prevent recursive inclusion ------------------------------ */
#ifndef INC_FILTER_H_
#define INC_FILTER_H_

/* Includes ----------------------------------------------------------- */
#include <stdint.h>

/* Public defines ----------------------------------------------------- */
#define MOVING_AVERAGE_WINDOW_SIZE 3	/*!< Size of the moving average filter window */
#define BANDPASS_LOWPASS_WINDOW_SIZE 5  /*!< Size of the low-pass filter window for bandpass filter (cutoff ~40 Hz) */
#define BANDPASS_HIGHPASS_WINDOW_SIZE 128 /*!< Size of the high-pass filter window for bandpass filter (cutoff ~0.5 Hz) */

/* Public enumerate/structure ----------------------------------------- */
/**
 * @brief Structure to store data for the Moving Average Filter.
 */
typedef struct {
    uint16_t buffer[MOVING_AVERAGE_WINDOW_SIZE]; /**< Buffer to store recent samples */
    uint8_t index;                               /**< Current index in the buffer */
    uint8_t is_full;                             /**< Flag to indicate if the buffer is full */
} MovingAverageFilter;

/**
 * @brief Structure to store data for the Bandpass Filter.
 */
typedef struct {
    int32_t lowpass_buffer[BANDPASS_LOWPASS_WINDOW_SIZE];    /*!< Buffer for low-pass filter (cutoff ~40 Hz) */
    int32_t highpass_buffer[BANDPASS_HIGHPASS_WINDOW_SIZE];   /*!< Buffer for high-pass filter (cutoff ~0.5 Hz) */
    uint8_t lowpass_index;                                    /*!< Current index for low-pass buffer */
    uint16_t highpass_index;                                  /*!< Current index for high-pass buffer */
} BandpassFilter;

/* Public function prototypes ----------------------------------------- */
/**
 * @brief  Initialize the Moving Average Filter.
 *
 * @param[inout]  filter  Pointer to the MovingAverageFilter structure.
 *
 * @attention  Must be called before using the filter.
 *
 * @return
 *  - None
 */
void MovingAverageFilter_Init(MovingAverageFilter* filter);

/**
 * @brief  Apply the Moving Average Filter to a new sample.
 *
 * @param[inout]  filter      Pointer to the MovingAverageFilter structure.
 * @param[in]     new_sample  New ADC sample to be filtered.
 *
 * @attention  The filter smooths the signal by averaging over a window of samples.
 *
 * @return
 *  - Filtered value (uint16_t)
 */
uint16_t MovingAverageFilter_Apply(MovingAverageFilter* filter, uint16_t new_sample);

/**
 * @brief  Initialize the Bandpass Filter.
 *
 * @param[inout]  filter  Pointer to the BandpassFilter structure.
 *
 * @attention  Must be called before using the filter.
 *
 * @return
 *  - None
 */
void BandpassFilter_Init(BandpassFilter* filter);

/**
 * @brief  Apply the Bandpass Filter to a new sample.
 *
 * @param[inout]  filter      Pointer to the BandpassFilter structure.
 * @param[in]     new_sample  New ADC sample to be filtered.
 *
 * @attention  The filter applies a bandpass filter (~0.5-40 Hz) to remove noise while preserving ECG features.
 *
 * @return
 *  - Filtered value (int32_t)
 */
int32_t BandpassFilter_Apply(BandpassFilter* filter, int32_t new_sample);

#endif /* INC_FILTER_H_ */
/* End of file -------------------------------------------------------- */

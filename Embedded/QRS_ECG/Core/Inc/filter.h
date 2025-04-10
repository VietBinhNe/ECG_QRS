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
 * @note       This file provides a Moving Average Filter for smoothing ADC signals.
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

/* Public enumerate/structure ----------------------------------------- */
/**
 * @brief Structure to store data for the Moving Average Filter.
 */
typedef struct {
    uint16_t buffer[MOVING_AVERAGE_WINDOW_SIZE]; /**< Buffer to store recent samples */
    uint8_t index;                               /**< Current index in the buffer */
    uint8_t is_full;                             /**< Flag to indicate if the buffer is full */
} MovingAverageFilter;

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

#endif /* INC_FILTER_H_ */
/* End of file -------------------------------------------------------- */

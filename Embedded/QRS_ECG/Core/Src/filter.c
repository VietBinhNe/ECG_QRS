/**
 * @file       filter.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-10
 * @author     Binh Nguyen
 *
 * @brief      Implementation of signal filtering functions for STM32.
 *
 * @note       This file implements a Moving Average Filter for smoothing ADC signals.
 * @example    main.c
 *             Main application using the filter to smooth ADC data.
 */

/* Includes ----------------------------------------------------------- */
#include "filter.h"

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
void MovingAverageFilter_Init(MovingAverageFilter* filter)
{
    for (uint8_t i = 0; i < MOVING_AVERAGE_WINDOW_SIZE; i++) {
        filter->buffer[i] = 0;
    }
    filter->index = 0;
    filter->is_full = 0;
}

uint16_t MovingAverageFilter_Apply(MovingAverageFilter* filter, uint16_t new_sample)
{
    filter->buffer[filter->index] = new_sample;
    filter->index++;

    if (filter->index >= MOVING_AVERAGE_WINDOW_SIZE) {
        filter->index = 0;
        filter->is_full = 1;
    }

    if (!filter->is_full) {
        return new_sample;
    }

    uint32_t sum = 0;
    for (uint8_t i = 0; i < MOVING_AVERAGE_WINDOW_SIZE; i++) {
        sum += filter->buffer[i];
    }
    return (uint16_t)(sum / MOVING_AVERAGE_WINDOW_SIZE);
}

/* Private definitions ----------------------------------------------- */
/* None */

/* End of file -------------------------------------------------------- */

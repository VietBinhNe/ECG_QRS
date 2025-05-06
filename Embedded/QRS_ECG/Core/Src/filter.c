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
 * @note       This file implements a Moving Average Filter and Bandpass Filter for smoothing and filtering ADC signals.
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

void BandpassFilter_Init(BandpassFilter* filter)
{
    for (uint8_t i = 0; i < BANDPASS_LOWPASS_WINDOW_SIZE; i++) {
        filter->lowpass_buffer[i] = 0;
    }
    for (uint16_t i = 0; i < BANDPASS_HIGHPASS_WINDOW_SIZE; i++) {
        filter->highpass_buffer[i] = 0;
    }
    filter->lowpass_index = 0;
    filter->highpass_index = 0;
}

int32_t BandpassFilter_Apply(BandpassFilter* filter, int32_t new_sample)
{
    // Low-pass filter (cutoff ~40 Hz at 200 Hz)
    for (uint8_t i = BANDPASS_LOWPASS_WINDOW_SIZE - 1; i > 0; i--) {
        filter->lowpass_buffer[i] = filter->lowpass_buffer[i - 1];
    }
    filter->lowpass_buffer[0] = new_sample;

    int32_t lowpass = 0;
    for (uint8_t i = 0; i < BANDPASS_LOWPASS_WINDOW_SIZE; i++) {
        lowpass += filter->lowpass_buffer[i];
    }
    lowpass /= BANDPASS_LOWPASS_WINDOW_SIZE;

    // High-pass filter (cutoff ~0.5 Hz at 200 Hz)
    for (uint16_t i = BANDPASS_HIGHPASS_WINDOW_SIZE - 1; i > 0; i--) {
        filter->highpass_buffer[i] = filter->highpass_buffer[i - 1];
    }
    filter->highpass_buffer[0] = lowpass;

    // Calculate the average of the previous 128 samples
    int32_t lowpass_average = 0;
    for (uint16_t i = 0; i < BANDPASS_HIGHPASS_WINDOW_SIZE; i++) {
        lowpass_average += filter->highpass_buffer[i];
    }
    lowpass_average /= BANDPASS_HIGHPASS_WINDOW_SIZE;

    // High-pass filter: y[n] = x[n] - (1/128) * sum(x[n-k])
    int32_t highpass = lowpass - lowpass_average;

    return highpass;
}

/* Private definitions ----------------------------------------------- */
/* None */

/* End of file -------------------------------------------------------- */

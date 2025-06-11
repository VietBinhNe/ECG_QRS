/**
 * @file       filter.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.2
 * @date       2025-04-10
 * @author     Binh Nguyen
 *
 * @brief      Implementation of signal filtering functions for STM32.
 *
 * @note       This file implements a Bandpass Filter for filtering ADC signals.
 * @example    main.c
 *             Main application using the filter to filter ADC data.
 */

/* Includes ----------------------------------------------------------- */
#include "filter.h"
#include "mylib.h"

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
    lowpass = (lowpass * 384) >> 10;

    // High-pass filter (cutoff ~0.5 Hz at 200 Hz)
    for (uint16_t i = BANDPASS_HIGHPASS_WINDOW_SIZE - 1; i > 0; i--) {
        filter->highpass_buffer[i] = filter->highpass_buffer[i - 1];
    }
    filter->highpass_buffer[0] = lowpass;

    int32_t lowpass_average = 0;
    for (uint16_t i = 0; i < BANDPASS_HIGHPASS_WINDOW_SIZE; i++) {
        lowpass_average += filter->highpass_buffer[i];
    }

    lowpass_average >>= 7;

    // High-pass filter: y[n] = x[n] - (1/128) * sum(x[n-k])
    int32_t highpass = lowpass - lowpass_average;

    // Overflow control
    if (highpass > 32767) highpass = 32767;
    if (highpass < -32768) highpass = -32768;

    // Debug: Print filtered value every 100 samples
    if (filter->highpass_index % 100 == 0) {
        char debug_msg[50];
        sprintf(debug_msg, "DEBUG:FILTER:%ld\n", highpass);
        HAL_UART_Transmit(&huart2, (uint8_t*)debug_msg, strlen(debug_msg), 200);
    }

    return highpass;
}

/* Private definitions ----------------------------------------------- */
/* None */

/* End of file -------------------------------------------------------- */

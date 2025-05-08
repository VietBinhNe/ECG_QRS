/**
  ******************************************************************************
  * @file    stm32f4xx_it.c
  * @brief   Interrupt Service Routines.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32f4xx_it.h"
#include "mylib.h"
#include "filter.h"
#include "cbuffer.h"
#include "qrs_detector.h"

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */

// Declare global variables defined in main.c
extern BandpassFilter bandpass_filter;
extern cbuffer_t adc_buffer;
extern uint8_t adc_buffer_data[512];
extern QRSDetector qrs_detector;
extern int32_t first_10s_filtered[2000];
extern uint8_t first_10s_qrs_flags[2000];
extern uint32_t first_10s_count;
extern uint8_t first_10s_ready;

/* USER CODE END PV */

/* External variables --------------------------------------------------------*/
extern DMA_HandleTypeDef hdma_adc1;
extern TIM_HandleTypeDef htim2;
extern uint8_t qrs_flags[64];
extern uint8_t qrs_flag_index;

/* USER CODE BEGIN EV */

/* USER CODE END EV */

/******************************************************************************/
/*           Cortex-M4 Processor Interruption and Exception Handlers          */
/******************************************************************************/
/**
  * @brief This function handles Non maskable interrupt.
  */
void NMI_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Hard fault interrupt.
  */
void HardFault_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Memory management fault.
  */
void MemManage_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Pre-fetch fault, memory access fault.
  */
void BusFault_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles Undefined instruction or illegal state.
  */
void UsageFault_Handler(void)
{
  while (1)
  {
  }
}

/**
  * @brief This function handles System service call via SWI instruction.
  */
void SVC_Handler(void)
{
}

/**
  * @brief This function handles Debug monitor.
  */
void DebugMon_Handler(void)
{
}

/**
  * @brief This function handles Pendable request for system service.
  */
void PendSV_Handler(void)
{
}

/**
  * @brief This function handles System tick timer.
  */
void SysTick_Handler(void)
{
  HAL_IncTick();
}

/******************************************************************************/
/* STM32F4xx Peripheral Interrupt Handlers                                    */
/* Add here the Interrupt Handlers for the used peripherals.                  */
/* For the available peripheral interrupt handler names,                      */
/* please refer to the startup file (startup_stm32f4xx.s).                    */
/******************************************************************************/

/**
  * @brief This function handles TIM2 global interrupt.
  */
void TIM2_IRQHandler(void)
{
  // Use raw ADC value directly
  uint16_t raw_value = (uint16_t)ADC_value;

  // Apply bandpass filter to get filtered signal
  int32_t bandpass = BandpassFilter_Apply(&bandpass_filter, raw_value);

  // Store filtered value for the first 10 seconds
  if (first_10s_count < 2000) {
    first_10s_filtered[first_10s_count] = bandpass;
    first_10s_count++;
    if (first_10s_count == 2000) {
      // Detect QRS on the first 10 seconds of filtered data
      QRSDetector_Detect(&qrs_detector, first_10s_filtered, first_10s_qrs_flags);
      first_10s_ready = 1;
    }
  }

  // Store raw and filtered values into Circular Buffer
  // Each sample: 2 bytes for raw_value, 2 bytes for bandpass
  uint8_t raw_high_byte = (raw_value >> 8) & 0xFF;
  uint8_t raw_low_byte = raw_value & 0xFF;
  uint8_t bp_high_byte = (bandpass >> 8) & 0xFF;
  uint8_t bp_low_byte = bandpass & 0xFF;

  cb_write(&adc_buffer, &raw_high_byte, 1);
  cb_write(&adc_buffer, &raw_low_byte, 1);
  cb_write(&adc_buffer, &bp_high_byte, 1);
  cb_write(&adc_buffer, &bp_low_byte, 1);

  // Check the amount of data in the buffer
  if (cb_data_count(&adc_buffer) >= 256) // 256 bytes = 64 samples (each sample 4 bytes: 2 bytes raw + 2 bytes bandpass)
  {
    send_flag = 1; // Set flag to send data in main
  }

  HAL_TIM_IRQHandler(&htim2);
}

/**
  * @brief This function handles DMA2 stream0 global interrupt.
  */
void DMA2_Stream0_IRQHandler(void)
{
  HAL_DMA_IRQHandler(&hdma_adc1);
}

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */

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

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */
extern BandpassFilter bandpass_filter;
extern cbuffer_t adc_buffer;
extern uint8_t adc_buffer_data[512];
/* USER CODE END PV */

/* External variables --------------------------------------------------------*/
extern DMA_HandleTypeDef hdma_adc1;
extern TIM_HandleTypeDef htim2;

/* USER CODE BEGIN EV */

/* USER CODE END EV */

/******************************************************************************/
/*           Cortex-M4 Processor Interruption and Exception Handlers          */
/******************************************************************************/
void NMI_Handler(void)
{
  while (1)
  {
  }
}

void HardFault_Handler(void)
{
  while (1)
  {
  }
}

void MemManage_Handler(void)
{
  while (1)
  {
  }
}

void BusFault_Handler(void)
{
  while (1)
  {
  }
}

void UsageFault_Handler(void)
{
  while (1)
  {
  }
}

void SVC_Handler(void)
{
}

void DebugMon_Handler(void)
{
}

void PendSV_Handler(void)
{
}

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

void TIM2_IRQHandler(void)
{
  uint16_t raw_value = (uint16_t)ADC_value;
  int32_t bandpass = BandpassFilter_Apply(&bandpass_filter, raw_value);

  uint8_t raw_high_byte = (raw_value >> 8) & 0xFF;
  uint8_t raw_low_byte = raw_value & 0xFF;
  uint8_t bp_high_byte = (bandpass >> 8) & 0xFF;
  uint8_t bp_low_byte = bandpass & 0xFF;

  cb_write(&adc_buffer, &raw_high_byte, 1);
  cb_write(&adc_buffer, &raw_low_byte, 1);
  cb_write(&adc_buffer, &bp_high_byte, 1);
  cb_write(&adc_buffer, &bp_low_byte, 1);

  if (cb_data_count(&adc_buffer) >= 256)
  {
    send_flag = 1;
  }

  HAL_TIM_IRQHandler(&htim2);
}

void DMA2_Stream0_IRQHandler(void)
{
  HAL_DMA_IRQHandler(&hdma_adc1);
}

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */

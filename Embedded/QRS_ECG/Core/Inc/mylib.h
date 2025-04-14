/**
 * @file       mylib.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-03-23
 * @author     Binh Nguyen
 *             
 * @brief      Library for managing global variables and handles for STM32 ADC and UART operations.
 *             
 * @note       This file contains declarations of global variables used across the project.
 * @example    main.c
 *             Main application using ADC and UART variables.
 */

/* Define to prevent recursive inclusion ------------------------------ */
#ifndef INC_MYLIB_H_
#define INC_MYLIB_H_

/* Includes ----------------------------------------------------------- */
#include "main.h"
#include <string.h>
#include <stdlib.h>

/* Public defines ----------------------------------------------------- */
/* None */

/* Public enumerate/structure ----------------------------------------- */
/* None */

/* Public macros ------------------------------------------------------ */
/* None */

/* Public variables --------------------------------------------------- */
extern uint8_t send_flag;     /**< Flag to indicate when to send data over UART */
extern uint32_t ADC_value;    /**< Raw ADC value read from the sensor */
extern UART_HandleTypeDef huart2; /**< UART handle for communication */
extern ADC_HandleTypeDef hadc1;   /**< ADC handle for reading sensor data */

/* Public function prototypes ----------------------------------------- */
/* None */

#endif /* INC_MYLIB_H_ */

/* End of file -------------------------------------------------------- */

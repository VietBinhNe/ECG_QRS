/**
 * @file       mylib.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-03-23
 * @author     Binh Nguyen
 *             
 * @brief      Implementation of global variables for STM32 ADC and UART operations.
 *             
 * @note       This file defines global variables declared in mylib.h.
 * @example    main.c
 *             Main application using ADC and UART variables.
 */

/* Includes ----------------------------------------------------------- */
#include "mylib.h"

/* Private defines ---------------------------------------------------- */
/* None */

/* Private enumerate/structure ---------------------------------------- */
/* None */

/* Private macros ----------------------------------------------------- */
/* None */

/* Public variables --------------------------------------------------- */
uint8_t send_flag = 0;     /**< Flag to indicate when to send data over UART */
uint32_t ADC_value;        /**< Raw ADC value read from the sensor */

/* Private variables -------------------------------------------------- */
/* None */

/* Private function prototypes ---------------------------------------- */
/* None */

/* Function definitions ----------------------------------------------- */
/* None */

/* Private definitions ----------------------------------------------- */
/* None */

/* End of file -------------------------------------------------------- */

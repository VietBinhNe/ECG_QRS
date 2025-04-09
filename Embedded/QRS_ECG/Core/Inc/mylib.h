/*
 * mylib.h
 *
 *  Created on: Mar 23, 2025
 *      Author: nguye
 */

#ifndef INC_MYLIB_H_
#define INC_MYLIB_H_

#include "main.h"
#include <string.h>
#include <stdlib.h>

extern uint8_t stream_index, array_index, send_flag;
extern uint32_t ADC_value;
extern UART_HandleTypeDef huart2;
extern uint16_t ADC_Values[4][64]; // 64 sample and 4 line ?
extern ADC_HandleTypeDef hadc1;

#endif /* INC_MYLIB_H_ */

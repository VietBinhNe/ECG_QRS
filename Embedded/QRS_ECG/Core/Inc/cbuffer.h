/**
 * @file       cbuffer.h
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-10
 * @author     Binh Nguyen
 *
 * @brief      Circular Buffer implementation for STM32.
 *             This Circular Buffer is safe to use in IRQ with single reader,
 *             single writer. No need to disable any IRQ.
 *
 * @note       Capacity = size - 1. Should use correct size of buffer when init.
 * @example    main.c
 *             Main application using Circular Buffer to store ADC data.
 */

/* Define to prevent recursive inclusion ------------------------------ */
#ifndef INC_CBUFFER_H_
#define INC_CBUFFER_H_

/* Includes ----------------------------------------------------------- */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Public defines ----------------------------------------------------- */
#define CB_MAX_SIZE (0x00800000) /*!< Max size of circular buffer */
#define CB_ERROR    (0xFFFFFFFF) /*!< Error return value */
#define CB_SUCCESS  (0x00000000) /*!< Success return value */

/* Public enumerate/structure ----------------------------------------- */
/**
 * @brief Circular buffer structure definition.
 */
typedef struct
{
    uint8_t *data;              /**< Pointer to buffer */
    uint32_t size;              /**< Size of buffer */
    volatile uint32_t writer;   /**< Position to write */
    volatile uint32_t reader;   /**< Position to read */
    volatile uint32_t overflow; /**< How many bytes are overflow */
    volatile bool active;       /**< Initialized or not */
} cbuffer_t;

/* Public function prototypes ----------------------------------------- */
/**
 * @brief  Initialize circular buffer.
 *
 * @param[inout]  cb    Pointer to a cbuffer_t structure.
 * @param[in]     buf   Pointer to array.
 * @param[in]     size  Size of buffer.
 *
 * @attention  Must be called before using the buffer.
 *
 * @return
 *  - (0) : Success
 *  - (-1): Error
 */
uint32_t cb_init(cbuffer_t *cb, void *buf, uint32_t size);

/**
 * @brief  Clear circular buffer.
 *
 * @param[inout]  cb  Pointer to a cbuffer_t structure.
 *
 * @attention  Resets the buffer to initial state.
 *
 * @return
 *  - (0) : Success
 *  - (-1): Error
 */
uint32_t cb_clear(cbuffer_t *cb);

/**
 * @brief  Read data from circular buffer.
 *
 * @param[in]   cb      Pointer to a cbuffer_t structure.
 * @param[out]  buf     Pointer to data buffer.
 * @param[in]   nbytes  Size of data to read.
 *
 * @attention  Reads up to nbytes from the buffer.
 *
 * @return
 *  - Number of successfully read bytes: Success
 *  - (-1): Error
 */
uint32_t cb_read(cbuffer_t *cb, void *buf, uint32_t nbytes);

/**
 * @brief  Write data to circular buffer.
 *
 * @param[inout]  cb      Pointer to a cbuffer_t structure.
 * @param[in]     buf     Pointer to data buffer.
 * @param[in]     nbytes  Size of data to write.
 *
 * @attention  Writes up to nbytes to the buffer.
 *
 * @return
 *  - Number of successfully written bytes: Success
 *  - (-1): Error
 */
uint32_t cb_write(cbuffer_t *cb, void *buf, uint32_t nbytes);

/**
 * @brief  Return the number of bytes in circular buffer.
 *
 * @param[in]  cb  Pointer to a cbuffer_t structure.
 *
 * @attention  None
 *
 * @return
 *  - Number of bytes in circular buffer: Success
 *  - (-1): Error
 */
uint32_t cb_data_count(cbuffer_t *cb);

/**
 * @brief  Return the number of free space (in bytes) in circular buffer.
 *
 * @param[in]  cb  Pointer to a cbuffer_t structure.
 *
 * @attention  None
 *
 * @return
 *  - Number of free space (in bytes) in circular buffer: Success
 *  - (-1): Error
 */
uint32_t cb_space_count(cbuffer_t *cb);

#endif /* INC_CBUFFER_H_ */
/* End of file -------------------------------------------------------- */

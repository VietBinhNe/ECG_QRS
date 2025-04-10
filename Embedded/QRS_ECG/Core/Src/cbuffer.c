/**
 * @file       cbuffer.c
 * @copyright  Copyright (C) 2025 HCMUS. All rights reserved.
 * @license    This project is released under the VB's License.
 * @version    1.0.0
 * @date       2025-04-10
 * @author     Binh Nguyen
 *
 * @brief      Implementation of Circular Buffer for STM32.
 *             This Circular Buffer is safe to use in IRQ with single reader,
 *             single writer. No need to disable any IRQ.
 *
 * @note       Capacity = size - 1. Should use correct size of buffer when init.
 * @example    main.c
 *             Main application using Circular Buffer to store ADC data.
 */

/* Includes ----------------------------------------------------------- */
#include "cbuffer.h"

/* Private function prototypes ---------------------------------------- */
/**
 * @brief  Write 1 byte to circular buffer.
 *
 * @param[inout]  cb    Pointer to a cbuffer_t structure.
 * @param[in]     byte  Data to write.
 *
 * @attention  Internal function, not for direct use.
 *
 * @return
 *  - (0) : Success
 *  - (-1): Error
 */
static uint32_t cb_write_byte(cbuffer_t *cb, uint8_t byte);

/**
 * @brief  Read 1 byte from circular buffer.
 *
 * @param[in]   cb    Pointer to a cbuffer_t structure.
 * @param[out]  byte  Pointer to data buffer.
 *
 * @attention  Internal function, not for direct use.
 *
 * @return
 *  - (0) : Success
 *  - (-1): Error
 */
static uint32_t cb_read_byte(cbuffer_t *cb, uint8_t *byte);

/* Function definitions ----------------------------------------------- */
uint32_t cb_init(cbuffer_t *cb, void *buf, uint32_t size)
{
    if (cb == NULL || buf == NULL || size >= CB_MAX_SIZE)
        return CB_ERROR;

    cb->data = buf;
    cb->size = size;
    cb->writer = 0;
    cb->reader = 0;
    cb->overflow = 0;
    cb->active = 1;

    return CB_SUCCESS;
}

uint32_t cb_clear(cbuffer_t *cb)
{
    if (cb == NULL)
        return CB_ERROR;

    cb->writer = 0;
    cb->reader = 0;
    cb->overflow = 0;

    return CB_SUCCESS;
}

uint32_t cb_read(cbuffer_t *cb, void *buf, uint32_t nbytes)
{
    int data_count = 0;
    int num_avail_bytes = 0;
    if (cb == NULL || buf == NULL || !cb->active)
        return CB_ERROR;

    cb->active = 0;
    data_count = cb_data_count(cb);
    if (data_count >= nbytes)
        num_avail_bytes = nbytes;
    else
        num_avail_bytes = data_count;

    for (int i = 0; i < num_avail_bytes; i++)
        cb_read_byte(cb, (uint8_t *)buf + i);

    cb->active = 1;
    return num_avail_bytes;
}

uint32_t cb_write(cbuffer_t *cb, void *buf, uint32_t nbytes)
{
    int space_count = 0;
    int num_avail_bytes = 0;
    if (cb == NULL || buf == NULL || !cb->active)
        return CB_ERROR;

    cb->active = 0;
    space_count = cb_space_count(cb);
    if (space_count >= nbytes)
    {
        num_avail_bytes = nbytes;
        cb->overflow = 0;
    }
    else
    {
        num_avail_bytes = space_count;
        cb->overflow = nbytes - space_count;
    }

    for (int i = 0; i < num_avail_bytes; i++)
        cb_write_byte(cb, *((uint8_t *)buf + i));

    cb->active = 1;
    return num_avail_bytes;
}

uint32_t cb_data_count(cbuffer_t *cb)
{
    int res = 0;
    if (cb == NULL)
        return CB_ERROR;

    if (cb->writer >= cb->reader)
        res = cb->writer - cb->reader;
    else
        res = cb->size - cb->reader + cb->writer;

    return res;
}

uint32_t cb_space_count(cbuffer_t *cb)
{
    int res = 0;
    if (cb == NULL)
        return CB_ERROR;

    if (cb->reader > cb->writer)
        res = cb->reader - cb->writer - 1;
    else if (cb->reader < cb->writer)
        res = cb->size - cb->writer + cb->reader - 1;
    else
        res = cb->size - 1;

    return res;
}

/* Private definitions ----------------------------------------------- */
static uint32_t cb_write_byte(cbuffer_t *cb, uint8_t byte)
{
    uint32_t next = cb->writer + 1;
    if (next == cb->size)
        next = 0;

    if (next == cb->reader)
        return CB_ERROR;

    *(cb->data + cb->writer) = byte;
    cb->writer = next;
    return CB_SUCCESS;
}

static uint32_t cb_read_byte(cbuffer_t *cb, uint8_t *byte)
{
    uint32_t next = cb->reader + 1;
    if (cb->reader == cb->writer)
        return CB_ERROR;

    if (next == cb->size)
        next = 0;

    *byte = *(cb->data + cb->reader);
    cb->reader = next;
    return CB_SUCCESS;
}

/* End of file -------------------------------------------------------- */

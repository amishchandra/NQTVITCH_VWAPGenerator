import argparse
import sys

from itch_config import *
import gzip
import struct


STOCK_DIR = dict()
ORDERS_DIR = dict()
FILLED_ORDERS = dict()


def populate_orderbook(itch_flag, order_info, is_mkt_open):
    # Processing Stock Directory Messages
    if itch_flag == STOCK_DIR_FLAG:
        STOCK_DIR[order_info[0]] = order_info[3].decode('latin1').encode('utf-8').strip()

    # Processing Orders Addition Messages
    elif itch_flag in [ADD_ORDER_NO_MPID_FLAG, ADD_ORDER_FLAG]:
        ORDERS_DIR[order_info[3]] = order_info[7] / (10 ** 4)
    elif itch_flag == ORDER_REPLACE_FLAG:
        del ORDERS_DIR[order_info[3]]
        ORDERS_DIR[order_info[4]] = order_info[6] / (10 ** 4)
    elif itch_flag == ORDER_DELETE_FLAG:
        del ORDERS_DIR[order_info[3]]

    # Processing Order Fill Messages
    elif is_mkt_open and itch_flag == ORDER_EXECUTED_FLAG:
        if STOCK_DIR[order_info[0]] not in FILLED_ORDERS:
            FILLED_ORDERS[STOCK_DIR[order_info[0]]] = {'cum_vol': 0, 'cum_price': 0}
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_vol'] += order_info[4]
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_price'] += (order_info[4]*ORDERS_DIR[order_info[3]])
    elif is_mkt_open and itch_flag == ORDER_EXECUTED_DIFF_PRICE_FLAG and order_info[6].decode('latin1') == PRINTABLE:
        if STOCK_DIR[order_info[0]] not in FILLED_ORDERS:
            FILLED_ORDERS[STOCK_DIR[order_info[0]]] = {'cum_vol': 0, 'cum_price': 0}
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_vol'] += order_info[4]
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_price'] += (order_info[4] * order_info[7] / (10 ** 4))
    elif is_mkt_open and itch_flag == TRADE_MSG_FLAG:
        if STOCK_DIR[order_info[0]] not in FILLED_ORDERS:
            FILLED_ORDERS[STOCK_DIR[order_info[0]]] = {'cum_vol': 0, 'cum_price': 0}
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_vol'] += order_info[5]
        FILLED_ORDERS[STOCK_DIR[order_info[0]]]['cum_price'] += (order_info[5] * order_info[7] / (10 ** 4))


def report_vwap_value(tsp_ns):
    with open(f"vwap_{tsp_ns}.csv", "a") as vwap_file:
        vwap_file.write("symbol,vwap\n")
        for symbol, vol_price_info in FILLED_ORDERS.items():
            vwap = vol_price_info['cum_price']/vol_price_info['cum_vol']
            vwap_file.write(f"{symbol.decode()},{round(vwap,3)}\n")
    print(f"Written Hourly VWAP at {round(tsp_ns / REPORTING_INTERVAL, 2)} hours")


def refresh_byte_array(byte_array, end_limit, bytes_parsed, total_bytes_parsed, file_obj, chunk_size):
    byte_array_len = len(byte_array)
    byte_array = file_obj.read(chunk_size) if bytes_parsed+1 == byte_array_len else \
        byte_array[bytes_parsed+1:]+file_obj.read(chunk_size) if end_limit >= byte_array_len else byte_array
    total_bytes_parsed = total_bytes_parsed + bytes_parsed if end_limit >= byte_array_len else total_bytes_parsed
    bytes_parsed = -1 if end_limit >= byte_array_len else bytes_parsed
    return byte_array, bytes_parsed, total_bytes_parsed


def parse_and_compute_vwap(source_file, chunk_size):
    time_elapsed, total_bytes_parsed, log_after_mb = 0, 0, 100
    is_mkt_open = False
    with gzip.open(source_file, 'rb') as itch_file:
        print("Reading File...")
        byte_array = itch_file.read(chunk_size)
        print(f"Byte Array Size: {round(sys.getsizeof(byte_array)/(1024**2), 2)} MBs")
        bytes_parsed = 0
        itch_byte = byte_array[bytes_parsed]

        while True:
            itch_flag = chr(itch_byte)
            if itch_flag in ITCH_NON_VWAP_MSG_INFO:
                msg_size = ITCH_NON_VWAP_MSG_INFO[itch_flag]['size']
                byte_array, bytes_parsed, total_bytes_parsed = refresh_byte_array(byte_array, bytes_parsed+msg_size,
                                                                                  bytes_parsed, total_bytes_parsed,
                                                                                  itch_file, chunk_size)
                bytes_parsed += msg_size
            elif itch_flag in ITCH_VWAP_MSG_INFO:
                msg_size = ITCH_VWAP_MSG_INFO[itch_flag]['size']
                msg_format = ITCH_VWAP_MSG_INFO[itch_flag]['format']
                byte_array, bytes_parsed, total_bytes_parsed = refresh_byte_array(byte_array, bytes_parsed+msg_size,
                                                                                  bytes_parsed, total_bytes_parsed,
                                                                                  itch_file, chunk_size)
                itch_msg = byte_array[bytes_parsed+1:bytes_parsed+msg_size+1]
                bytes_parsed += msg_size
                data = list(struct.unpack(msg_format, itch_msg))
                tsp_field_idx = msg_format.index(TIMESTAMP_FORMAT)-1 if TIMESTAMP_FORMAT in msg_format else -1
                # Format the Timestamp Field
                if tsp_field_idx >= 0:
                    padded_byte = struct.pack('>2s6s', b'\x00\x00', data[tsp_field_idx])
                    data[tsp_field_idx] = struct.unpack('>Q', padded_byte)[0]
                    if is_mkt_open and data[tsp_field_idx]-time_elapsed >= REPORTING_INTERVAL:
                        report_vwap_value(data[tsp_field_idx])
                        time_elapsed += REPORTING_INTERVAL
                # Get the market start and market end from system message
                if itch_flag == SYSTEM_EVENT_FLAG:
                    print(f"SYSTEM_EVENT_FLAG: {data[3].decode('latin1')}")
                    if data[3].decode('latin1') == MKT_OPEN_FLAG:
                        is_mkt_open = True
                        print(f"Market Open Time: {data[tsp_field_idx]}")
                        time_elapsed = data[tsp_field_idx]
                    elif data[3].decode('latin1') == MKT_CLOSE_FLAG:
                        print(f"Market Close Time: {data[tsp_field_idx]}")
                        break
                else:
                    populate_orderbook(itch_flag, data, is_mkt_open)

            byte_array, bytes_parsed, total_bytes_parsed = refresh_byte_array(byte_array, bytes_parsed+1, bytes_parsed,
                                                                              total_bytes_parsed, itch_file, chunk_size)
            itch_byte = byte_array[bytes_parsed+1]
            bytes_parsed += 1
            if total_bytes_parsed / (log_after_mb*1024*1024) >= 1:
                print(f"{log_after_mb} MB done...")
                log_after_mb += 100
    report_vwap_value(data[tsp_field_idx])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script to parse NASDAQ TV ITCH data and calculate VWAP')
    parser.add_argument('--source_file', required=True, type=str)
    parser.add_argument('--chunk_size', default=100000000, type=int)
    args = parser.parse_args()
    parse_and_compute_vwap(args.source_file, args.chunk_size)

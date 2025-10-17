# RAR5 CRC:
#   1. Main Header CRC
#   2. End Block CRC
#   3. For each file:
#       File Header CRC and File Data CRC

import rarfile
import zlib


def read_file(filename):
    with open(filename, 'rb') as file:
        return file.read()


def block_crc_read(start, rar_bytes):
    crc_bytes = rar_bytes[start:start + 4]
    return int.from_bytes(crc_bytes, 'little')


def block_crc_calc(start, rar_bytes):
    bytes_for_crc = rar_bytes[start:start + rar_bytes[start] + 1]
    return zlib.crc32(bytes_for_crc) & 0xFFFFFFFF


def analyze_rar5_structure(filename):
    rar_bytes = read_file(filename)
    archive_size = len(rar_bytes)
    print(f"Archive -> Name: {filename}, Size: {archive_size} bytes")

    offset = 8
    header_len = rar_bytes[offset + 4]
    header_end = offset + header_len
    read_crc = block_crc_read(offset, rar_bytes)
    calc_crc = block_crc_calc(offset + 4, rar_bytes)

    print(f"Main Header [{offset}, {header_end}] CRC ->", end=" ")
    print(f"Read: {read_crc:0x}", end=", ")
    print(f"Calc: {calc_crc:0x}")

    with rarfile.RarFile(filename) as rf:
        for file_info in rf.infolist():

            if file_info.is_file():

                # FILE HEADER CRC
                offset = file_info.header_offset
                header_len = rar_bytes[offset + 4]
                header_end = offset + header_len
                read_crc = block_crc_read(offset, rar_bytes)
                calc_crc = block_crc_calc(offset + 4, rar_bytes)
                print(f"File '{file_info.filename}'", end=" ")
                print(f"Header [{offset}, {header_end}] CRC ->", end=" ")
                print(f"Read: {read_crc:0x}", end=", ")
                print(f"Calc: {calc_crc:0x}")

                # FILE DATA CRC
                read_crc = file_info.CRC
                uncompressed_data = rf.read(file_info.filename)
                calc_crc = zlib.crc32(uncompressed_data) & 0xFFFFFFFF
                print(f"File '{file_info.filename}' Data CRC ->", end=" ")
                print(f"Read: {read_crc:0x}", end=", ")
                print(f"Calc: {calc_crc:0x}")

    offset = archive_size - 8
    read_crc = block_crc_read(offset, rar_bytes)
    calc_crc = block_crc_calc(offset + 4, rar_bytes)

    print("End Block CRC ->", end=" ")
    print(f"Read: {read_crc:0x}", end=", ")
    print(f"Calc: {calc_crc:0x}")


analyze_rar5_structure('dllDONE.rar')

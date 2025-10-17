import rarfile
import zlib
import sys
from typing import List, Dict, Any


class RAR5Analyzer:
    def __init__(self, filename: str):
        self.filename = filename
        self.rar_bytes = self._read_file(filename)
        self.archive_size = len(self.rar_bytes)
        self.headers = []

    def _read_file(self, filename):
        with open(filename, 'rb') as file:
            return file.read()

    def block_crc_read(self, start: int) -> int:
        crc_bytes = self.rar_bytes[start:start + 4]
        return int.from_bytes(crc_bytes, 'little')

    def block_crc_calc(self, start: int) -> int:
        bytes_for_crc = self.rar_bytes[start:start + self.rar_bytes[start] + 1]
        return zlib.crc32(bytes_for_crc) & 0xFFFFFFFF

    def analyze(self):
        self.headers = []

        # Main Header
        offset = 8
        header_len = self.rar_bytes[offset + 4]
        main_header = {
            'type': 'main_header',
            'header_start': offset,
            'header_end': offset + header_len + 4,
            'crc_read': self.block_crc_read(offset),
            'crc_calc': self.block_crc_calc(offset + 4)
        }
        self.headers.append(main_header)

        # File Headers
        with rarfile.RarFile(self.filename) as rf:
            for file_info in rf.infolist():
                if file_info.is_file():

                    # File Header CRC
                    offset = file_info.header_offset
                    header_len = self.rar_bytes[offset + 4]
                    file_header = {
                        'type': 'file_header',
                        'filename': file_info.filename,
                        'header_start': offset,
                        'header_end': offset + header_len + 4,
                        'crc_read': self.block_crc_read(offset),
                        'crc_calc': self.block_crc_calc(offset + 4),
                        'data_crc_read': file_info.CRC
                    }

                    # File Data CRC
                    uncompressed_data = rf.read(file_info.filename)
                    crc32 = zlib.crc32(uncompressed_data) & 0xFFFFFFFF
                    file_header['data_crc_calc'] = crc32
                    self.headers.append(file_header)

        # End Block Header
        offset = self.archive_size - 8
        end_header = {
            'type': 'end_block',
            'header_start': offset,
            'header_end': self.archive_size - 1,
            'crc_read': self.block_crc_read(offset),
            'crc_calc': self.block_crc_calc(offset + 4)
        }
        self.headers.append(end_header)

    def get_headers(self) -> List[Dict[str, Any]]:
        return self.headers


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rar_analyzer.py <rar_file>")
        sys.exit(1)

    filename = sys.argv[1]
    analyzer = RAR5Analyzer(filename)
    analyzer.analyze()

    headers = analyzer.get_headers()
    for header in headers:
        print(f"\nHeader: {header}")

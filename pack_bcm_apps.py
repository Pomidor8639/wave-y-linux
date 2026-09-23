#!/usr/bin/env python3
"""
pack_bcm_apps.py - Packs raw ARM zImage into Samsung Broadcom BCM2153/21553 apps_compressed.bin
with valid 1024-byte s_bada_footer and Broadcom security certificate for MultiLoader v5.67.
"""

import os
import sys
import struct
import hashlib

BCM_CERT_BLOCK = (
    b'y\x13Fy\\\xa0\x055\xe1\xe6T\x10\xb7\x01M7V\'V\xbd\r@\xfa\xc4\xb6\xe3\xce`\xab\x1b\x97\t'
    b'}\x96\xb5[\x97S\x9d\xdcP@uJ\xfb\xe7\xb4\x00\xff$H:\xdc0\xb8\xc5k\xe5X\xbbjT _\x9d\xb2\xc46'
    b'y\xbb^GA\xff\xba\xbf\x843qF\x1b\x08\xf7\x8c\x13a\x1f\xd77\x9fjf5\xe1\xe4\xd7\xd7\x9c\x99\x06'
    b'UZ\x17T\x86\x08\x9c\x1c\x86\x91{\xba\x87um\xcaQ8\xc1D\xb1\xabP\xc1\xa5\xb1^\xd0\xa1\x93V\xf8'
    b'\x00\x00\xb8\x00b\xe9yWsL\xae\x01\xb1hH\xb4\xf5\x01g\xbf\xc3\x7fz\x8a\x93\xb8UY\x1d9HF\xbf'
    b'\x03!\x02"\xfc[\xd1\xf8\xfd\xa0\x9f\x84\x8d-]\x1eTx\xb6\xe3\xb6-\xc8\x80\xb3L\xb4\xf7uF\xf6'
    b'\x1dL\xbf\xf8Fq\x9f\x08,\xe8\x87\x10\x18ei\x19~\xf4\xa2\x0c:$\xb25\xc0+C\rz\x9c\\\x00\x92'
    b'\xf4t\x04`\x0cc\x12ZA\xf0\x05\x8a\x96\xfe$\xa0^m\x11|$\x93\x08\x80w-\x06$\xe3\xbd"\xe8\x8d#'
    b'\x00\x03;\xe6\n1\xfdR\x01\x99W\xb8.\xf5\x11l-.\nF\x0cz\xf4\x13\x05\xaf\x8b\xe8\x0cE\xb0r'
    b'\x07\x08\xf3\x08\x01PD\x1d\x18\xact\xb0\x01[\xb4T2\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    b'\xff\xff\xff\xff\xff\xffy\x13Fy\x00\x00\xa0\x01\xd4\x99\x8bET\xdb\x93\xa7\n\xad\xbb\xf8\xea '
    b'\xda\x03\x81"HoV!\xed\xad\xdeC\x93\xf0\xb0c\xd4\xad\xd2\x91\xdf\xe5\xceFk\'\xab\xa7\x15\xc5'
    b'Q\x96$boE\xfc?\xa2,\xc2\xfc\xd8\xb2\xba\xa4\x88\xd7\xd4\x88\xe355\xff\xf2&c\x05q\x8f\xc6'
    b'\xc4\xa6\xa0r}S723E+XX+LB3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00TkToolVer:2.0.0\x00\x00\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
)

def multiloader_md5(data):
    ctx = hashlib.md5()
    chunk_size = 64
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        if len(chunk) < chunk_size:
            chunk = chunk + b'\x00' * (chunk_size - len(chunk))
        ctx.update(chunk)
    return ctx.digest()

def pack_bada_apps(input_file, output_file, model_name='S5380', nand_addr=0x00C00000):
    with open(input_file, 'rb') as f:
        payload = f.read()

    payload_len = len(payload)
    if payload_len == 0:
        raise ValueError("Input file is empty")

    if payload_len > 0x30:
        magic = struct.unpack('<I', payload[0x24:0x28])[0]
        if magic == 0x016F2818:
            print(f"[*] Detected valid ARM Linux zImage (magic 0x{magic:08x})")

    pad_md5 = multiloader_md5(payload)
    print(f"[*] Payload size: {payload_len} bytes ({payload_len / 1024 / 1024:.2f} MB)")
    print(f"[*] MultiLoader Padded MD5: {pad_md5.hex()}")

    footer = bytearray(1024)

    # 0x00: Magic (0xABCDABCD)
    struct.pack_into('<I', footer, 0, 0xABCDABCD)
    # 0x04: NAND Base Addr (0x00C00000 for APPS partition)
    struct.pack_into('<I', footer, 4, nand_addr)
    # 0x08: unk0 (Should Be Zero)
    struct.pack_into('<I', footer, 8, 0)
    # 0x0C: Model Name (ASCII, max 32 chars)
    name_bytes = model_name.encode('latin1')[:31]
    footer[12 : 12 + len(name_bytes)] = name_bytes
    # 0x2C: Ext (ASCII, max 8 chars)
    ext_bytes = b'bin'
    footer[44 : 44 + len(ext_bytes)] = ext_bytes

    # 0x34: unk1 flags (5 x uint32)
    # flag 0: 0
    # flag 1: 1 (Bypasses MultiLoader client hash check, but reads NAND geometry)
    # flag 2: 2 (NAND Type 2)
    # flag 3: 0x1000 (NAND Page Size: 4096 bytes)
    # flag 4: 0x40000 (NAND Block Size: 256 KB = 0x40000)
    struct.pack_into('<5I', footer, 52, 0, 1, 2, 0x1000, 0x40000)

    # 0x48: Broadcom BCM Security Certificate (512 bytes, magic 0x79461379)
    footer[0x48 : 0x48 + 512] = BCM_CERT_BLOCK

    # 0x248: MD5 Checksum (16 bytes, using MultiLoader padded MD5)
    footer[0x248 : 0x248 + 16] = pad_md5

    with open(output_file, 'wb') as f:
        f.write(payload)
        f.write(footer)

    total_len = payload_len + 1024
    print(f"[+] Successfully wrote {output_file} ({total_len} bytes)")
    print(f"[+] Ready for flashing via MultiLoader V5.67 [BRCM2153]!")

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'zImage'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'apps_compressed.bin'
    model = sys.argv[3] if len(sys.argv) > 3 else 'S5380'
    pack_bada_apps(src, dst, model)

#!/usr/bin/env python3
"""
pack_bcm_apps.py - Packs raw ARM zImage into Samsung Broadcom BCM2153/21553 apps_compressed.bin
with valid 1024-byte s_bada_footer for MultiLoader v5.67.
"""

import os
import sys
import struct
import hashlib

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

    md5_digest = hashlib.md5(payload).digest()
    print(f"[*] Payload size: {payload_len} bytes ({payload_len / 1024 / 1024:.2f} MB)")
    print(f"[*] Payload MD5:  {md5_digest.hex()}")

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
    struct.pack_into('<5I', footer, 52, 0, 2, 2, 0x1000, 0x40000)

    # 0x228: Tool Version string
    footer[0x228 : 0x228 + 16] = b'TkToolVer:2.0.0\x00'

    # 0x248: MD5 Checksum (16 bytes)
    footer[0x248 : 0x248 + 16] = md5_digest

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

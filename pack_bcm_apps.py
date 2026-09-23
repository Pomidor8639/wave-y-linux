#!/usr/bin/env python3
"""
pack_bcm_apps.py - Packs raw ARM zImage into Samsung Broadcom BCM2153/21553 apps_compressed.bin
with valid 1024-byte s_bada_footer for MultiLoader v5.67.
"""

import os
import sys
import struct
import hashlib

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
    # flag 1: 1 (Bypasses MD5 hash check since 1 < 2, but enables NAND size copy since 1 >= 1)
    # flag 2: 2 (NAND Type 2)
    # flag 3: 0x1000 (NAND Page Size: 4096 bytes)
    # flag 4: 0x40000 (NAND Block Size: 256 KB = 0x40000)
    struct.pack_into('<5I', footer, 52, 0, 1, 2, 0x1000, 0x40000)

    # 0x228: Tool Version string
    footer[0x228 : 0x228 + 16] = b'TkToolVer:2.0.0\x00'

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

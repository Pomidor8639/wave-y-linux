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
    b'y\x13FydyT\xf7*\xc7*\xc3\x85l\x04\xcb7\x0b\xe8\xdfe]s\x84r\xdf\x94\xc5\xc9\xac\xb3m\xc4r\x0b\xf8?\xabG\xeda\x88\xea\xbf\xd7q\x98\xe8\xd3\xbc\xc4\x14\xb4-\x10\xe5\xb0kl-\xa1\tm\xca+\xe48\x86m3l|\x86o\x97L7\xb1\xe1\x18\xd4\x9a\x88\xd1\xefP\xe5*\xf9E\x12)\xd7^B,\xe13z\xdeY\xe5\x8c\x174\xf4\x18\xc4*#\xae\x07G\xd1\xd3\xf7\xe3\xd1\xd0\xaa\x9f\xdfh\xcb{\x81\xb6g\xb0r\xf6\xe1\x00\x00\xa8\x00\x08k\xb6\xd1\xb4\x8bhfb\xae_\xfc:Zzb\xe41\x184d"p\xaa\x8a\x15\x83\x0f#\x98\x97\xaf\xd4\x90\xb5\x12\x93,-(:\x9f\xc0\xd7\xc2\x85T?9\xd4\xe2\xbe\x1f\xa37\xf7\xc1\\\n\xe1,\xe3\xf3\xd7\x1amI\x11@\xc3\x98(R\xce}\x1f\rh\x80\n\x9a\xc6\x9a\nh\xdb\xe1\x07\xd7\xf1\xfd\x10(\xb9\xe5\x16L\x1a\xd5\x00r\x1dU\x14\xc0\xc1&\x03(\xcb=\x01\xdc4\x95 \xab\x9ff\t\x18M\x91\x12\x9c-\xdb\n\xc8\xaa\xbb\x07\x80H9\x04\xf51\xe0\x07A\x97V\n\xd6T5\x10\xd6\x11\x8e\x1d\xd2r\x02\x12\x9cdB\x1c ^%\x08F,\xb9\x01s\xe04\x11\xed\x0f=\x0b\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xffy\x13Fy\x00\x00\xac\x01%\xef\xc4+\xe6\n\xb1\xff9\xd6DB\xb5}\xad\xd9\xb9\xbfW\xdd`\xa5\x85\xdcWd\x06\x17OM\xb00\x9f\x14/\x88\x02\x8d\x87F\x93\xbb(\x9b\x14B\xdb\xf9tb7\xf3O\x8f\\xW\xae\x8dh\xc1\xe6_\x85\xb8\x81@f\xb3z\xaep\x97\xdc\xcd\xbf\x12C4\xa9S5380D+XX+LF1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00TkToolVer:2.0.0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
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

def pack_bada_apps(input_file, output_file, model_name='S5380D', nand_addr=0x00E00000):
    with open(input_file, 'rb') as f:
        payload = f.read()

    raw_len = len(payload)
    if raw_len == 0:
        raise ValueError("Input file is empty")

    if raw_len > 0x30:
        magic = struct.unpack('<I', payload[0x24:0x28])[0]
        if magic == 0x016F2818:
            print(f"[*] Detected valid ARM Linux zImage (magic 0x{magic:08x})")

    # Align payload to NAND block boundary (256 KB = 262144 bytes)
    block_size = 262144
    rem = raw_len % block_size
    if rem != 0:
        pad_len = block_size - rem
        payload = payload + b'\x00' * pad_len
        print(f"[*] Padded payload by {pad_len} bytes to align with 256 KB NAND blocks")

    payload_len = len(payload)
    pad_md5 = multiloader_md5(payload)
    print(f"[*] Final payload size: {payload_len} bytes ({payload_len / 1024 / 1024:.2f} MB, {payload_len // block_size} blocks)")
    print(f"[*] MultiLoader Padded MD5: {pad_md5.hex()}")

    footer = bytearray(1024)

    # 0x00: Magic (0xABCDABCD)
    struct.pack_into('<I', footer, 0, 0xABCDABCD)
    # 0x04: NAND Base Addr (0x00E00000 for APPS partition on GT-S5380)
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
    # (0, 2, 2, 4096, 262144) matches GT-S5380 NAND geometry & MultiLoader verification
    struct.pack_into('<5I', footer, 52, 0, 2, 2, 4096, 262144)

    # 0x48: Broadcom BCM Security Certificate (512 bytes, authentic S5380D)
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
    model = sys.argv[3] if len(sys.argv) > 3 else 'S5380D'
    pack_bada_apps(src, dst, model)


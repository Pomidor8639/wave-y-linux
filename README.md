# Linux for Samsung Wave Y (GT-S5380 / GT-S5380F)

Minimal Linux 2.6.35.7 kernel with embedded BusyBox initramfs targeting the Broadcom BCM21553 SoC (ARM11 @ 832 MHz) on the Samsung Wave Y.

## Specifications
- **Target:** Samsung Wave Y (GT-S5380 / GT-S5380F)
- **SoC:** Broadcom BCM21553 (ARMv6 / ARM1136JF-S)
- **Base:** Samsung totoro / bcm215xx
- **Console:** UART A (`/dev/ttyS0` @ 115200n8 via USB COM port)
- **Init:** BusyBox `/init` with interactive `/bin/sh` shell
- **Flashing Tool:** MultiLoader v5.67 (Broadcom BRCM2153 mode)

## Architecture
1. **Kernel:** Linux 2.6.35.7 compiled with Google `arm-eabi-4.8` GCC toolchain.
2. **Rootfs:** Built with static BusyBox (armv6l) packed into `rootfs.cpio.gz` and embedded in `zImage`.
3. **Early Output:** `CONFIG_DEBUG_LL=y` and `CONFIG_EARLY_PRINTK=y` routed directly to physical UART A (`0x08820000`).

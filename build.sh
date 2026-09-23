#!/bin/bash
set -e

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential bc bison flex libssl-dev gcc-arm-linux-gnueabi binutils-arm-linux-gnueabi cpio wget curl git python3

echo '=== Step 1: Clone Kernel Source ==='
git clone --depth=1 -b cm-11.0 https://github.com/CyanogenMod-ARMv6/android_kernel_samsung_bcm21553-common.git kernel
cp kernel/include/linux/compiler-gcc4.h kernel/include/linux/compiler-gcc5.h
cp kernel/include/linux/compiler-gcc4.h kernel/include/linux/compiler-gcc7.h
cp kernel/include/linux/compiler-gcc4.h kernel/include/linux/compiler-gcc8.h
sed -i 's/extern inline void \*return_address/static inline void \*return_address/' kernel/arch/arm/include/asm/ftrace.h

echo '=== Step 1.1: Patch Machine ID for Bada Bootloader ==='
sed -i 's/mov\tr7, r1/ldr\tr7, =477/' kernel/arch/arm/boot/compressed/head.S
sed -i 's/mov\tr8, r2/mov\tr8, #0/' kernel/arch/arm/boot/compressed/head.S
sed -i 's/ENTRY(stext)/ENTRY(stext)\n\tmov\tr0, #0\n\tldr\tr1, =477\n\tmov\tr2, #0/' kernel/arch/arm/kernel/head.S

echo '=== Step 2: Build Minimal RootFS ==='
mkdir -p rootfs_build/bin rootfs_build/sbin rootfs_build/etc rootfs_build/proc rootfs_build/sys rootfs_build/dev rootfs_build/tmp rootfs_build/root
wget -q https://busybox.net/downloads/binaries/1.21.1/busybox-armv6l -O rootfs_build/bin/busybox
chmod +x rootfs_build/bin/busybox
for app in sh ls cat echo ps mount umount dmesg sleep reboot hostname clear uname free kill grep head tail date; do
  ln -s busybox rootfs_build/bin/$app
done
cp rootfs/init rootfs_build/init
chmod +x rootfs_build/init
cd rootfs_build
find . | cpio -o -H newc | gzip -9 > ../kernel/rootfs.cpio.gz
cd ..
ls -lh kernel/rootfs.cpio.gz

echo '=== Step 3: Configure and Compile Kernel ==='
cp config/wave_y_defconfig kernel/arch/arm/configs/wave_y_defconfig
cd kernel
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabi-
make wave_y_defconfig
sed -i 's/CONFIG_VGA_CONSOLE=y/# CONFIG_VGA_CONSOLE is not set/' .config || true
echo "# CONFIG_VGA_CONSOLE is not set" >> .config
echo "CONFIG_DUMMY_CONSOLE=y" >> .config
echo "CONFIG_BCM_LCD_SKIP_INIT=y" >> .config
make -j4 zImage
cd ..

echo '=== Step 4: Export and Package Artifacts ==='
mkdir -p output
cp kernel/arch/arm/boot/zImage output/zImage
python3 pack_bcm_apps.py output/zImage output/apps_compressed.bin S5380D
ls -lh output/
echo '=== BUILD SUCCESSFUL ==='

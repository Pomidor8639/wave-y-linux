with open('config/wave_y_defconfig', 'r') as f:
    lines = f.readlines()

overrides = {
    'CONFIG_CMDLINE': 'CONFIG_CMDLINE="console=tty0 console=ttyS0,115200n8 earlyprintk init=/init"\n',
    'CONFIG_CMDLINE_FORCE': 'CONFIG_CMDLINE_FORCE=y\n',
    'CONFIG_DEBUG_LL': 'CONFIG_DEBUG_LL=y\n',
    'CONFIG_EARLY_PRINTK': 'CONFIG_EARLY_PRINTK=y\n',
    'CONFIG_BLK_DEV_INITRD': 'CONFIG_BLK_DEV_INITRD=y\n',
    'CONFIG_INITRAMFS_SOURCE': 'CONFIG_INITRAMFS_SOURCE="rootfs.cpio.gz"\n',
    'CONFIG_INITRAMFS_COMPRESSION_GZIP': 'CONFIG_INITRAMFS_COMPRESSION_GZIP=y\n',
    'CONFIG_DEFAULT_HOSTNAME': 'CONFIG_DEFAULT_HOSTNAME="wave-y"\n',
    'CONFIG_VT': 'CONFIG_VT=y\n',
    'CONFIG_VT_CONSOLE': 'CONFIG_VT_CONSOLE=y\n',
    'CONFIG_HW_CONSOLE': 'CONFIG_HW_CONSOLE=y\n',
    'CONFIG_FRAMEBUFFER_CONSOLE': 'CONFIG_FRAMEBUFFER_CONSOLE=y\n',
    'CONFIG_FRAMEBUFFER_CONSOLE_DETECT_PRIMARY': 'CONFIG_FRAMEBUFFER_CONSOLE_DETECT_PRIMARY=y\n',
    'CONFIG_FRAMEBUFFER_CONSOLE_ROTATION': 'CONFIG_FRAMEBUFFER_CONSOLE_ROTATION=y\n',
    'CONFIG_FONTS': 'CONFIG_FONTS=y\n',
    'CONFIG_FONT_8x16': 'CONFIG_FONT_8x16=y\n',
    'CONFIG_LOGO': 'CONFIG_LOGO=y\n',
    'CONFIG_LOGO_LINUX_CLUT224': 'CONFIG_LOGO_LINUX_CLUT224=y\n',
}

new_lines = []
seen = set()
for line in lines:
    replaced = False
    for k, v in overrides.items():
        if line.startswith(k + '=') or line.startswith('# ' + k + ' ') or line.startswith('# ' + k + '=\n'):
            new_lines.append(v)
            seen.add(k)
            replaced = True
            break
    if not replaced:
        new_lines.append(line)

for k, v in overrides.items():
    if k not in seen:
        new_lines.append(v)

with open('config/wave_y_defconfig', 'w') as f:
    f.writelines(new_lines)

print("Successfully updated config/wave_y_defconfig!")

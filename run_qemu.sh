#!/bin/bash

THISDIR=`dirname $0`
KERNEL_SRC_DIR=${THISDIR}/linux-stable/
PORT=10023
SMP=4

echo "run \`ssh -i ssh/id_rsa -p ${PORT} root@localhost\`"

qemu-system-x86_64 -hda ${THISDIR}/wheezy.img -m 1024M -smp ${SMP} \
	-net user,hostfwd=tcp:127.0.0.1:${PORT}-:22 -net nic \
	-kernel $KERNEL_SRC_DIR/arch/x86/boot/bzImage \
	-append "console=ttyS0 root=/dev/sda earlyprintk=serial" \
	-nographic \
	-s  \
	-pidfile vm_pid  -enable-kvm


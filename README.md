# clang-kernel-build
Steps to build the Linux kernel using Clang

0. Start with an empty dir

	```
	git clone https://github.com/ramosian-glider/clang-kernel-build.git
	cd clang-kernel-build
	export WORLD=`pwd`
	```

1. Install Clang from Chromium:

	```
	cd $WORLD
	# Instruction taken from http://llvm.org/docs/LibFuzzer.html
	mkdir TMP_CLANG
	cd TMP_CLANG
	git clone https://chromium.googlesource.com/chromium/src/tools/clang
	cd ..
	TMP_CLANG/clang/scripts/update.py
	```

2. Clone the Linux source tree

	```
	cd $WORLD
	git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git
	cd linux-stable
	git reset --hard v4.6.7
	```

3. Download and apply the patches

	```
	cd $WORLD
	wget http://buildbot.llvm.linuxfoundation.org/configs/x86_64/kernel-patches.tar.bz2
	tar -jxf kernel-patches.tar.bz2
	cd linux-stable
	patch -p1 -i ../clang-flags.patch
	patch -p1 -i ../clang-uaccess.patch
	patch -p1 -i ../patches/boot-workaround-PR18415.patch
	```

4. Configure and build the kernel

	```
	cd $WORLD
	export CLANG_PATH=`pwd`/third_party/llvm-build/Release+Asserts/bin/
	cd linux-stable
	make CC=$CLANG_PATH/clang defconfig
	make CC=$CLANG_PATH/clang -j64 2>&1 | tee build.log
	```

5. Set up the VM:

	```
	cd $WORLD
	wget https://raw.githubusercontent.com/google/sanitizers/master/address-sanitizer/kernel_buildbot/create_os_image.sh
	# create_os_image.sh requires sudo
	sh create_os_image.sh
	```

6. Run the VM

	```
	cd $WORLD
	./run_qemu.sh
	# in a separate console:
	ssh -i ssh/id_rsa -p 10023 root@localhost
	```

# Known problems
1. The kernel doesn't boot if configured with CONFIG_KVM (e.g. `make kvmconfig`)
2. The kernel crashes in vm_unmap_aliases() if synced to v.4.7 (regressed at 80c4bd7a5e4368b680e0aeb57050a1b06eb573d8)

# Debugging

	```
	# Start the VM before running GDB
	cd $WORLD
	gdb -x gdb.script
	(gdb) br dump_stack
	```


# Hacking

	```
	# Perform these steps instead of Step 4 above.
	cd $WORLD/linux-stable
	make CC=$CLANG_PATH/clang defconfig
	make CC=`pwd`/../clang_wrapper.py 2>&1 | tee build.log
	```

The handy `clang_wrapper.py` lets you add arguments to Clang invocation, measure compilation times or fall back to GCC for certain files.

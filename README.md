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
	# Used to be:
	#  git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git
	# , but v4.13-rc7 is still unstable.
	git clone https://github.com/torvalds/linux.git linux-stable
	cd linux-stable
	git reset --hard v4.13-rc7
	```

3. Apply the patches

	```
	cd $WORLD
	cd linux-stable
	# These two patches are in ToT already:
	#   patch -p1 -i ../0001-x86-boot-64-clang-use-fixup_pointer-to-access-next_e.patch
	#   patch -p1 -i ../ext4-fix.patch
	# There's an ongoing discussion about how this can be done better, see https://lkml.org/lkml/2017/7/28/775
	patch -p1 -i ../clang-uaccess.patch
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

Also, get yourself a log symbolizer: https://raw.githubusercontent.com/google/sanitizers/master/address-sanitizer/tools/kasan_symbolize.py

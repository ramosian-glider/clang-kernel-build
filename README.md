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
	git reset --hard v4.12-rc7
	```

3. Apply the patches

	```
	cd $WORLD
	cd linux-stable
	git cherry-pick 96d3599c8477016025e5b20debd1cb82aa06cdae
	git cherry-pick a92a9808f75f9a81aa67199ffb8b404885e7facf
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
2. Newer kernels (e.g. v. 4.13-rc4) have the necessary patches, but cannot boot :(

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

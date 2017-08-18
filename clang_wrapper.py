#!/usr/bin/env python
from collections import defaultdict
import optparse
import os
import subprocess
import sys
import time

WORLD_PATH = os.path.dirname(os.path.abspath(__file__))

COMPILER_PATH = {
  'gcc': 'gcc',
  'clang': '/'.join([os.getenv('CLANG_PATH'), 'clang'])
}

FILTER = {'gcc': ['-Qunused-arguments', '-no-integrated-as', '-mno-global-merge',
  '-Wdate-time', '-Wno-unknown-warning-option', '-Wno-initializer-overrides', '-Wno-tautological-compare',
  '-Wincompatible-pointer-types', '-Wno-gnu', '-Wno-format-invalid-specifier',
  '-Werror=date-time', '-Werror=incompatible-pointer-types',
],'clang': ['-maccumulate-outgoing-args', '-falign-jumps=1', '-falign-loops=1']}
SOURCE = 'source'
WRAPPER_LOG = WORLD_PATH + '/wrapper.log'
LOG = sys.stderr
LOG_OPTIONS = {'time': True, 'argv': True, 'kmsan_inst': True}

def compiler(flags):
  path = 'clang'
  #if SOURCE == 'security/selinux/hooks.c':
  #  return 'gcc'
  return path  # no need to use GCC for now
  if SOURCE in flags:
    source = flags[SOURCE]
    #print >>LOG, source
    # kernel/* ok
    # kernel/[st] broken
    # kernel/[kmpstuw] broken
    # kernel/[abckmpstuw] broken
    # kernel/[abcdefgkmpstuw] ok
    # kernel/[defgkmpstuw] ok
    # kernel/[defgkm] ok
    # kernel/[defg] ok
    # kernel/[de] broken
    # kernel/[fg] ok
    # kernel/[f] broken
    # kernel/[g] ok -- that's kernel/groups.h
    if source.startswith('kernel/'):
      pieces = source.split('/')
      if pieces[1][0] in ['g']:
        path = 'gcc'
    #print >>LOG, path
  return path

def filter_args(argv, cname):
  new_argv = []
  for arg in argv:
    if arg not in FILTER[cname]:
      new_argv.append(arg)
  return new_argv

def add_to_list(lst, prefix, files):
  for f in files:
    lst.append(prefix + f)

def want_msan_for_file(source):
  if source.endswith('.S'):
    return False
  # Order of application: exact blacklist > starts_whitelist > starts_blacklist
  starts_whitelist = []
  starts_blacklist = []
  # Only exact filenames, no wildcards here!
  exact_blacklist = []

  starts_blacklist += ['mm/kmsan/', 'arch/x86/']
  #starts_blacklist += ['drivers/firmware/efi/']
  exact_blacklist += ['mm/slab.c', 'mm/slub.c', 'mm/slab_common.c', 'lib/stackdepot.c']
  # TODO: for debugging KMSAN only
  # vsprintf.c deadlocks.
  ###starts_blacklist += ['kernel/printk/printk.c', 'lib/vsprintf.c']
  exact_blacklist += ['lib/vsprintf.c']
  # does not link
  exact_blacklist += ['arch/x86/boot/early_serial_console.c', 'arch/x86/boot/compressed/early_serial_console.c']

  for i in 'bcdefhikmnrstuvw':
    starts_blacklist.append('mm/' + i)
  starts_blacklist += ['kernel/']

  mm_black = ['percpu.c', 'pagewalk.c', 'process_vm_access.c', 'percpu-km.c', 'pgtable-generic.c']
  mm_black += ['percpu-vm.c', 'page_counter.c', 'page_ext.c', 'page_idle.c', 'page_io.c', 'page_isolation.c']
  mm_black += ['page_owner.c', 'page_poison.c', 'page_alloc.c', 'mempolicy.c']
  add_to_list(starts_blacklist, 'mm/', mm_black)

  # TODO: printk takes lock, calls memchr() on uninit memory, memchr() reports an uninit and attempts to take the same lock.
  #starts_blacklist += ['lib/string.c'] # TODO: handle
  # TODO: lib/vsprintf.c deadlocks when printint reports.
  exact_blacklist += ['init/main.c']

  starts_whitelist += ['kernel/time/']
  starts_whitelist += ['kernel/rcu/']
  starts_whitelist += ['arch/x86/lib/delay.c']
  starts_whitelist += ['kernel/irq/handle.c', 'kernel/irq/irqdesc.c']

  arch_x86_kernel_white = ['time.c', 'apic/apic.c', 'apic/io_apic.c', 'acpi/boot.c', 'process.c', 'rtc.c', 'irq.c', 'sys_x86_64.c']
  add_to_list(starts_whitelist, 'arch/x86/kernel/', arch_x86_kernel_white)

  starts_whitelist += ['arch/x86/pci/', 'arch/x86/lib/', 'arch/x86/boot/']

  starts_whitelist += ['arch/x86/mm/ioremap.c', 'arch/x86/mm/pat.c', 'arch/x86/mm/fault.c']
  starts_whitelist += ['kernel/printk/printk.c']


  kernel_sched_white = ['wait.c', 'completion.c', 'idle.c', 'rt.c', 'core.c', 'cputime.c', 'fair.c']
  add_to_list(starts_whitelist, 'kernel/sched/', kernel_sched_white)

  for i in 'abcdw':
    starts_whitelist.append('kernel/' + i)

  mm_white = ['backing-dev.c', 'util.c', 'vmalloc.c', 'mmap.c', 'rmap.c', 'interval_tree.c', 'shmem.c', 'readahead.c']
  mm_white += ['filemap.c', 'swap.c', 'truncate.c', 'page-writeback.c', 'swap_state.c', 'memory.c', 'swapfile.c', 'mlock.c']
  add_to_list(starts_whitelist, 'mm/', mm_white)

  kernel_locking_white = ['rwsem-spinlock.c', 'rwsem-xadd.c']
  add_to_list(starts_whitelist, 'kernel/locking/', kernel_locking_white)

  kernel_white = ['softirq.c', 'smpboot.c', 'workqueue.c', 'kthread.c', 'stop_machine.c', 'fork.c', 'exit.c', 'groups.c', 'signal.c']
  kernel_white += ['audit.c', 'params.c', 'pid.c', 'cred.c', 'user.c', 'nsproxy.c', 'kmod.c', 'smp.c', 'cpu.c']
  add_to_list(starts_whitelist, 'kernel/', kernel_white)
  starts_whitelist += ['kernel/trace/', 'kernel/events/']

  for black in exact_blacklist:
    if source == black:
      if LOG_OPTIONS['kmsan_inst']:
        print >>LOG, 'kmsan: exact_blacklist: skipping %s' % source
      return False
  for white in starts_whitelist:
    if source.startswith(white):
      if LOG_OPTIONS['kmsan_inst']:
        print >>LOG, 'kmsan: instrumenting %s' % source
      return True
  for black in starts_blacklist:
    if source.startswith(black):
      if LOG_OPTIONS['kmsan_inst']:
        print >>LOG, 'kmsan: starts_blacklist: skipping %s' % source
      return False

  return bool(source)


def msan_argv(flags, argv):
  source = flags[SOURCE]
  argv += ['-Wno-address-of-packed-member']
  if want_msan_for_file(source):
    argv += ['-fsanitize=kernel-memory', '-mllvm', '-msan-kernel=1', '-mllvm', '-msan-keep-going=1', '-mllvm', '-msan-track-origins=2']
#    ]
#    '-fsanitize-memory-track-origins=2']
  return argv

def compiler_argv(flags, argv):
  cname = compiler(flags)
  new_argv = [COMPILER_PATH[cname]] + filter_args(argv, cname)
  if os.getenv('USE_MSAN'):
    new_argv = msan_argv(flags, new_argv)
  return new_argv

def make_flags(argv):
  flags = defaultdict(str)
  argv = argv[1:]
  for arg in argv:
    if arg.endswith('.c'):
      flags[SOURCE] = arg
    if arg.endswith('.S'):
      flags[SOURCE] = arg
  return flags, argv

def main(argv):
  global LOG
  LOG = file(WRAPPER_LOG, 'a+')
  if LOG_OPTIONS['argv']:
    print >>LOG, ' '.join(argv)
  flags, argv = make_flags(argv)
  new_argv = compiler_argv(flags, argv)
  #print >>LOG, ' '.join(new_argv)
  start_time = time.time()
  ret = subprocess.call(new_argv)
  end_time = time.time()
  if LOG_OPTIONS['time']:
    print >> LOG, 'Time elapsed: {:.3f} seconds'.format(end_time - start_time)
  LOG.close()
  return ret


if __name__ == '__main__':
  sys.exit(main(sys.argv))

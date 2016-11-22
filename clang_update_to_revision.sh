#!/bin/bash

set -x
REVISION=$1

function update_path_rev {
  (
    cd $1
    if [ -z "${REVISION}" ]
    then
      svn up || exit 1
    else
      svn up -r ${REVISION} || exit 1
    fi
  )
}

function get_llvm {
  svn co http://llvm.org/svn/llvm-project/llvm/trunk .
  cd tools
  svn co http://llvm.org/svn/llvm-project/cfe/trunk clang
  cd ../projects
  svn co http://llvm.org/svn/llvm-project/compiler-rt/trunk compiler-rt
  svn co http://llvm.org/svn/llvm-project/libcxx/trunk libcxx
  svn co http://llvm.org/svn/llvm-project/libcxxabi/trunk libcxxabi
}

if [ ! -d '.svn' ]; then
  ls -la
  get_llvm
fi

update_path_rev .
update_path_rev tools/clang
update_path_rev projects/compiler-rt
update_path_rev projects/libcxx
update_path_rev projects/libcxxabi
rm -rf llvm_cmake_build

mkdir llvm_cmake_build && cd llvm_cmake_build
#cmake -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_ASSERTIONS=ON `pwd`/../
cmake  -DLLVM_ENABLE_ASSERTIONS=OFF -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE='-O3 -DNDEBUG  -fno-omit-frame-pointer' `pwd`/../

make -j64 clang

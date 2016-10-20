#!/bin/bash

set -x
REVISION=$1

function update_path_rev {
  (
    cd $1
    if [ -z "${REVISION}" ]
    then
      svn up
    else
      svn up -r ${REVISION}
    fi
  )
}

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

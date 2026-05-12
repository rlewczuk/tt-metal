---
description: validate and fix CMakeLists.txt for TTNN op
agent: build
---

Verify and fix cmake file $1 to ensure that public host API files are properly exported and installed for target defined in this file.
Directory where $1 resides is operation directory and it contains all implementation of given operation (or group of operations).
This operation should be performed in steps:

## Step 1: identify public API files

Look through operation directory and find all public API files in this directory.

Those are public API files:
* header files that contain only declarations of functions that return either `ttnn:Tensor`, `Tensor` or a structure of tensors (eg. `std::vector<ttnn:Tensor>`) and also accept tensors in at least some arguments
* are placed in the operation directory or in one of its subdirectories
* files included by other public API files that are residing in the operation directory or one of subdirectories
* example of proper API header file: `ttnn/cpp/ttnn/operations/transformer/sdpa/sdpa.hpp`


Those are NOT public API files:
* files whose names match `*_nanobind.hpp`, containing Python bindings for TNN ops
* compute kernels intended to be run on devices (typically in `kernels` subdirectory);
* host side infrastructure and support (typically in `device` subdirectory), eg. program factories and device operation definitions `*_program_factory.hpp`, `*_device_operation.hpp`
* all `.cpp` files (DO NOT read or analyze them at all, just skip them all)

Prepare a list of public API files as they will be used in subsequent steps.

## Step 2: ensure that all API files are present in `target_sources()`

Find `target_sources()` command in $1 and check its `FILES` section following `FILE_SET api` (i.e. list of files for this fileset).
It should contain list of API files detected in step 1. If `FILES` section is incomplete or empty, please add missing API files to it.


## Step 3: ensure `install()` for API files is present

Near the end of CMakeLists.txt there should be command like this:

```
install(TARGETS ttnn_op_myoperation FILE_SET api COMPONENT ttnn-dev LIBRARY COMPONENT tar)
```

Where `ttnn_op_myoperation` is name of target from `target_sources()` section.

If it is not present, then please add it.

## Step 4: make sure needed target link libraries have proper visibility (PUBLIC or PRIVATE)

If any of public API files found in step 1 contains includes to common TTNN files (eg. `ttnn/operations/core` or any other `ttnn/*` pointing to files/directories outside of the operation directory you currently work on), then `TTNN:Core` dependency in `target_link_libraries` should be `PUBLIC`:

```
target_link_libraries(ttnn_op_transformer PRIVATE TT::Metalium PUBLIC TTNN::Core)
```

## Final Remarks

1. You are supposed to fix build system, not code itself, so please DO NOT modify any other files than $1.

2. See `ttnn/cpp/ttnn/operations/transformer/CMakeLists.txt` for reference how to properly export public API files.

3. DO NOT run full build, it is too costly. Just make changes to `CMakeLists.txt`.

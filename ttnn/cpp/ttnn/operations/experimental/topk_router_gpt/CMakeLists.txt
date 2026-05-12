# SPDX-FileCopyrightText: 2026 Tenstorrent USA, Inc.
#
# SPDX-License-Identifier: Apache-2.0

include(sources.cmake)

add_library(ttnn_op_experimental_topk_router_gpt ${LIB_TYPE})
add_library(TTNN::Ops::Experimental::TopkRouterGpt ALIAS ttnn_op_experimental_topk_router_gpt)

target_precompile_headers(ttnn_op_experimental_topk_router_gpt REUSE_FROM TT::CommonPCH)
TT_ENABLE_UNITY_BUILD(ttnn_op_experimental_topk_router_gpt)

set_target_properties(
    ttnn_op_experimental_topk_router_gpt
    PROPERTIES
        INTERFACE_HEADER_SETS_TO_VERIFY
            api
)

target_sources(
    ttnn_op_experimental_topk_router_gpt
    PUBLIC
        FILE_SET api
        TYPE HEADERS
        BASE_DIRS ${FixmeOpAPIDir}
        FILES
            topk_router_gpt.hpp
            device/topk_router_gpt_device_operation.hpp
            device/topk_router_gpt_device_operation_types.hpp
            device/topk_router_gpt_program_factory.hpp
    PRIVATE
        ${TTNN_OP_EXPERIMENTAL_TOPK_ROUTER_GPT_SRCS}
)

target_include_directories(ttnn_op_experimental_topk_router_gpt PRIVATE ${FixmeOpIncDirs})
target_link_libraries(ttnn_op_experimental_topk_router_gpt PRIVATE TT::Metalium PUBLIC TTNN::Core)

install(TARGETS ttnn_op_experimental_topk_router_gpt LIBRARY COMPONENT tar)
install(TARGETS ttnn_op_experimental_topk_router_gpt FILE_SET api COMPONENT ttnn-dev LIBRARY COMPONENT tar)

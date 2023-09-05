# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from typing import cast, Optional, Tuple

import executorch.exir as exir
import torch

from executorch.backends.xnnpack.utils.configs import (
    get_xnnpack_capture_config,
    get_xnnpack_edge_compile_config,
)
from executorch.exir.dialects._ops import ops as exir_ops

### XNNPACK Capture ###
def capture_graph_for_xnnpack(
    module: torch.nn.Module,
    inputs: Tuple[torch.Tensor],
    enable_aot: Optional[bool] = None,
) -> exir.ExirExportedProgram:
    return exir.capture(
        module,
        inputs,
        get_xnnpack_capture_config(enable_aot=enable_aot),
    ).to_edge(get_xnnpack_edge_compile_config())


### XNNPACK Utils ###
PERM_NCHW_TO_NHWC = [0, 2, 3, 1]
PERM_NHWC_TO_NCHW = [0, 3, 1, 2]


def check_or_raise(condition: bool, err: str) -> None:
    """
    Raises runtime error if condition is false, with the given error message

    Args:
        condition: boolean condition to check
        err: error message to raise if condition is not true
    """
    if not condition:
        raise RuntimeError(err)


def get_input_node(node: torch.fx.Node, input_index: int) -> torch.fx.Node:
    return cast(torch.fx.Node, node.args[input_index])


def get_relu_fused_node(node: torch.fx.Node) -> Optional[torch.fx.Node]:
    """
    Checks if the current node is only consumed by a relu node and can be fused,
    if so, we return the relu node that can be fused, otherwise return None
    """
    if (
        len(node.users) == 1
        and list(node.users.keys())[0].target == exir_ops.edge.aten.relu.default
    ):
        relu_node = list(node.users.keys())[0]
        return relu_node

    return None
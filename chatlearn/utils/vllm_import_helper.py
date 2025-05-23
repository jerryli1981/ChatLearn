# Copyright 2024 Alibaba Group Holding Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
""""Version compatibility for vLLM"""

from typing import List, TypedDict
from typing_extensions import NotRequired
from chatlearn.utils.constant import CURRENT_VLLM_VERSION, VLLMVersion

# pylint: disable=unused-import,import-outside-toplevel,wrong-import-position,wrong-import-order
if CURRENT_VLLM_VERSION == VLLMVersion.v_0_3_0:
    # imports for vllm-030
    from vllm.core.block_manager import BlockSpaceManager
    from vllm.engine.llm_engine import LLMEngine
    from vllm.model_executor.model_loader import _set_default_torch_dtype
    from vllm.model_executor.parallel_utils import parallel_state
    from vllm.model_executor.parallel_utils.communication_op import tensor_model_parallel_all_gather
    from vllm.model_executor.parallel_utils.parallel_state import initialize_model_parallel
    from vllm.model_executor.weight_utils import initialize_dummy_weights

elif CURRENT_VLLM_VERSION == VLLMVersion.v_0_5_1:
    # imports for vllm-051
    from vllm.core.interfaces import BlockSpaceManager
    from vllm.distributed import parallel_state
    from vllm.distributed.communication_op import tensor_model_parallel_all_gather
    from vllm.distributed.parallel_state import init_world_group
    from vllm.distributed.parallel_state import initialize_model_parallel
    from vllm.engine.llm_engine import LLMEngine
    from vllm.engine.llm_engine import _load_generation_config_dict
    from vllm.engine.output_processor.interfaces import SequenceGroupOutputProcessor
    from vllm.engine.output_processor.stop_checker import StopChecker
    from vllm.inputs import INPUT_REGISTRY
    from vllm.inputs import TextTokensPrompt
    from vllm.model_executor.model_loader.utils import set_default_torch_dtype as _set_default_torch_dtype
    from vllm.model_executor.model_loader.weight_utils import initialize_dummy_weights
    from vllm.sequence import ExecuteModelRequest
    from vllm.transformers_utils.detokenizer import Detokenizer

elif CURRENT_VLLM_VERSION in [VLLMVersion.v_0_6_3, VLLMVersion.v_0_6_6]:
    # imports for vllm-063/-66
    from vllm.core.interfaces import BlockSpaceManager
    from vllm.distributed import parallel_state
    from vllm.distributed.communication_op import tensor_model_parallel_all_gather
    from vllm.distributed.parallel_state import init_world_group
    from vllm.distributed.parallel_state import initialize_model_parallel
    from vllm.distributed.utils import get_pp_indices
    from vllm.engine.async_llm_engine import _AsyncLLMEngine as LLMEngine
    if CURRENT_VLLM_VERSION == VLLMVersion.v_0_6_3:
        from vllm.engine.llm_engine import _load_generation_config_dict
    from vllm.engine.llm_engine import SchedulerContext, SchedulerOutputState
    from vllm.engine.output_processor.interfaces import SequenceGroupOutputProcessor
    from vllm.engine.output_processor.stop_checker import StopChecker
    from vllm.inputs import INPUT_REGISTRY
    from vllm.inputs.preprocess import InputPreprocessor
    from vllm.model_executor.model_loader.utils import set_default_torch_dtype as _set_default_torch_dtype
    from vllm.model_executor.model_loader.weight_utils import initialize_dummy_weights
    from vllm.model_executor.models.qwen2_moe import Qwen2MoeForCausalLM
    from vllm.sequence import ExecuteModelRequest
    from vllm.transformers_utils.detokenizer import Detokenizer

    class TextTokensPrompt(TypedDict):
        """It is assumed that :attr:`prompt` is consistent with
        :attr:`prompt_token_ids`. This is currently used in
        :class:`AsyncLLMEngine` for logging both the text and token IDs."""

        prompt: str
        """The prompt text."""

        prompt_token_ids: List[int]
        """The token IDs of the prompt."""

        multi_modal_data: NotRequired["MultiModalDataDict"]
        """
        Optional multi-modal data to pass to the model,
        if the model supports it.
        """


from vllm.core.scheduler import Scheduler
from vllm.engine.arg_utils import EngineArgs
from vllm.entrypoints.llm import LLM
from vllm.model_executor.models.llama import LlamaForCausalLM
from vllm.model_executor.models.qwen import QWenLMHeadModel
from vllm.model_executor.models.qwen2 import Qwen2ForCausalLM
from vllm.sampling_params import SamplingParams
from vllm.utils import Counter
from vllm.worker.worker import Worker


def get_block_manager_cls(version):
    if CURRENT_VLLM_VERSION == VLLMVersion.v_0_3_0:
        return BlockSpaceManager

    elif CURRENT_VLLM_VERSION in [VLLMVersion.v_0_5_1, VLLMVersion.v_0_6_3, VLLMVersion.v_0_6_6]:
        return BlockSpaceManager.get_block_space_manager_class(version)


def get_model_architecture(config):
    if CURRENT_VLLM_VERSION == VLLMVersion.v_0_3_0:
        from vllm.model_executor.model_loader import _get_model_architecture as get_model_architecture_v1
        return get_model_architecture_v1(config)

    elif CURRENT_VLLM_VERSION in [VLLMVersion.v_0_5_1, VLLMVersion.v_0_6_3, VLLMVersion.v_0_6_6]:
        from vllm.model_executor.model_loader.utils import get_model_architecture  as get_model_architecture_v2
        return get_model_architecture_v2(config)[0]


def get_pipeline_model_parallel_rank():
    if CURRENT_VLLM_VERSION == VLLMVersion.v_0_3_0:
        return parallel_state.get_pipeline_model_parallel_rank()

    elif CURRENT_VLLM_VERSION in [VLLMVersion.v_0_5_1, VLLMVersion.v_0_6_3, VLLMVersion.v_0_6_6]:
        return parallel_state.get_pp_group().rank_in_group


def get_pipeline_model_parallel_world_size():
    if CURRENT_VLLM_VERSION == VLLMVersion.v_0_3_0:
        return parallel_state.get_pipeline_model_parallel_world_size()

    elif CURRENT_VLLM_VERSION in [VLLMVersion.v_0_5_1, VLLMVersion.v_0_6_3, VLLMVersion.v_0_6_6]:
        return parallel_state.get_pp_group().world_size

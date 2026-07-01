# Reproduce & validate: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/   (clone of https://github.com/furiosa-ai/EfficientRollout)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

**Abstract:** Reinforcement learning (RL) has become a representative post-training paradigm for LLMs, enabling strong reasoning and agentic capabilities. However, rollout generation remains a dominant latency bottleneck because autoregressive sampling decodes responses sequentially and a small number of long-tailed generations often determine completion time. Speculative decoding (SD) offers a natural way to address this bottleneck, as it is a well-established technique for serving fixed LLMs that reduces latency by rapidly drafting tokens and accepting them through parallel verification while preserving the target-model distribution. However, its practical speedups do not directly carry over to RL rollouts: (i) the evolving target policy makes any fixed drafter increasingly mismatched with the policy's output distribution; and (ii) active batch sizes shrink throughout rollout decoding, shifting decoding from compute-bound to memory-bound regimes where parallel verification can exploit underutilized compute. Therefore, accelerating RL rollouts requires both a drafter that remains effective under long, high-temperature generations from an evolving policy and system-aware use of SD that avoids compute-bound regimes. We present EfficientRollout, a system-aware self-SD framework designed to address this gap for RL rollouts. EfficientRollout induces a quantized drafter from the target model (i.e. self-speculative decoding), keeping it coupled to the evolving policy without separate drafter pretraining or online adaptation. It further coordinates a system-aware SD toggle policy with acceptance-aware draft-length adaptation, enabling speculation only in beneficial regimes while matching the drafting budget to evolving drafter quality. EfficientRollout reduces rollout and end-to-end latency by up to 19.6% and 12.7%, respectively, over an accelerated AR rollout baseline, while preserving final model quality.

## Shipped code — file tree (`projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/`)

```
.gitignore
.pre-commit-config.yaml
LICENSE
README.md
img/banner.png
img/banner_animated.gif
pyproject.toml
requirements-test.txt
requirements.txt
scripts/__init__.py
scripts/calibrate_llama_instruct.sh
scripts/calibrate_qwen_14b.sh
scripts/calibrate_qwen_7b.sh
scripts/convert_data_for_model.py
scripts/install_vllm.sh
scripts/prepare_data_simplerl_8k_easy.sh
scripts/prepare_data_simplerl_8k_hard.sh
scripts/prepare_data_simplerl_8k_medium.sh
scripts/prepare_simplerl_zoo.py
scripts/profiling/measure_gemm_effective_tflops.py
scripts/profiling/measure_nccl_allreduce.py
scripts/quantize_utils.py
scripts/run_fit_and_validate.sh
scripts/run_llama3.1_8b_instruct_sd.sh
scripts/run_qwen2.5_14b_sd.sh
scripts/run_qwen2.5_7b_sd.sh
sd_toggle/README.md
sd_toggle/__init__.py
sd_toggle/__main__.py
sd_toggle/cli.py
sd_toggle/config.py
sd_toggle/configs/F_eff_bench_a100.json
sd_toggle/configs/a100_tp1_llama318binstruct.json
sd_toggle/configs/a100_tp1_qwen2514b.json
sd_toggle/configs/a100_tp1_qwen257b.json
sd_toggle/configs/c_comm_bench_a100.json
sd_toggle/configs/model_constants_llama318binstruct_tp1.json
sd_toggle/configs/model_constants_qwen2514b_tp1.json
sd_toggle/configs/model_constants_qwen257b_tp1.json
sd_toggle/configs/sweep_a100_tp1_llama318binstruct.csv
sd_toggle/configs/sweep_a100_tp1_qwen2514b.csv
sd_toggle/configs/sweep_a100_tp1_qwen257b.csv
sd_toggle/constants.py
sd_toggle/fit.py
sd_toggle/plot.py
sd_toggle/predict.py
sd_toggle/roofline.py
sd_toggle/sweep.py
setup.py
tests/__init__.py
tests/test_sd_toggle_on_cpu.py
tests/utils/test_phase0_modules_on_cpu.py
third_party/vllm/CMakeLists.txt
third_party/vllm/LICENSE
third_party/vllm/MANIFEST.in
third_party/vllm/README.md
third_party/vllm/cmake/cpu_extension.cmake
third_party/vllm/cmake/external_projects/flashmla.cmake
third_party/vllm/cmake/external_projects/qutlass.cmake
third_party/vllm/cmake/external_projects/vllm_flash_attn.cmake
third_party/vllm/cmake/hipify.py
third_party/vllm/cmake/utils.cmake
third_party/vllm/csrc/activation_kernels.cu
third_party/vllm/csrc/attention/attention_dtypes.h
third_party/vllm/csrc/attention/attention_generic.cuh
third_party/vllm/csrc/attention/attention_kernels.cuh
third_party/vllm/csrc/attention/attention_utils.cuh
third_party/vllm/csrc/attention/dtype_bfloat16.cuh
third_party/vllm/csrc/attention/dtype_float16.cuh
third_party/vllm/csrc/attention/dtype_float32.cuh
third_party/vllm/csrc/attention/dtype_fp8.cuh
third_party/vllm/csrc/attention/merge_attn_states.cu
third_party/vllm/csrc/attention/mla/cutlass_sm100_mla/device/sm100_mla.hpp
third_party/vllm/csrc/attention/mla/cutlass_sm100_mla/kernel/sm100_fmha_mla_reduction.hpp
third_party/vllm/csrc/attention/mla/cutlass_sm100_mla/kernel/sm100_fmha_mla_tma_warpspecialized.hpp
third_party/vllm/csrc/attention/mla/cutlass_sm100_mla/kernel/sm100_mla_tile_scheduler.hpp
third_party/vllm/csrc/attention/mla/sm100_cutlass_mla_kernel.cu
third_party/vllm/csrc/attention/paged_attention_v1.cu
third_party/vllm/csrc/attention/paged_attention_v2.cu
third_party/vllm/csrc/attention/vertical_slash_index.cu
third_party/vllm/csrc/cache.h
third_party/vllm/csrc/cache_kernels.cu
third_party/vllm/csrc/core/batch_invariant.hpp
third_party/vllm/csrc/core/exception.hpp
third_party/vllm/csrc/core/math.hpp
third_party/vllm/csrc/core/registration.h
third_party/vllm/csrc/core/scalar_type.hpp
third_party/vllm/csrc/cpu/activation.cpp
third_party/vllm/csrc/cpu/cpu_attn.cpp
third_party/vllm/csrc/cpu/cpu_attn_amx.hpp
third_party/vllm/csrc/cpu/cpu_attn_impl.hpp
third_party/vllm/csrc/cpu/cpu_attn_macros.h
third_party/vllm/csrc/cpu/cpu_attn_vec.hpp
third_party/vllm/csrc/cpu/cpu_attn_vec16.hpp
third_party/vllm/csrc/cpu/cpu_types.hpp
third_party/vllm/csrc/cpu/cpu_types_arm.hpp
third_party/vllm/csrc/cpu/cpu_types_scalar.hpp
third_party/vllm/csrc/cpu/cpu_types_vsx.hpp
third_party/vllm/csrc/cpu/cpu_types_vxe.hpp
third_party/vllm/csrc/cpu/cpu_types_x86.hpp
third_party/vllm/csrc/cpu/dnnl_helper.cpp
third_party/vllm/csrc/cpu/dnnl_helper.h
third_party/vllm/csrc/cpu/dnnl_kernels.cpp
third_party/vllm/csrc/cpu/float_convert.hpp
third_party/vllm/csrc/cpu/layernorm.cpp
third_party/vllm/csrc/cpu/mla_decode.cpp
third_party/vllm/csrc/cpu/pos_encoding.cpp
third_party/vllm/csrc/cpu/scratchpad_manager.cpp
third_party/vllm/csrc/cpu/scratchpad_manager.h
third_party/vllm/csrc/cpu/sgl-kernels/common.h
third_party/vllm/csrc/cpu/sgl-kernels/gemm.cpp
third_party/vllm/csrc/cpu/sgl-kernels/gemm.h
third_party/vllm/csrc/cpu/sgl-kernels/gemm_fp8.cpp
third_party/vllm/csrc/cpu/sgl-kernels/gemm_int8.cpp
third_party/vllm/csrc/cpu/sgl-kernels/moe.cpp
third_party/vllm/csrc/cpu/sgl-kernels/moe_fp8.cpp
third_party/vllm/csrc/cpu/sgl-kernels/moe_int8.cpp
third_party/vllm/csrc/cpu/sgl-kernels/vec.h
third_party/vllm/csrc/cpu/shm.cpp
third_party/vllm/csrc/cpu/torch_bindings.cpp
third_party/vllm/csrc/cpu/utils.cpp
third_party/vllm/csrc/cub_helpers.h
third_party/vllm/csrc/cuda_compat.h
third_party/vllm/csrc/cuda_utils.h
third_party/vllm/csrc/cuda_utils_kernels.cu
third_party/vllm/csrc/cuda_view.cu
third_party/vllm/csrc/cumem_allocator.cpp
third_party/vllm/csrc/cumem_allocator_compat.h
third_party/vllm/csrc/custom_all_reduce.cu
third_party/vllm/csrc/custom_all_reduce.cuh
third_party/vllm/csrc/custom_all_reduce_test.cu
third_party/vllm/csrc/custom_quickreduce.cu
third_party/vllm/csrc/cutlass_extensions/common.cpp
third_party/vllm/csrc/cutlass_extensions/common.hpp
third_party/vllm/csrc/cutlass_extensions/cute_utils.cuh
third_party/vllm/csrc/cutlass_extensions/epilogue/broadcast_load_epilogue_array_c3x.hpp
third_party/vllm/csrc/cutlass_extensions/epilogue/broadcast_load_epilogue_c2x.hpp
third_party/vllm/csrc/cutlass_extensions/epilogue/broadcast_load_epilogue_c3x.hpp
third_party/vllm/csrc/cutlass_extensions/epilogue/scaled_mm_epilogues_c2x.hpp
third_party/vllm/csrc/cutlass_extensions/epilogue/scaled_mm_epilogues_c3x.hpp
third_party/vllm/csrc/cutlass_extensions/torch_utils.hpp
third_party/vllm/csrc/cutlass_extensions/vllm_collective_builder.cuh
third_party/vllm/csrc/cutlass_extensions/vllm_custom_types.cuh
third_party/vllm/csrc/cutlass_extensions/vllm_cutlass_library_extension.py
third_party/vllm/csrc/cutlass_extensions/vllm_numeric_conversion.cuh
third_party/vllm/csrc/cutlass_extensions/vllm_type_utils.cuh
third_party/vllm/csrc/dispatch_utils.h
third_party/vllm/csrc/fused_qknorm_rope_kernel.cu
third_party/vllm/csrc/launch_bounds_utils.h
third_party/vllm/csrc/layernorm_kernels.cu
third_party/vllm/csrc/layernorm_quant_kernels.cu
third_party/vllm/csrc/mamba/mamba_ssm/selective_scan.h
third_party/vllm/csrc/mamba/mamba_ssm/selective_scan_fwd.cu
third_party/vllm/csrc/mamba/mamba_ssm/static_switch.h
third_party/vllm/csrc/moe/dynamic_4bit_int_moe_cpu.cpp
third_party/vllm/csrc/moe/grouped_topk_kernels.cu
third_party/vllm/csrc/moe/marlin_moe_wna16/.gitignore
third_party/vllm/csrc/moe/marlin_moe_wna16/generate_kernels.py
third_party/vllm/csrc/moe/marlin_moe_wna16/kernel.h
third_party/vllm/csrc/moe/marlin_moe_wna16/marlin_template.h
third_party/vllm/csrc/moe/marlin_moe_wna16/ops.cu
third_party/vllm/csrc/moe/moe_align_sum_kernels.cu
third_party/vllm/csrc/moe/moe_lora_align_sum_kernels.cu
third_party/vllm/csrc/moe/moe_ops.h
third_party/vllm/csrc/moe/moe_permute_unpermute_op.cu
third_party/vllm/csrc/moe/moe_wna16.cu
third_party/vllm/csrc/moe/moe_wna16_utils.h
third_party/vllm/csrc/moe/permute_unpermute_kernels/dispatch.h
third_party/vllm/csrc/moe/permute_unpermute_kernels/moe_permute_unpermute_kernel.cu
third_party/vllm/csrc/moe/permute_unpermute_kernels/moe_permute_unpermute_kernel.h
third_party/vllm/csrc/moe/permute_unpermute_kernels/moe_permute_unpermute_kernel.inl
third_party/vllm/csrc/moe/topk_softmax_kernels.cu
third_party/vllm/csrc/moe/torch_bindings.cpp
third_party/vllm/csrc/ops.h
third_party/vllm/csrc/permute_cols.cu
third_party/vllm/csrc/pos_encoding_kernels.cu
third_party/vllm/csrc/quantization/activation_kernels.cu
third_party/vllm/csrc/quantization/awq/dequantize.cuh
third_party/vllm/csrc/quantization/awq/gemm_kernels.cu
third_party/vllm/csrc/quantization/cutlass_w4a8/w4a8_mm_entry.cu
third_party/vllm/csrc/quantization/fp4/activation_nvfp4_quant_fusion_kernels.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_blockwise_moe_kernel.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_experts_quant.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_quant_entry.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_quant_kernels.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_scaled_mm_entry.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_scaled_mm_kernels.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_scaled_mm_sm120_kernels.cu
third_party/vllm/csrc/quantization/fp4/nvfp4_utils.cuh
third_party/vllm/csrc/quantization/fused_kernels/fused_layernorm_dynamic_per_token_quant.cu
third_party/vllm/csrc/quantization/fused_kernels/layernorm_utils.cuh
third_party/vllm/csrc/quantization/fused_kernels/quant_conversions.cuh
third_party/vllm/csrc/quantization/gguf/dequantize.cuh
third_party/vllm/csrc/quantization/gguf/ggml-common.h
third_party/vllm/csrc/quantization/gguf/gguf_kernel.cu
third_party/vllm/csrc/quantization/gguf/mmq.cuh
third_party/vllm/csrc/quantization/gguf/mmvq.cuh
third_party/vllm/csrc/quantization/gguf/moe.cuh
third_party/vllm/csrc/quantization/gguf/moe_vec.cuh
third_party/vllm/csrc/quantization/gguf/vecdotq.cuh
… (truncated)
```

## Detected entry points

- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/third_party/vllm/vllm/entrypoints/cli/main.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/third_party/vllm/vllm/entrypoints/cli/benchmark/main.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/predict.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/scripts/convert_data_for_model.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/scripts/prepare_simplerl_zoo.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/scripts/quantize_utils.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/cli.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/config.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/constants.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/fit.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/plot.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/roofline.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/sd_toggle/sweep.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/tests/test_sd_toggle_on_cpu.py`
- `projects/PROJ-738-efficientrollout-system-aware-self-specu/external/EfficientRollout/verl/base_config.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `EfficientRollout` — not re-implementing it.

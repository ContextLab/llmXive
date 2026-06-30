# Reproduce & validate: LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/   (clone of https://github.com/NVlabs/LongLive)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation

**Abstract:** We present LongLive-2.0, an NVFP4-based parallel infrastructure throughout the full training and inference workflow of long video generation, addressing speed and memory bottlenecks. For training, we introduce sequence-parallel autoregressive (AR) training, instantiated as Balanced SP, which co-designs the efficient teacher-forcing layout with SP execution by pairing clean-history and noisy-target temporal chunks on each rank, enabling a natural teacher-forcing mask with SP-aware chunked VAE encoding. Combined with NVFP4 precision, it reduces GPU memory cost and accelerates GEMM computation during training, the proportion of which increases as video length grows. Moreover, we show that a high-quality infrastructure and dataset enable a remarkably clean training pipeline. Unlike existing Self-Forcing series methods that rely on ODE initialization and subsequent distribution matching distillation (DMD), LongLive-2.0 directly tunes a diffusion model into a long, multi-shot, interactive auto-regressive (AR) diffusion model. It can be further converted to real-time generation (4 to 2 denoising steps) with standalone LoRA weights. For inference on Blackwell GPUs, we enable W4A4 NVFP4 inference, quantize KV cache into NVFP4 for memory savings, and boost end-to-end throughput with asynchronous streaming VAE decoding. On non-Blackwell GPU architectures, we deploy SP inference to match the speed on Blackwell GPUs, while the quantized KV cache can lower inter-GPU communication of SP. Experiments show up to 2.15x speedup in training, and 1.84x in inference. LongLive-2.0-5B achieves 45.7 FPS inference while attaining strong performance on benchmarks. To our knowledge, LongLive-2.0 is the first NVFP4 training and inference system for long video generation.

## Shipped code — file tree (`projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/`)

```
.gitignore
CONTRIBUTING.md
LICENSE
README.md
assets/longlive2/LongLive1_teaser.png
assets/longlive2/fig_framework_overview.png
assets/longlive2/first-video-frame.png
assets/longlive2/logo.png
assets/longlive2/teaser.jpg
configs/inference.yaml
configs/inference_sp.yaml
configs/nvfp4/inference_i2v_nvfp4.yaml
configs/nvfp4/inference_nvfp4.yaml
configs/nvfp4/train_ar_nvfp4.yaml
configs/nvfp4/train_dmd_nvfp4_step4.yaml
configs/nvfp4/train_i2v_ar_nvfp4.yaml
configs/nvfp4/train_i2v_dmd_nvfp4_step4.yaml
configs/train_ar.yaml
configs/train_dmd.yaml
configs/train_i2v_ar.yaml
configs/train_i2v_dmd.yaml
docs/FLASH_ATTENTION_3_AND_HOPPER_SUPPORT.md
docs/getting_started.md
example/long_example.txt
fouroversix/.github/workflows/_build.yml
fouroversix/.github/workflows/build.yml
fouroversix/.github/workflows/pre-commit.yml
fouroversix/.github/workflows/publish.yml
fouroversix/.gitignore
fouroversix/.gitmodules
fouroversix/LICENSE.md
fouroversix/MANIFEST.in
fouroversix/README.md
fouroversix/docs/index.md
fouroversix/docs/matmul.md
fouroversix/docs/ptq.md
fouroversix/docs/quantization.md
fouroversix/mkdocs.yml
fouroversix/pyproject.toml
fouroversix/scripts/__init__.py
fouroversix/scripts/create_test_case.py
fouroversix/scripts/generate_kernels.py
fouroversix/scripts/hadamard_code_gen.py
fouroversix/scripts/ptq/__init__.py
fouroversix/scripts/ptq/__main__.py
fouroversix/scripts/ptq/coordinators/__init__.py
fouroversix/scripts/ptq/coordinators/base.py
fouroversix/scripts/ptq/coordinators/local.py
fouroversix/scripts/ptq/coordinators/modal.py
fouroversix/scripts/ptq/evaluators/__init__.py
fouroversix/scripts/ptq/evaluators/awq.py
fouroversix/scripts/ptq/evaluators/evaluator.py
fouroversix/scripts/ptq/evaluators/gptq.py
fouroversix/scripts/ptq/evaluators/high_precision.py
fouroversix/scripts/ptq/evaluators/rtn.py
fouroversix/scripts/ptq/evaluators/smoothquant.py
fouroversix/scripts/ptq/evaluators/spinquant.py
fouroversix/scripts/ptq/evaluators/utils.py
fouroversix/scripts/ptq/experiment.py
fouroversix/scripts/ptq/tasks/__init__.py
fouroversix/scripts/ptq/tasks/wikitext_train/preprocess_wikitext.py
fouroversix/scripts/ptq/tasks/wikitext_train/wikitext_train.yaml
fouroversix/scripts/ptq/utils.py
fouroversix/scripts/resources.py
fouroversix/scripts/speedtest/__init__.py
fouroversix/scripts/speedtest/matmul.py
fouroversix/scripts/speedtest/quantize.py
fouroversix/scripts/test_on_modal.py
fouroversix/scripts/train/__init__.py
fouroversix/scripts/train/__main__.py
fouroversix/scripts/train/configs/transformer_1B_bf16.json
fouroversix/scripts/train/configs/transformer_1B_fp4.json
fouroversix/scripts/train/configs/transformer_1B_fp4_fouroversix.json
fouroversix/scripts/train/configs/transformer_340M_bf16.json
fouroversix/scripts/train/configs/transformer_340M_fp4.json
fouroversix/scripts/train/configs/transformer_340M_fp4_fouroversix.json
fouroversix/scripts/train/prepare_dataset.py
fouroversix/setup.py
fouroversix/src/fouroversix/__init__.py
fouroversix/src/fouroversix/csrc/bindings.cpp
fouroversix/src/fouroversix/csrc/fp4_gemm.cu
fouroversix/src/fouroversix/csrc/fp4_gemm_sm120.cu
fouroversix/src/fouroversix/csrc/include/element_traits.hpp
fouroversix/src/fouroversix/csrc/include/fp4_quant.h
fouroversix/src/fouroversix/csrc/include/fp4_quant_kernel.h
fouroversix/src/fouroversix/csrc/include/fp4_quant_launch_template.h
fouroversix/src/fouroversix/csrc/include/hadamard_transform.h
fouroversix/src/fouroversix/csrc/include/hardware_info.h
fouroversix/src/fouroversix/csrc/include/kernel_traits.h
fouroversix/src/fouroversix/csrc/include/static_switch.h
fouroversix/src/fouroversix/csrc/include/utils.h
fouroversix/src/fouroversix/csrc/quantize/fp4_quant.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_mxfp4_rht_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_mxfp4_rht_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_mxfp4_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_mxfp4_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_nvfp4_rht_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_nvfp4_rht_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_nvfp4_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_bf16_nvfp4_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_mxfp4_rht_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_mxfp4_rht_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_mxfp4_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_mxfp4_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_nvfp4_rht_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_nvfp4_rht_trans_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_nvfp4_sm100.cu
fouroversix/src/fouroversix/csrc/quantize/fp4_quant_fp16_nvfp4_trans_sm100.cu
fouroversix/src/fouroversix/matmul/__init__.py
fouroversix/src/fouroversix/matmul/backend.py
fouroversix/src/fouroversix/matmul/cutlass/__init__.py
fouroversix/src/fouroversix/matmul/cutlass/backend.py
fouroversix/src/fouroversix/matmul/cutlass/ops.py
fouroversix/src/fouroversix/matmul/frontend.py
fouroversix/src/fouroversix/matmul/pytorch.py
fouroversix/src/fouroversix/model/__init__.py
fouroversix/src/fouroversix/model/config.py
fouroversix/src/fouroversix/model/modules/__init__.py
fouroversix/src/fouroversix/model/modules/gpt_oss.py
fouroversix/src/fouroversix/model/modules/linear.py
fouroversix/src/fouroversix/model/modules/linear_ori.py
fouroversix/src/fouroversix/model/modules/qwen.py
fouroversix/src/fouroversix/model/quantize.py
fouroversix/src/fouroversix/quantize/__init__.py
fouroversix/src/fouroversix/quantize/backend.py
fouroversix/src/fouroversix/quantize/config.py
fouroversix/src/fouroversix/quantize/cuda/__init__.py
fouroversix/src/fouroversix/quantize/cuda/backend.py
fouroversix/src/fouroversix/quantize/cuda/ops.py
fouroversix/src/fouroversix/quantize/frontend.py
fouroversix/src/fouroversix/quantize/pytorch/__init__.py
fouroversix/src/fouroversix/quantize/pytorch/backend.py
fouroversix/src/fouroversix/quantize/pytorch/reference.py
fouroversix/src/fouroversix/quantize/quantized_tensor.py
fouroversix/src/fouroversix/quantize/transformer_engine.py
fouroversix/src/fouroversix/quantize/triton/__init__.py
fouroversix/src/fouroversix/quantize/triton/backend.py
fouroversix/src/fouroversix/quantize/triton/kernel.py
fouroversix/src/fouroversix/quantize/utils.py
fouroversix/src/fouroversix/utils.py
fouroversix/src/fouroversix/weight_conversions/__init__.py
fouroversix/src/fouroversix/weight_conversions/conversions.py
fouroversix/src/fouroversix/weight_conversions/gpt_oss.py
fouroversix/tests/__init__.py
fouroversix/tests/test_correctness.py
inference.py
inference_sp.py
model/__init__.py
model/base.py
model/diffusion.py
model/dmd.py
pipeline/__init__.py
pipeline/causal_diffusion_inference.py
pipeline/causal_diffusion_inference_sp.py
pipeline/self_forcing_training.py
requirements.txt
scripts/compute_sp_vae_chunk_halo.py
scripts/decode_lightvae_latents.py
scripts/decode_vae_latents.py
scripts/merge_lora_generator.py
scripts/save_merged_nvfp4_generator.py
tests/test_dmd_i2v_conditioning.py
tests/test_i2v_dataset_frame_accounting.py
tests/test_i2v_sequence_parallel_config.py
tests/test_i2v_teacher_forcing_context.py
train.py
trainer/__init__.py
trainer/diffusion.py
trainer/distillation.py
trainer/sp_helper.py
utils/DATASET_PROMPT_LOGIC.md
utils/__init__.py
utils/adaln_triton.py
utils/config.py
utils/dataset.py
utils/distributed.py
utils/error_buffer.py
utils/i2v_conditioning.py
utils/inference_utils.py
utils/kernel/README.md
utils/kernel/__init__.py
utils/kernel/kv_dequant.cpp
utils/kernel/kv_dequant.py
utils/kernel/kv_dequant_cuda.cu
utils/kernel/setup.py
utils/lightvae_5b_wrapper.py
utils/lora_utils.py
utils/loss.py
utils/memory.py
utils/misc.py
utils/nvfp4_checkpoint.py
utils/nvfp4_kernel.py
utils/position_embedding_utils.py
utils/quant.py
utils/rope_triton.py
utils/scheduler.py
utils/torch_compile_utils.py
utils/wan_5b_wrapper.py
wan_5b/__init__.py
wan_5b/configs/__init__.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/train.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/inference.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/inference_sp.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/model/base.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/model/diffusion.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/model/dmd.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/pipeline/causal_diffusion_inference.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/pipeline/causal_diffusion_inference_sp.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/pipeline/self_forcing_training.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/scripts/compute_sp_vae_chunk_halo.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/scripts/decode_lightvae_latents.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/scripts/decode_vae_latents.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/scripts/merge_lora_generator.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/scripts/save_merged_nvfp4_generator.py`
- `projects/PROJ-604-https-arxiv-org-abs-2605-18739/external/LongLive/tests/test_dmd_i2v_conditioning.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `LongLive` — not re-implementing it.

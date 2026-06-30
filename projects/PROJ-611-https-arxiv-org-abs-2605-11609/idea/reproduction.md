# Reproduce & validate: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/   (clone of https://github.com/FloyedShen/AntiSD)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

**Abstract:** On-policy self-distillation, where a student is pulled toward a copy of itself conditioned on privileged context (e.g., a verified solution or feedback), offers a promising direction for advancing reasoning capability without a stronger external teacher. Yet in math reasoning the gains are inconsistent, even when the same approach succeeds elsewhere. A pointwise mutual information analysis traces the failure to the privileged context itself: it inflates the teacher's confidence on tokens already implied by the solution (structural connectives, verifiable claims) and deflates it on deliberation tokens ("Wait", "Let", "Maybe") that drive multi-step search. We propose Anti-Self-Distillation (AntiSD), which ascends a divergence between student and teacher rather than descending it: this reverses the per-token sign and yields a naturally bounded advantage in one step. An entropy-triggered gate disables the term once the teacher entropy collapses, completing a drop-in replacement for default self-distillation. Across five models from 4B to 30B parameters on math reasoning benchmarks, AntiSD reaches the GRPO baseline's accuracy in 2 to 10x fewer training steps and improves final accuracy by up to 11.5 points. AntiSD opens a path to scalable self-improvement, where a language model bootstraps its own reasoning through its training signal.

## Shipped code — file tree (`projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/`)

```
.gitignore
Dockerfile
INSTALL.md
LICENSE
NOTICE
README.md
data/prepare_antisd.sh
data/prepare_dapomath.sh
data/prepare_deepmath.sh
data/prepare_math.sh
data/preprocess_math_datasets.py
docker/README.md
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.app.sglang.mcore0.12
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.app.sglang.mcore0.13.preview
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.base
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/README.md
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.app.sglang
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.base
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.vllm011.mcore_gpt-oss
examples/data_preprocess/aime2024_multiturn_w_tool.py
examples/data_preprocess/dapo_multiturn_w_tool.py
examples/data_preprocess/full_hh_rlhf.py
examples/data_preprocess/geo3k.py
examples/data_preprocess/geo3k_multiturn_w_tool.py
examples/data_preprocess/gsm8k.py
examples/data_preprocess/gsm8k_multiturn_sft.py
examples/data_preprocess/gsm8k_multiturn_w_interaction.py
examples/data_preprocess/gsm8k_multiturn_w_tool.py
examples/data_preprocess/gsm8k_tool_agent_loop.py
examples/data_preprocess/hellaswag.py
examples/data_preprocess/math_dataset.py
examples/data_preprocess/multiturn.py
examples/data_preprocess/pokemon.py
examples/data_preprocess/preprocess_search_r1_dataset.py
figures/fig1a_overview.png
figures/fig1b_qn_hmmt25.png
figures/fig2a_trace_main_pid24_y20.png
figures/fig2b_heatmap.png
figures/fig_pass_k_hmmt.png
figures/fig_train_dynamics.png
pyproject.toml
recipe/antisd/README.md
recipe/antisd/_launchers/launch_long.sh
recipe/antisd/_launchers/launch_short.sh
recipe/antisd/run/olmo3-instruct/antisd.sh
recipe/antisd/run/olmo3-instruct/grpo.sh
recipe/antisd/run/olmo3-instruct/sd.sh
recipe/antisd/run/olmo3-think/antisd.sh
recipe/antisd/run/olmo3-think/grpo.sh
recipe/antisd/run/olmo3-think/sd.sh
recipe/antisd/run/qwen3-4b/antisd.sh
recipe/antisd/run/qwen3-4b/grpo.sh
recipe/antisd/run/qwen3-4b/sd.sh
recipe/antisd/run/qwen3-8b/antisd.sh
recipe/antisd/run/qwen3-8b/grpo.sh
recipe/antisd/run/qwen3-8b/sd.sh
requirements-cuda.txt
requirements.txt
scripts/__init__.py
scripts/converter_hf_to_mcore.py
scripts/diagnose.py
scripts/generate_trainer_config.sh
scripts/init_random_model.py
scripts/install_vllm_sglang_mcore.sh
scripts/megatron_merge_lora.py
scripts/print_cfg.py
scripts/rollout_viewer.py
setup.py
verl/__init__.py
verl/base_config.py
verl/checkpoint_engine/README.md
verl/checkpoint_engine/__init__.py
verl/checkpoint_engine/base.py
verl/checkpoint_engine/nccl_checkpoint_engine.py
verl/checkpoint_engine/nixl_checkpoint_engine.py
verl/experimental/__init__.py
verl/experimental/agent_loop/__init__.py
verl/experimental/agent_loop/agent_loop.py
verl/experimental/agent_loop/prometheus_utils.py
verl/experimental/agent_loop/single_turn_agent_loop.py
verl/experimental/agent_loop/tool_agent_loop.py
verl/experimental/agent_loop/tool_parser.py
verl/experimental/agent_loop/utils.py
verl/experimental/dataset/__init__.py
verl/experimental/dataset/sampler.py
verl/experimental/reward_loop/__init__.py
verl/experimental/reward_loop/reward_loop.py
verl/experimental/reward_loop/reward_manager/__init__.py
verl/experimental/reward_loop/reward_manager/base.py
verl/experimental/reward_loop/reward_manager/dapo.py
verl/experimental/reward_loop/reward_manager/limited.py
verl/experimental/reward_loop/reward_manager/naive.py
verl/experimental/reward_loop/reward_manager/registry.py
verl/experimental/reward_loop/reward_manager/remote.py
verl/experimental/reward_loop/reward_model.py
verl/experimental/reward_loop/router/inner_sglang_router.py
verl/experimental/reward_loop/router/naive_router.py
verl/interactions/__init__.py
verl/interactions/base.py
verl/interactions/gsm8k_interaction.py
verl/interactions/utils/__init__.py
verl/interactions/utils/interaction_registry.py
verl/interactions/weather_interaction.py
verl/model_merger/__init__.py
verl/model_merger/__main__.py
verl/model_merger/base_model_merger.py
verl/model_merger/fsdp_model_merger.py
verl/model_merger/megatron_model_merger.py
verl/models/README.md
verl/models/__init__.py
verl/models/llama/__init__.py
verl/models/llama/megatron/__init__.py
verl/models/llama/megatron/checkpoint_utils/__init__.py
verl/models/llama/megatron/checkpoint_utils/llama_loader.py
verl/models/llama/megatron/checkpoint_utils/llama_loader_depracated.py
verl/models/llama/megatron/checkpoint_utils/llama_saver.py
verl/models/llama/megatron/layers/__init__.py
verl/models/llama/megatron/layers/parallel_attention.py
verl/models/llama/megatron/layers/parallel_decoder.py
verl/models/llama/megatron/layers/parallel_linear.py
verl/models/llama/megatron/layers/parallel_mlp.py
verl/models/llama/megatron/layers/parallel_rmsnorm.py
verl/models/llama/megatron/modeling_llama_megatron.py
verl/models/mcore/__init__.py
verl/models/mcore/bridge.py
verl/models/mcore/config_converter.py
verl/models/mcore/loader.py
verl/models/mcore/mbridge.py
verl/models/mcore/model_forward.py
verl/models/mcore/model_forward_1f1b_overlap.py
verl/models/mcore/model_forward_fused.py
verl/models/mcore/model_initializer.py
verl/models/mcore/patch_v012.py
verl/models/mcore/qwen2_5_vl/__init__.py
verl/models/mcore/qwen2_5_vl/attention.py
verl/models/mcore/qwen2_5_vl/model.py
verl/models/mcore/qwen2_5_vl/rope_utils.py
verl/models/mcore/qwen2_5_vl/vision_config.py
verl/models/mcore/qwen2_5_vl/vision_model.py
verl/models/mcore/qwen2_5_vl/vision_transformer_block.py
verl/models/mcore/readme.md
verl/models/mcore/registry.py
verl/models/mcore/saver.py
verl/models/mcore/util.py
verl/models/mcore/weight_converter.py
verl/models/qwen2/__init__.py
verl/models/qwen2/megatron/__init__.py
verl/models/qwen2/megatron/checkpoint_utils/__init__.py
verl/models/qwen2/megatron/checkpoint_utils/qwen2_loader.py
verl/models/qwen2/megatron/checkpoint_utils/qwen2_loader_depracated.py
verl/models/qwen2/megatron/checkpoint_utils/qwen2_saver.py
verl/models/qwen2/megatron/layers/__init__.py
verl/models/qwen2/megatron/layers/parallel_attention.py
verl/models/qwen2/megatron/layers/parallel_decoder.py
verl/models/qwen2/megatron/layers/parallel_linear.py
verl/models/qwen2/megatron/layers/parallel_mlp.py
verl/models/qwen2/megatron/layers/parallel_rmsnorm.py
verl/models/qwen2/megatron/modeling_qwen2_megatron.py
verl/models/registry.py
verl/models/transformers/__init__.py
verl/models/transformers/apertus.py
verl/models/transformers/dense_common.py
verl/models/transformers/glm4v.py
verl/models/transformers/kimi_vl.py
verl/models/transformers/llama.py
verl/models/transformers/monkey_patch.py
verl/models/transformers/npu_patch.py
verl/models/transformers/qwen2.py
verl/models/transformers/qwen2_vl.py
verl/models/transformers/qwen3_vl.py
verl/models/transformers/tiled_mlp.py
verl/models/weight_loader_registry.py
verl/protocol.py
verl/py.typed
verl/single_controller/__init__.py
verl/single_controller/base/__init__.py
verl/single_controller/base/decorator.py
verl/single_controller/base/worker.py
verl/single_controller/base/worker_group.py
verl/single_controller/ray/__init__.py
verl/single_controller/ray/base.py
verl/third_party/__init__.py
verl/third_party/torch/__init__.py
verl/third_party/torch/distributed/__init__.py
verl/third_party/torch/distributed/_state_dict_utils.py
verl/third_party/torch/distributed/checkpoint/__init__.py
verl/third_party/torch/distributed/checkpoint/state_dict.py
verl/third_party/vllm/__init__.py
verl/tools/__init__.py
verl/tools/base_tool.py
verl/tools/geo3k_tool.py
verl/tools/gsm8k_tool.py
verl/tools/image_zoom_in_tool.py
verl/tools/mcp_base_tool.py
verl/tools/mcp_search_tool.py
verl/tools/sandbox_fusion_tools.py
verl/tools/schemas.py
verl/tools/search_tool.py
verl/tools/utils/__init__.py
verl/tools/utils/mcp_clients/McpClientManager.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/data/preprocess_math_datasets.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/converter_hf_to_mcore.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/diagnose.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/init_random_model.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/megatron_merge_lora.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/print_cfg.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/scripts/rollout_viewer.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/verl/base_config.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/verl/protocol.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/aime2024_multiturn_w_tool.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/dapo_multiturn_w_tool.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/full_hh_rlhf.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/geo3k.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/geo3k_multiturn_w_tool.py`
- `projects/PROJ-611-https-arxiv-org-abs-2605-11609/external/AntiSD/examples/data_preprocess/gsm8k.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `AntiSD` — not re-implementing it.

# Reproduce & validate: VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/   (clone of https://github.com/Fu-Fu-Fu-Fu/VideoKR)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding

**Abstract:** We introduce VideoKR, the first large-scale training corpus specifically designed to strengthen knowledge- and reasoning-intensive video understanding. It comprises 315K video reasoning examples over 145K newly collected, CC-licensed, expert-domain videos. We develop a human-in-the-loop, skill-oriented example generation pipeline that targets progressively deeper video reasoning capabilities while ensuring the difficulty, diversity, and reliability of both the examples and their CoT rationales. We also curate VideoKR-Eval, a new expert-annotated benchmark where questions require genuine video understanding and knowledge-intensive reasoning rather than textual shortcuts. Our experiments show that, under a standard SFT$\rightarrow$GRPO pipeline, models post-trained on VideoKR outperform prior post-training approaches on knowledge-intensive video reasoning while remaining competitive on general video reasoning, highlighting data design as a key driver of progress in video reasoning. We further conduct comprehensive ablations to isolate the contributions of VideoKR, providing actionable insights for future work.

## Shipped code — file tree (`projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/`)

```
.gitignore
README.md
assets/overview.png
llamafactory/.gitattributes
llamafactory/.gitignore
llamafactory/LICENSE
llamafactory/README.md
llamafactory/data/dataset_info.json
llamafactory/examples/deepspeed/ds_z3_config.json
llamafactory/examples/train_full/videokr_qwen2_5vl_sft.yaml
llamafactory/examples/train_full/videokr_qwen3vl_sft.yaml
llamafactory/local_script/prepare_videokr_sft_data.py
llamafactory/local_script/train_videokr.sh
llamafactory/pyproject.toml
llamafactory/requirements/adam-mini.txt
llamafactory/requirements/apollo.txt
llamafactory/requirements/aqlm.txt
llamafactory/requirements/badam.txt
llamafactory/requirements/bitsandbytes.txt
llamafactory/requirements/deepspeed.txt
llamafactory/requirements/dev.txt
llamafactory/requirements/eetq.txt
llamafactory/requirements/fp8-te.txt
llamafactory/requirements/fp8.txt
llamafactory/requirements/galore.txt
llamafactory/requirements/gptq.txt
llamafactory/requirements/hqq.txt
llamafactory/requirements/liger-kernel.txt
llamafactory/requirements/metrics.txt
llamafactory/requirements/minicpm-v.txt
llamafactory/requirements/npu.txt
llamafactory/requirements/openmind.txt
llamafactory/requirements/sglang.txt
llamafactory/requirements/swanlab.txt
llamafactory/requirements/vllm.txt
llamafactory/src/api.py
llamafactory/src/llamafactory/__init__.py
llamafactory/src/llamafactory/api/__init__.py
llamafactory/src/llamafactory/api/app.py
llamafactory/src/llamafactory/api/chat.py
llamafactory/src/llamafactory/api/common.py
llamafactory/src/llamafactory/api/protocol.py
llamafactory/src/llamafactory/chat/__init__.py
llamafactory/src/llamafactory/chat/base_engine.py
llamafactory/src/llamafactory/chat/chat_model.py
llamafactory/src/llamafactory/chat/hf_engine.py
llamafactory/src/llamafactory/chat/kt_engine.py
llamafactory/src/llamafactory/chat/sglang_engine.py
llamafactory/src/llamafactory/chat/vllm_engine.py
llamafactory/src/llamafactory/cli.py
llamafactory/src/llamafactory/data/__init__.py
llamafactory/src/llamafactory/data/collator.py
llamafactory/src/llamafactory/data/converter.py
llamafactory/src/llamafactory/data/data_utils.py
llamafactory/src/llamafactory/data/formatter.py
llamafactory/src/llamafactory/data/loader.py
llamafactory/src/llamafactory/data/mm_plugin.py
llamafactory/src/llamafactory/data/parser.py
llamafactory/src/llamafactory/data/processor/__init__.py
llamafactory/src/llamafactory/data/processor/feedback.py
llamafactory/src/llamafactory/data/processor/pairwise.py
llamafactory/src/llamafactory/data/processor/pretrain.py
llamafactory/src/llamafactory/data/processor/processor_utils.py
llamafactory/src/llamafactory/data/processor/supervised.py
llamafactory/src/llamafactory/data/processor/unsupervised.py
llamafactory/src/llamafactory/data/template.py
llamafactory/src/llamafactory/data/tool_utils.py
llamafactory/src/llamafactory/eval/__init__.py
llamafactory/src/llamafactory/eval/evaluator.py
llamafactory/src/llamafactory/eval/template.py
llamafactory/src/llamafactory/extras/__init__.py
llamafactory/src/llamafactory/extras/constants.py
llamafactory/src/llamafactory/extras/env.py
llamafactory/src/llamafactory/extras/logging.py
llamafactory/src/llamafactory/extras/misc.py
llamafactory/src/llamafactory/extras/packages.py
llamafactory/src/llamafactory/extras/ploting.py
llamafactory/src/llamafactory/hparams/__init__.py
llamafactory/src/llamafactory/hparams/data_args.py
llamafactory/src/llamafactory/hparams/evaluation_args.py
llamafactory/src/llamafactory/hparams/finetuning_args.py
llamafactory/src/llamafactory/hparams/generating_args.py
llamafactory/src/llamafactory/hparams/model_args.py
llamafactory/src/llamafactory/hparams/parser.py
llamafactory/src/llamafactory/hparams/training_args.py
llamafactory/src/llamafactory/launcher.py
llamafactory/src/llamafactory/model/__init__.py
llamafactory/src/llamafactory/model/adapter.py
llamafactory/src/llamafactory/model/loader.py
llamafactory/src/llamafactory/model/model_utils/__init__.py
llamafactory/src/llamafactory/model/model_utils/attention.py
llamafactory/src/llamafactory/model/model_utils/checkpointing.py
llamafactory/src/llamafactory/model/model_utils/embedding.py
llamafactory/src/llamafactory/model/model_utils/ktransformers.py
llamafactory/src/llamafactory/model/model_utils/kv_cache.py
llamafactory/src/llamafactory/model/model_utils/liger_kernel.py
llamafactory/src/llamafactory/model/model_utils/longlora.py
llamafactory/src/llamafactory/model/model_utils/misc.py
llamafactory/src/llamafactory/model/model_utils/mod.py
llamafactory/src/llamafactory/model/model_utils/moe.py
llamafactory/src/llamafactory/model/model_utils/packing.py
llamafactory/src/llamafactory/model/model_utils/quantization.py
llamafactory/src/llamafactory/model/model_utils/rope.py
llamafactory/src/llamafactory/model/model_utils/unsloth.py
llamafactory/src/llamafactory/model/model_utils/valuehead.py
llamafactory/src/llamafactory/model/model_utils/visual.py
llamafactory/src/llamafactory/model/patcher.py
llamafactory/src/llamafactory/third_party/__init__.py
llamafactory/src/llamafactory/third_party/muon/__init__.py
llamafactory/src/llamafactory/third_party/muon/muon.py
llamafactory/src/llamafactory/train/__init__.py
llamafactory/src/llamafactory/train/callbacks.py
llamafactory/src/llamafactory/train/dpo/__init__.py
llamafactory/src/llamafactory/train/dpo/ktrainer.py
llamafactory/src/llamafactory/train/dpo/trainer.py
llamafactory/src/llamafactory/train/dpo/workflow.py
llamafactory/src/llamafactory/train/fp8_utils.py
llamafactory/src/llamafactory/train/kto/__init__.py
llamafactory/src/llamafactory/train/kto/trainer.py
llamafactory/src/llamafactory/train/kto/workflow.py
llamafactory/src/llamafactory/train/mca/__init__.py
llamafactory/src/llamafactory/train/mca/trainer.py
llamafactory/src/llamafactory/train/mca/workflow.py
llamafactory/src/llamafactory/train/ppo/__init__.py
llamafactory/src/llamafactory/train/ppo/ppo_utils.py
llamafactory/src/llamafactory/train/ppo/trainer.py
llamafactory/src/llamafactory/train/ppo/workflow.py
llamafactory/src/llamafactory/train/pt/__init__.py
llamafactory/src/llamafactory/train/pt/trainer.py
llamafactory/src/llamafactory/train/pt/workflow.py
llamafactory/src/llamafactory/train/rm/__init__.py
llamafactory/src/llamafactory/train/rm/metric.py
llamafactory/src/llamafactory/train/rm/trainer.py
llamafactory/src/llamafactory/train/rm/workflow.py
llamafactory/src/llamafactory/train/sft/__init__.py
llamafactory/src/llamafactory/train/sft/metric.py
llamafactory/src/llamafactory/train/sft/trainer.py
llamafactory/src/llamafactory/train/sft/workflow.py
llamafactory/src/llamafactory/train/test_utils.py
llamafactory/src/llamafactory/train/trainer_utils.py
llamafactory/src/llamafactory/train/tuner.py
llamafactory/src/llamafactory/v1/__init__.py
llamafactory/src/llamafactory/v1/accelerator/__init__.py
llamafactory/src/llamafactory/v1/accelerator/helper.py
llamafactory/src/llamafactory/v1/accelerator/interface.py
llamafactory/src/llamafactory/v1/accelerator/profiler.py
llamafactory/src/llamafactory/v1/config/__init__.py
llamafactory/src/llamafactory/v1/config/arg_parser.py
llamafactory/src/llamafactory/v1/config/arg_utils.py
llamafactory/src/llamafactory/v1/config/data_args.py
llamafactory/src/llamafactory/v1/config/model_args.py
llamafactory/src/llamafactory/v1/config/sample_args.py
llamafactory/src/llamafactory/v1/config/training_args.py
llamafactory/src/llamafactory/v1/core/__init__.py
llamafactory/src/llamafactory/v1/core/base_sampler.py
llamafactory/src/llamafactory/v1/core/base_trainer.py
llamafactory/src/llamafactory/v1/core/data_engine.py
llamafactory/src/llamafactory/v1/core/model_engine.py
llamafactory/src/llamafactory/v1/core/utils/__init__.py
llamafactory/src/llamafactory/v1/core/utils/batching.py
llamafactory/src/llamafactory/v1/core/utils/callback.py
llamafactory/src/llamafactory/v1/core/utils/inference_engine.py
llamafactory/src/llamafactory/v1/core/utils/rendering.py
llamafactory/src/llamafactory/v1/launcher.py
llamafactory/src/llamafactory/v1/plugins/__init__.py
llamafactory/src/llamafactory/v1/plugins/data_plugins/__init__.py
llamafactory/src/llamafactory/v1/plugins/data_plugins/converter.py
llamafactory/src/llamafactory/v1/plugins/data_plugins/loader.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/add_token.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/initialization.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/base.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/interface.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/mlp/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/mlp/npu_fused_moe.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/mlp/npu_swiglu.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/rms_norm/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/rms_norm/npu_rms_norm.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/rope/__init__.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/ops/rope/npu_rope.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/kernels/registry.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/peft.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/quantization.py
llamafactory/src/llamafactory/v1/plugins/model_plugins/rendering.py
llamafactory/src/llamafactory/v1/plugins/sampler_plugins/__init__.py
llamafactory/src/llamafactory/v1/plugins/sampler_plugins/vllm.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/__init__.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/batching.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/distributed/__init__.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/distributed/deepspeed.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/distributed/fsdp2.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/distributed/hub.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/lr_scheduler.py
llamafactory/src/llamafactory/v1/plugins/trainer_plugins/optimizer.py
llamafactory/src/llamafactory/v1/samplers/cli_sampler.py
llamafactory/src/llamafactory/v1/trainers/__init__.py
llamafactory/src/llamafactory/v1/trainers/dpo_trainer.py
llamafactory/src/llamafactory/v1/trainers/rm_trainer.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/src/train.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/src/llamafactory/webui/components/train.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/src/llamafactory/webui/components/eval.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/local_script/prepare_videokr_sft_data.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/src/api.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/llamafactory/src/webui.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/lmms_eval/lmms_eval/evaluator.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/lmms_eval/lmms_eval/evaluator_utils.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/lmms_eval/lmms_eval/protocol.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/lmms_eval/lmms_eval/utils.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/verl/local_script/prepare_videokr_rl_data.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/verl/scripts/converter_hf_to_mcore.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/verl/scripts/diagnose.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/verl/scripts/init_random_model.py`
- `projects/PROJ-667-https-arxiv-org-abs-2606-05259/external/VideoKR/verl/scripts/legacy_model_merger.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `VideoKR` — not re-implementing it.

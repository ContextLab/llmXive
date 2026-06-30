# Reproduce & validate: AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/   (clone of https://github.com/NVLabs/AnyFlow)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation

**Abstract:** Few-step video generation has been significantly advanced by consistency distillation. However, the performance of consistency-distilled models often degrades as more sampling steps are allocated at test time, limiting their effectiveness for any-step video diffusion. This limitation arises because consistency distillation replaces the original probability-flow ODE trajectory with a consistency-sampling trajectory, weakening the desirable test-time scaling behavior of ODE sampling. To address this limitation, we introduce AnyFlow, the first any-step video diffusion distillation framework based on flow maps. Instead of distilling a model for only a few fixed sampling steps, AnyFlow optimizes the full ODE sampling trajectory. To this end, we shift the distillation target from endpoint consistency mapping $(z_{t}\rightarrow z_{0})$ to flow-map transition learning $(z_{t}\rightarrow z_{r})$ over arbitrary time intervals. We further propose Flow Map Backward Simulation, which decomposes a full Euler rollout into shortcut flow-map transitions, enabling efficient on-policy distillation that reduces test-time errors (i.e., discretization error in few-step sampling and exposure bias in causal generation). Extensive experiments across both bidirectional and causal architectures, at scales ranging from 1.3B to 14B parameters, demonstrate that AnyFlow achieves performance matches or surpasses consistency-based counterparts in the few-step regime, while scaling with sampling step budgets.

## Shipped code — file tree (`projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/`)

```
.gitignore
.pre-commit-config.yaml
LICENSE
README.md
SECURITY.md
assets/data/meta/vbench/VBench_aug_full_info.json
assets/data/meta/vbench/VBench_full_info.json
assets/data/meta/vbench/vbench2_i2v_aug_full_info.json
assets/data/meta/vbench/vbench2_i2v_full_info.json
assets/data/meta/vidprom_dummy/raw.json
assets/demo_video_first_frame.png
assets/evaluation/eval_caption_i2v.json
assets/evaluation/eval_caption_t2v.json
assets/evaluation/eval_caption_v2v.json
assets/evaluation/example/images/1.jpg
assets/evaluation/example/images/2.jpg
assets/evaluation/example/images/3.jpg
assets/evaluation/example/images/4.jpg
assets/evaluation/example/images/5.jpg
assets/evaluation/example/images/6.jpg
assets/evaluation/example/images/7.jpg
assets/evaluation/example/images/8.jpg
assets/evaluation/example/videos/1.mp4
assets/evaluation/example/videos/2.mp4
assets/evaluation/example/videos/3.mp4
assets/evaluation/example/videos/4.mp4
assets/evaluation/example/videos/5.mp4
assets/evaluation/example/videos/6.mp4
assets/evaluation/example/videos/7.mp4
assets/evaluation/example/videos/8.mp4
assets/negative_embedding/wan_negemb_cn.pth
assets/negative_embedding/wan_negemb_en.pth
demo.py
docs/DATA.md
far/data/__init__.py
far/data/dataloader.py
far/data/prompt_dataset.py
far/data/sampler.py
far/data/t2v_tar_dataset.py
far/data/vbench_i2v_dataset.py
far/data/vbench_t2v_dataset.py
far/data/web_dataset/__init__.py
far/data/web_dataset/generate_meta.py
far/data/web_dataset/wids.py
far/data/web_dataset/wids_dl.py
far/data/web_dataset/wids_lru.py
far/data/web_dataset/wids_mmtar.py
far/data/web_dataset/wids_specs.py
far/data/web_dataset/wids_tar.py
far/main.py
far/metrics/vbench.py
far/metrics/vbench_i2v.py
far/models/__init__.py
far/models/transformer_far_wan_model.py
far/models/transformer_wan_model.py
far/pipelines/__init__.py
far/pipelines/pipeline_far_wan_anyflow.py
far/pipelines/pipeline_wan_anyflow.py
far/schedulers/scheduling_flowmap_euler_discrete.py
far/trainers/__init__.py
far/trainers/convert_lora_into_base.py
far/trainers/trainer_far_wan_anyflow_onpolicy.py
far/trainers/trainer_far_wan_anyflow_pretrain.py
far/trainers/trainer_wan_anyflow_onpolicy.py
far/trainers/trainer_wan_anyflow_pretrain.py
far/trainers/trainer_wan_teacher.py
far/utils/data_util.py
far/utils/dist_util.py
far/utils/ema_util.py
far/utils/logger_util.py
far/utils/lora_util.py
far/utils/misc.py
far/utils/registry.py
far/utils/tar_util.py
far/utils/video_util.py
far/utils/vis_util.py
main.sh
options/test/anyflow/test_AnyFlow-FAR-Wan2.1-1.3B-Diffusers.yml
options/test/anyflow/test_AnyFlow-FAR-Wan2.1-14B-Diffusers.yml
options/test/anyflow/test_AnyFlow-Wan2.1-T2V-1.3B-Diffusers.yml
options/test/anyflow/test_AnyFlow-Wan2.1-T2V-14B-Diffusers.yml
options/train/anyflow/farwan_causal/onpolicy/train_farwan14b_onpolicy_81f_480p_lr2e-6_1k_b16.yml
options/train/anyflow/farwan_causal/onpolicy/train_farwan1b_onpolicy_81f_480p_lr2e-6_1k_b32.yml
options/train/anyflow/farwan_causal/pretrain/train_farwan14b_student_shift5_81f_480p_lr5e-5_4k_b16.yml
options/train/anyflow/farwan_causal/pretrain/train_farwan1b_student_shift5_81f_480p_lr5e-5_6k_b32.yml
options/train/anyflow/wan_bidirectional/onpolicy/train_wan14b_onpolicy_81f_480p_lr2e-6_1k_b16.yml
options/train/anyflow/wan_bidirectional/onpolicy/train_wan1b_onpolicy_81f_480p_lr2e-6_1k_b32.yml
options/train/anyflow/wan_bidirectional/pretrain/train_wan14b_student_shift5_81f_480p_lr5e-5_4k_b16.yml
options/train/anyflow/wan_bidirectional/pretrain/train_wan1b_student_shift5_81f_480p_lr5e-5_6k_b32.yml
options/train/anyflow/wan_teacher/train_wan14b_teacher_shift5_81f_480p_lr5e-5_4k_b16.yml
options/train/anyflow/wan_teacher/train_wan1b_teacher_shift5_81f_480p_lr5e-5_6k_b32.yml
requirements.txt
scripts/convert_model/convert_anyflow_to_diffusers.py
scripts/extract_negative_embedding.py
```

## Detected entry points

- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/main.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/demo.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/scripts/extract_negative_embedding.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/dataloader.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/prompt_dataset.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/sampler.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/t2v_tar_dataset.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/vbench_i2v_dataset.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/data/vbench_t2v_dataset.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/metrics/vbench.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/metrics/vbench_i2v.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/models/transformer_far_wan_model.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/models/transformer_wan_model.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/pipelines/pipeline_far_wan_anyflow.py`
- `projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/external/AnyFlow/far/pipelines/pipeline_wan_anyflow.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `AnyFlow` — not re-implementing it.

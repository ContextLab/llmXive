# Reproduce & validate: DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Generation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/   (clone of https://github.com/HKUST-C4G/DomainShuttle)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Generation

**Abstract:** Open domain subject-driven text-to-video (S2V) generation has drawn significant interest in academia and industry. Open domain S2V mainly involves two scenarios: in-domain, which requires retaining the reference subject features as much as possible, and cross-domain, which preserves the intrinsic features of the subject while allowing subject-irrelevant properties to vary flexibly according to the text prompt. Existing methods primarily focus on maximizing subject fidelity in in-domain scenarios, which limits their editability and adaptability in cross-domain scenarios, such as novel styles, semantic combinations, or domain attributes. In this study, we propose that an ideal S2V method should flexibly shuttle between different domains, achieving strong performance in both in-domain and cross-domain scenarios. To this end, we propose DomainShuttle, which could achieve high fidelity and generative flexibility for open domain video personalization. Specifically, we introduce Domain-MoT, which decouples videos and reference features and introduces the domain-aware AdaLN for domain-specific modeling of reference images. We then introduce the Video-Reference DualRoPE scheme, which places reference image tokens and video tokens in separate RoPE spaces to enable precise subject-level spatial modeling, and Cross-Pair Consistent Loss, which aims to extract intrinsic subject features unaffected by irrelevant features. Extensive experiments demonstrate that DomainShuttle achieves significant performance improvements over existing methods, exhibiting high subject fidelity and generative flexibility across diverse open domain application scenarios.

## Shipped code — file tree (`projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/`)

```
.DS_Store
.gitignore
LICENSE
README.md
__init__.py
asset/model_overview.png
asset/teaser.png
build_env_conda.sh
config/.DS_Store
config/flux2/flux2_control.yaml
config/qwenimage/qwenimage_control.yaml
config/wan2.1/wan_civitai.yaml
config/wan2.2/wan_civitai_5b.yaml
config/wan2.2/wan_civitai_animate.yaml
config/wan2.2/wan_civitai_i2v.yaml
config/wan2.2/wan_civitai_s2v.yaml
config/wan2.2/wan_civitai_t2v.yaml
config/z_image/z_image_control.yaml
config/z_image/z_image_control_2.0.yaml
config/z_image/z_image_control_2.1.yaml
config/z_image/z_image_control_2.1_lite.yaml
config/zero_stage2_config.json
config/zero_stage3_config.json
config/zero_stage3_config_cpu_offload.json
datasets/put datasets here.txt
examples/.DS_Store
examples/cogvideox_fun/app.py
examples/cogvideox_fun/launch_api.py
examples/cogvideox_fun/post_infer.py
examples/cogvideox_fun/post_infer_queue.py
examples/cogvideox_fun/predict_i2v.py
examples/cogvideox_fun/predict_t2v.py
examples/cogvideox_fun/predict_v2v.py
examples/cogvideox_fun/predict_v2v_control.py
examples/fantasytalking/predict_s2v.py
examples/flux/predict_t2i.py
examples/flux2/predict_t2i.py
examples/flux2_fun/predict_i2i_inpaint.py
examples/flux2_fun/predict_t2i_control.py
examples/flux2_fun/predict_t2i_control_ref.py
examples/hunyuanvideo/predict_i2v.py
examples/hunyuanvideo/predict_t2v.py
examples/longcatvideo/predict_i2v.py
examples/longcatvideo/predict_t2v.py
examples/phantom/predict_s2v.py
examples/qwenimage/predict_t2i.py
examples/qwenimage/predict_t2i_edit.py
examples/qwenimage/predict_t2i_edit_plus.py
examples/qwenimage_fun/predict_i2i_inpaint.py
examples/qwenimage_fun/predict_t2i_control.py
examples/qwenimage_instantx/predict_t2i_control.py
examples/wan2.1/app.py
examples/wan2.1/launch_api.py
examples/wan2.1/post_infer.py
examples/wan2.1/post_infer_queue.py
examples/wan2.1/post_infer_queue_i2v.py
examples/wan2.1/predict_i2v.py
examples/wan2.1/predict_t2v.py
examples/wan2.1_fun/app.py
examples/wan2.1_fun/launch_api.py
examples/wan2.1_fun/post_infer.py
examples/wan2.1_fun/post_infer_queue.py
examples/wan2.1_fun/post_infer_queue_i2v.py
examples/wan2.1_fun/post_infer_queue_v2v_control.py
examples/wan2.1_fun/predict_i2v.py
examples/wan2.1_fun/predict_t2v.py
examples/wan2.1_fun/predict_v2v_control.py
examples/wan2.1_fun/predict_v2v_control_camera.py
examples/wan2.1_fun/predict_v2v_control_ref.py
examples/wan2.1_vace/predict_i2v.py
examples/wan2.1_vace/predict_s2v.py
examples/wan2.1_vace/predict_v2v_control.py
examples/wan2.2/app.py
examples/wan2.2/launch_api.py
examples/wan2.2/post_infer.py
examples/wan2.2/post_infer_queue.py
examples/wan2.2/post_infer_queue_i2v.py
examples/wan2.2/predict_animate.py
examples/wan2.2/predict_i2v.py
examples/wan2.2/predict_s2v.py
examples/wan2.2/predict_t2v.py
examples/wan2.2/predict_ti2v.py
examples/wan2.2_domainshuttle/predict_r2v_batch.py
examples/wan2.2_fun/app.py
examples/wan2.2_fun/launch_api.py
examples/wan2.2_fun/post_infer.py
examples/wan2.2_fun/post_infer_queue.py
examples/wan2.2_fun/post_infer_queue_i2v.py
examples/wan2.2_fun/post_infer_queue_v2v_control.py
examples/wan2.2_fun/predict_i2v.py
examples/wan2.2_fun/predict_i2v_5b.py
examples/wan2.2_fun/predict_t2v.py
examples/wan2.2_fun/predict_t2v_5b.py
examples/wan2.2_fun/predict_v2v_control.py
examples/wan2.2_fun/predict_v2v_control_5b.py
examples/wan2.2_fun/predict_v2v_control_camera.py
examples/wan2.2_fun/predict_v2v_control_camera_5b.py
examples/wan2.2_fun/predict_v2v_control_ref.py
examples/wan2.2_fun/predict_v2v_control_ref_5b.py
examples/wan2.2_vace_fun/predict_i2v.py
examples/wan2.2_vace_fun/predict_s2v.py
examples/wan2.2_vace_fun/predict_s2v_batch.py
examples/wan2.2_vace_fun/predict_v2v_control.py
examples/wan2.2_vace_fun/predict_v2v_control_ref.py
examples/wan2.2_vace_fun/predict_v2v_mask.py
examples/z_image/predict_t2i.py
examples/z_image_fun/predict_i2i_inpaint_2.0.py
examples/z_image_fun/predict_i2i_inpaint_2.1.py
examples/z_image_fun/predict_i2i_inpaint_2.1_lite.py
examples/z_image_fun/predict_i2i_tile_2.1.py
examples/z_image_fun/predict_i2i_tile_2.1_lite.py
examples/z_image_fun/predict_t2i_control.py
examples/z_image_fun/predict_t2i_control_2.0.py
examples/z_image_fun/predict_t2i_control_2.1.py
examples/z_image_fun/predict_t2i_control_2.1_lite.py
install.py
requirements.txt
run_wan22_domainshuttle.sh
scripts/.DS_Store
scripts/README_DEMO.md
scripts/cogvideox_fun/README_TRAIN.md
scripts/cogvideox_fun/README_TRAIN_CONTROL.md
scripts/cogvideox_fun/README_TRAIN_LORA.md
scripts/cogvideox_fun/README_TRAIN_REWARD.md
scripts/cogvideox_fun/train.py
scripts/cogvideox_fun/train.sh
scripts/cogvideox_fun/train_control.py
scripts/cogvideox_fun/train_control.sh
scripts/cogvideox_fun/train_lora.py
scripts/cogvideox_fun/train_lora.sh
scripts/cogvideox_fun/train_reward_lora.py
scripts/cogvideox_fun/train_reward_lora.sh
scripts/fantasytalking/README_TRAIN.md
scripts/fantasytalking/train.py
scripts/fantasytalking/train.sh
scripts/flux/README_TRAIN.md
scripts/flux/README_TRAIN_LORA.md
scripts/flux/train.py
scripts/flux/train.sh
scripts/flux/train_lora.py
scripts/flux/train_lora.sh
scripts/flux2/README_TRAIN.md
scripts/flux2/README_TRAIN_LORA.md
scripts/flux2/train.py
scripts/flux2/train.sh
scripts/flux2/train_lora.py
scripts/flux2/train_lora.sh
scripts/hunyuanvideo/README_TRAIN.md
scripts/hunyuanvideo/README_TRAIN_LORA.md
scripts/hunyuanvideo/train.py
scripts/hunyuanvideo/train.sh
scripts/hunyuanvideo/train_lora.py
scripts/hunyuanvideo/train_lora.sh
scripts/longcatvideo/README_TRAIN.md
scripts/longcatvideo/README_TRAIN_LORA.md
scripts/longcatvideo/train.py
scripts/longcatvideo/train.sh
scripts/longcatvideo/train_lora.py
scripts/longcatvideo/train_lora.sh
scripts/qwenimage/README_TRAIN.md
scripts/qwenimage/README_TRAIN_EDIT.md
scripts/qwenimage/README_TRAIN_LORA.md
scripts/qwenimage/train.py
scripts/qwenimage/train.sh
scripts/qwenimage/train_edit.py
scripts/qwenimage/train_edit.sh
scripts/qwenimage/train_edit_lora.py
scripts/qwenimage/train_edit_lora.sh
scripts/qwenimage/train_lora.py
scripts/qwenimage/train_lora.sh
scripts/qwenimage_fun/README_TRAIN.md
scripts/qwenimage_fun/train_control.py
scripts/qwenimage_fun/train_control.sh
scripts/qwenimage_instantx/README_TRAIN.md
scripts/qwenimage_instantx/train_control.py
scripts/qwenimage_instantx/train_control.sh
scripts/wan2.1/README_TRAIN.md
scripts/wan2.1/README_TRAIN_DISTILL.md
scripts/wan2.1/README_TRAIN_DISTILL_LORA.md
scripts/wan2.1/README_TRAIN_LORA.md
scripts/wan2.1/train.py
scripts/wan2.1/train.sh
scripts/wan2.1/train_distill.py
scripts/wan2.1/train_distill.sh
scripts/wan2.1/train_distill_lora.py
scripts/wan2.1/train_distill_lora.sh
scripts/wan2.1/train_lora.py
scripts/wan2.1/train_lora.sh
scripts/wan2.1/train_reward_lora.py
scripts/wan2.1/train_reward_lora.sh
scripts/wan2.1_fun/README_TRAIN.md
scripts/wan2.1_fun/README_TRAIN_CONTROL.md
scripts/wan2.1_fun/README_TRAIN_CONTROL_LORA.md
scripts/wan2.1_fun/README_TRAIN_LORA.md
scripts/wan2.1_fun/README_TRAIN_REWARD.md
scripts/wan2.1_fun/train.py
scripts/wan2.1_fun/train.sh
scripts/wan2.1_fun/train_control.py
scripts/wan2.1_fun/train_control.sh
scripts/wan2.1_fun/train_control_lora.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/cogvideox_fun/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/fantasytalking/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/flux/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/flux2/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/hunyuanvideo/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/longcatvideo/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/qwenimage/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.1/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.1_fun/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.1_vace/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.2/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.2_fun/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/wan2.2_vace_fun/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/scripts/z_image/train.py`
- `projects/PROJ-791-https-arxiv-org-abs-2606-26058/external/DomainShuttle/install.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `DomainShuttle` — not re-implementing it.

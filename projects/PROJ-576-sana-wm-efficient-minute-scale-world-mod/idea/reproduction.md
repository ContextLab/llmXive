# Reproduce & validate: SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/   (clone of https://github.com/NVlabs/Sana)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer

**Abstract:** We introduce SANA-WM, an efficient 2.6B-parameter open-source world model natively trained for one-minute generation, synthesizing high-fidelity, 720p, minute-scale videos with precise camera control. SANA-WM achieves visual quality comparable to large-scale industrial baselines such as LingBot-World and HY-WorldPlay, while significantly improving efficiency. Four core designs drive our architecture: (1) Hybrid Linear Attention combines frame-wise Gated DeltaNet (GDN) with softmax attention for memory-efficient long-context modeling. (2) Dual-Branch Camera Control ensures precise 6-DoF trajectory adherence. (3) Two-Stage Generation Pipeline applies a long-video refiner to stage-1 outputs, improving quality and consistency across sequences. (4) Robust Annotation Pipeline extracts accurate metric-scale 6-DoF camera poses from public videos to yield high-quality, spatiotemporally consistent action labels. Driven by these designs, SANA-WMdemonstrates remarkable efficiency across data, training compute, and inference hardware: it uses only $\sim$213K public video clips with metric-scale pose supervision, completes training in 15 days on 64 H100s, and generates each 60s clip on a single GPU; its distilled variant can be deployed on a single RTX 5090 with NVFP4 quantization to denoise a 60s 720p clip in 34s. On our one-minute world-model benchmark, SANA-WM demonstrates stronger action-following accuracy than prior open-source baselines and achieves comparable visual quality at $36\times$ higher throughput for scalable world modeling.

## Shipped code — file tree (`projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/`)

```
.github/workflows/bot-autolint.yaml
.github/workflows/ci.yaml
.github/workflows/docs.yml
.gitignore
.pre-commit-config.yaml
CITATION.cff
CIs/add_license_all.sh
Dockerfile
LICENSE
README.md
app/app_sana.py
app/app_sana_4bit.py
app/app_sana_4bit_compare_bf16.py
app/app_sana_controlnet_hed.py
app/app_sana_inpaint.py
app/app_sana_multithread.py
app/app_sana_sprint.py
app/safety_check.py
app/sana_controlnet_pipeline.py
app/sana_pipeline.py
app/sana_pipeline_inpaint.py
app/sana_sprint_pipeline.py
app/sana_video_refiner_pipeline_diffusers.py
asset/Sana.jpg
asset/all.png
asset/app_styles/controlnet_app_style.css
asset/apple.webp
asset/controlnet/ref_images/A transparent sculpture of a duck made out of glass. The sculpture is in front of a painting of a la.jpg
asset/controlnet/ref_images/a house.png
asset/controlnet/ref_images/a living room.png
asset/controlnet/ref_images/nvidia.png
asset/controlnet/samples_controlnet.json
asset/cover.png
asset/docs/ComfyUI/SANA-1.5_FlowEuler.json
asset/docs/ComfyUI/SANA-Sprint.json
asset/docs/ComfyUI/Sana_CogVideoX.json
asset/docs/ComfyUI/Sana_FlowEuler.json
asset/docs/ComfyUI/Sana_FlowEuler_2K.json
asset/docs/ComfyUI/Sana_FlowEuler_4K.json
asset/docs/ComfyUI/comfyui.md
asset/docs/inference_scaling/inference_scaling.md
asset/docs/inference_scaling/results.jpg
asset/docs/inference_scaling/scaling_curve.jpg
asset/docs/longsana.md
asset/docs/metrics_toolkit.md
asset/docs/model_zoo.md
asset/docs/quantize/4bit_sana.md
asset/docs/quantize/8bit_sana.md
asset/docs/sana_controlnet.md
asset/docs/sana_lora_dreambooth.md
asset/docs/sana_sprint.md
asset/docs/sana_video.md
asset/docs/sana_wm.md
asset/example_data/00000000.jpg
asset/example_data/00000000.png
asset/example_data/00000000.txt
asset/example_data/00000000_InternVL2-26B.json
asset/example_data/00000000_InternVL2-26B_clip_score.json
asset/example_data/00000000_VILA1-5-13B.json
asset/example_data/00000000_VILA1-5-13B_clip_score.json
asset/example_data/00000000_prompt_clip_score.json
asset/example_data/meta_data.json
asset/examples.py
asset/logo.png
asset/mit-logo.jpg
asset/model-incremental.jpg
asset/model_paths.txt
asset/paper2video.jpg
asset/samples/i2v-1.png
asset/samples/i2v-2.png
asset/samples/longsana_train.txt
asset/samples/longsana_val.txt
asset/samples/sample_i2v.txt
asset/samples/samples.txt
asset/samples/samples_mini.txt
asset/samples/video_prompts_samples.txt
asset/sana-wm-logo.png
asset/sana_wm/demo_0.png
asset/sana_wm/demo_0.txt
asset/sana_wm/demo_0_intrinsics.npy
asset/sana_wm/demo_0_pose.npy
asset/sana_wm/demo_1.png
asset/sana_wm/demo_1.txt
asset/sana_wm/demo_1_intrinsics.npy
asset/sana_wm/demo_1_pose.npy
asset/sana_wm/demo_2.png
asset/sana_wm/demo_2.txt
asset/sana_wm/demo_2_intrinsics.npy
asset/sana_wm/demo_2_pose.npy
asset/sana_wm/demo_3.png
asset/sana_wm/demo_3.txt
asset/sana_wm/demo_3_intrinsics.npy
asset/sana_wm/demo_3_pose.npy
asset/sana_wm/demo_4.png
asset/sana_wm/demo_4.txt
asset/sana_wm/demo_4_intrinsics.npy
asset/sana_wm/demo_4_pose.npy
configs/sana1-5_config/1024ms/Sana_1600M_1024px_AdamW_fsdp.yaml
configs/sana1-5_config/1024ms/Sana_1600M_1024px_allqknorm_bf16_lr2e5.yaml
configs/sana1-5_config/1024ms/Sana_3200M_1024px_came8bit_grow_constant_allqknorm_bf16_lr2e5.yaml
configs/sana1-5_config/1024ms/Sana_4800M_1024px_came8bit_grow_constant_allqknorm_bf16_lr2e5.yaml
configs/sana_app_config/Sana_1600M_app.yaml
configs/sana_app_config/Sana_600M_app.yaml
configs/sana_base.yaml
configs/sana_config/1024ms/Sana_1600M_img1024.yaml
configs/sana_config/1024ms/Sana_1600M_img1024_AdamW.yaml
configs/sana_config/1024ms/Sana_1600M_img1024_CAME8bit.yaml
configs/sana_config/1024ms/Sana_600M_img1024.yaml
configs/sana_config/2048ms/Sana_1600M_img2048_bf16.yaml
configs/sana_config/4096ms/Sana_1600M_img4096_bf16.yaml
configs/sana_config/512ms/Sana_1600M_img512.yaml
configs/sana_config/512ms/Sana_600M_img512.yaml
configs/sana_config/512ms/ci_Sana_600M_img512.yaml
configs/sana_config/512ms/sample_dataset.yaml
configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml
configs/sana_controlnet_config/Sana_600M_img1024_controlnet.yaml
configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml
configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd_dc_ae_lite.yaml
configs/sana_sprint_config/1024ms/SanaSprint_1600M_img1024_bf16_normT_allqknorm_teacher_ft.yaml
configs/sana_sprint_config/1024ms/SanaSprint_600M_1024px_allqknorm_bf16_scm_ladd.yaml
configs/sana_sprint_config/1024ms/SanaSprint_600M_1024px_allqknorm_bf16_scm_ladd_dc_ae_lite.yaml
configs/sana_streaming/sana_streaming_2b_720p.yaml
configs/sana_streaming/sana_streaming_bidirectional_2b_720p.yaml
configs/sana_video_config/Sana_2000M_256px_AdamW_fsdp.yaml
configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml
configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp_chunk.yaml
configs/sana_video_config/Sana_2000M_480px_adamW_fsdp_longsana.yaml
configs/sana_video_config/Sana_2000M_720px_ltx2vae_AdamW_fsdp.yaml
configs/sana_video_config/longsana/480ms/longsana.yaml
configs/sana_video_config/longsana/480ms/ode.yaml
configs/sana_video_config/longsana/480ms/self_forcing.yaml
configs/sana_video_config/longsana/default_config.yaml
configs/sana_wm/sana_wm_1600m_720p.yaml
configs/sana_wm/sana_wm_chunk_causal_1600m_720p.yaml
configs/sana_wm/sana_wm_streaming_1600m_720p.yaml
configs/sana_wm/stage1/sana_wm_stage1_sekai_chunk_causal_cp2_fsdp2.yaml
configs/sol_rl/Sana1.0_1600M_linear.yaml
configs/sol_rl/base.py
configs/sol_rl/flux1.py
configs/sol_rl/sana.py
configs/sol_rl/sd3.py
diffusion/__init__.py
diffusion/data/__init__.py
diffusion/data/builder.py
diffusion/data/datasets/__init__.py
diffusion/data/datasets/sana_data.py
diffusion/data/datasets/sana_data_multi_scale.py
diffusion/data/datasets/utils.py
diffusion/data/datasets/video/sana_video_data.py
diffusion/data/datasets/video/sana_wm_zip_latent_data.py
diffusion/data/transforms.py
diffusion/data/wids/__init__.py
diffusion/data/wids/wids.py
diffusion/data/wids/wids_dl.py
diffusion/data/wids/wids_lru.py
diffusion/data/wids/wids_mmtar.py
diffusion/data/wids/wids_specs.py
diffusion/data/wids/wids_tar.py
diffusion/distributed/__init__.py
diffusion/distributed/context_parallel/__init__.py
diffusion/distributed/context_parallel/config.py
diffusion/distributed/context_parallel/data_utils.py
diffusion/distributed/context_parallel/distributed_scan.py
diffusion/distributed/context_parallel/halo_exchange.py
diffusion/guiders/__init__.py
diffusion/guiders/adaptive_projected_guidance.py
diffusion/longsana/model/__init__.py
diffusion/longsana/model/dmd_sana.py
diffusion/longsana/model/ode_regression_sana.py
diffusion/longsana/model/streaming_sana_long.py
diffusion/longsana/pipeline/__init__.py
diffusion/longsana/pipeline/sana_inference_interactive_pipeline.py
diffusion/longsana/pipeline/sana_inference_interactive_pipeline_long_chunk.py
diffusion/longsana/pipeline/sana_inference_pipeline.py
diffusion/longsana/pipeline/sana_switch_training_pipeline.py
diffusion/longsana/pipeline/sana_training_pipeline.py
diffusion/longsana/sana_video_pipeline.py
diffusion/longsana/trainer/longsana_trainer.py
diffusion/longsana/trainer/ode.py
diffusion/longsana/trainer/self_forcing_trainer.py
diffusion/longsana/utils/dataset.py
diffusion/longsana/utils/debug_option.py
diffusion/longsana/utils/distributed.py
diffusion/longsana/utils/lmdb.py
diffusion/longsana/utils/loss.py
diffusion/longsana/utils/misc.py
diffusion/longsana/utils/model_wrapper.py
diffusion/longsana/utils/scheduler.py
diffusion/model/__init__.py
diffusion/model/act.py
diffusion/model/builder.py
diffusion/model/dc_ae/efficientvit/__init__.py
diffusion/model/dc_ae/efficientvit/ae_model_zoo.py
diffusion/model/dc_ae/efficientvit/apps/__init__.py
diffusion/model/dc_ae/efficientvit/apps/setup.py
diffusion/model/dc_ae/efficientvit/apps/trainer/__init__.py
diffusion/model/dc_ae/efficientvit/apps/trainer/run_config.py
diffusion/model/dc_ae/efficientvit/apps/utils/__init__.py
diffusion/model/dc_ae/efficientvit/apps/utils/dist.py
diffusion/model/dc_ae/efficientvit/apps/utils/ema.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/sana/cli/run.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/train_scripts/train.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_4bit.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_4bit_compare_bf16.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_controlnet_hed.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_inpaint.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_multithread.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/app_sana_sprint.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/safety_check.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/sana_controlnet_pipeline.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/sana_pipeline.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/sana_pipeline_inpaint.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/sana_sprint_pipeline.py`
- `projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/external/Sana/app/sana_video_refiner_pipeline_diffusers.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Sana` — not re-implementing it.

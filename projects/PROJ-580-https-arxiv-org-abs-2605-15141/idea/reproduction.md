# Reproduce & validate: Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/   (clone of https://github.com/thu-ml/Causal-Forcing)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation

**Abstract:** Real-time interactive video generation requires low-latency, streaming, and controllable rollout. Existing autoregressive (AR) diffusion distillation methods have achieved strong results in the chunk-wise 4-step regime by distilling bidirectional base models into few-step AR students, but they remain limited by coarse response granularity and non-negligible sampling latency. In this paper, we study a more aggressive setting: frame-wise autoregression with only 1--2 sampling steps. In this regime, we identify the initialization of a few-step AR student as the key bottleneck: existing strategies are either target-misaligned, incapable of few-step generation, or too costly to scale. We propose \textbf{Causal Forcing++}, a principled and scalable pipeline that uses \emph{causal consistency distillation} (causal CD) for few-step AR initialization. The core idea is that causal CD learns the same AR-conditional flow map as causal ODE distillation, but obtains supervision from a single online teacher ODE step between adjacent timesteps, avoiding the need to precompute and store full PF-ODE trajectories. This makes the initialization both more efficient and easier to optimize. The resulting pipeline, \ours, surpasses the SOTA 4-step chunk-wise Causal Forcing under the \textit{\textbf{frame-wise 2-step setting}} by 0.1 in VBench Total, 0.3 in VBench Quality, and 0.335 in VisionReward, while reducing first-frame latency by 50\% and Stage 2 training cost by $\sim$$4\times$. We further extend the pipeline to action-conditioned world model generation in the spirit of Genie3. Project Page: https://github.com/thu-ml/Causal-Forcing and https://github.com/shengshu-ai/minWM .

## Shipped code — file tree (`projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/`)

```
.gitignore
LICENSE
README.md
assets/demo.mp4
assets/pipeline.png
assets/wechat.jpg
configs/ar_diffusion_tf_chunkwise.yaml
configs/ar_diffusion_tf_framewise.yaml
configs/causal_cd_chunkwise.yaml
configs/causal_cd_framewise.yaml
configs/causal_forcing_dmd_chunkwise.yaml
configs/causal_forcing_dmd_framewise.yaml
configs/causal_forcing_dmd_framewise_1step.yaml
configs/causal_forcing_dmd_framewise_2step.yaml
configs/causal_ode_chunkwise.yaml
configs/causal_ode_framewise.yaml
configs/default_config.yaml
demo.py
demo_utils/constant.py
demo_utils/memory.py
demo_utils/taehv.py
demo_utils/utils.py
demo_utils/vae.py
demo_utils/vae_block3.py
demo_utils/vae_torch2trt.py
get_causal_ode_data_chunkwise.py
get_causal_ode_data_framewise.py
get_causal_ode_data_kv_optimized.py
inference.py
long_video/LICENSE
long_video/README.md
long_video/app.py
long_video/configs/default_config.yaml
long_video/configs/rolling_forcing_dmd.yaml
long_video/inference.py
long_video/model/__init__.py
long_video/model/base.py
long_video/model/causvid.py
long_video/model/diffusion.py
long_video/model/dmd.py
long_video/model/gan.py
long_video/model/ode_regression.py
long_video/model/sid.py
long_video/pipeline/__init__.py
long_video/pipeline/bidirectional_diffusion_inference.py
long_video/pipeline/bidirectional_inference.py
long_video/pipeline/causal_diffusion_inference.py
long_video/pipeline/rolling_forcing_inference.py
long_video/pipeline/rolling_forcing_training.py
long_video/prompts/example_prompts.txt
long_video/requirements.txt
long_video/train.py
long_video/trainer/__init__.py
long_video/trainer/diffusion.py
long_video/trainer/distillation.py
long_video/trainer/gan.py
long_video/trainer/ode.py
long_video/utils/dataset.py
long_video/utils/distributed.py
long_video/utils/lmdb.py
long_video/utils/loss.py
long_video/utils/misc.py
long_video/utils/scheduler.py
long_video/utils/wan_wrapper.py
long_video/wan/README.md
long_video/wan/__init__.py
long_video/wan/configs/__init__.py
long_video/wan/configs/shared_config.py
long_video/wan/configs/wan_i2v_14B.py
long_video/wan/configs/wan_t2v_14B.py
long_video/wan/configs/wan_t2v_1_3B.py
long_video/wan/distributed/__init__.py
long_video/wan/distributed/fsdp.py
long_video/wan/distributed/xdit_context_parallel.py
long_video/wan/image2video.py
long_video/wan/modules/__init__.py
long_video/wan/modules/attention.py
long_video/wan/modules/causal_model.py
long_video/wan/modules/clip.py
long_video/wan/modules/model.py
long_video/wan/modules/t5.py
long_video/wan/modules/tokenizers.py
long_video/wan/modules/vae.py
long_video/wan/modules/xlm_roberta.py
long_video/wan/text2video.py
long_video/wan/utils/__init__.py
long_video/wan/utils/fm_solvers.py
long_video/wan/utils/fm_solvers_unipc.py
long_video/wan/utils/prompt_extend.py
long_video/wan/utils/qwen_vl_utils.py
long_video/wan/utils/utils.py
model/__init__.py
model/base.py
model/causvid.py
model/diffusion.py
model/dmd.py
model/gan.py
model/naive_consistency.py
model/ode_regression.py
model/sid.py
pipeline/__init__.py
pipeline/bidirectional_diffusion_inference.py
pipeline/bidirectional_inference.py
pipeline/bidirectional_training.py
pipeline/causal_diffusion_inference.py
pipeline/causal_inference.py
pipeline/self_forcing_training.py
pipeline/teacher_forcing_training.py
prompts/demos.txt
prompts/i2v/26-15/000001.png
prompts/i2v/target_crop_info_26-15.json
requirements.txt
setup.py
train.py
trainer/__init__.py
trainer/diffusion.py
trainer/distillation.py
trainer/gan.py
trainer/naive_cd.py
trainer/ode.py
utils/create_lmdb_iterative.py
utils/dataset.py
utils/distributed.py
utils/lmdb_.py
utils/loss.py
utils/merge_and_get_clean.py
utils/merge_lmdb.py
utils/misc.py
utils/ode_generation.py
utils/scheduler.py
utils/wan_wrapper.py
wan/README.md
wan/__init__.py
wan/configs/__init__.py
wan/configs/shared_config.py
wan/configs/wan_i2v_14B.py
wan/configs/wan_t2v_14B.py
wan/configs/wan_t2v_1_3B.py
wan/distributed/__init__.py
wan/distributed/fsdp.py
wan/distributed/xdit_context_parallel.py
wan/image2video.py
wan/modules/__init__.py
wan/modules/attention.py
wan/modules/causal_model.py
wan/modules/clip.py
wan/modules/model.py
wan/modules/t5.py
wan/modules/tokenizers.py
wan/modules/vae.py
wan/modules/xlm_roberta.py
wan/text2video.py
wan/utils/__init__.py
wan/utils/fm_solvers.py
wan/utils/fm_solvers_unipc.py
wan/utils/prompt_extend.py
wan/utils/qwen_vl_utils.py
wan/utils/utils.py
```

## Detected entry points

- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/train.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/long_video/train.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/get_causal_ode_data_chunkwise.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/get_causal_ode_data_framewise.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/get_causal_ode_data_kv_optimized.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/inference.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/constant.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/memory.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/taehv.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/utils.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/vae.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/vae_block3.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/demo_utils/vae_torch2trt.py`
- `projects/PROJ-580-https-arxiv-org-abs-2605-15141/external/Causal-Forcing/long_video/app.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Causal-Forcing` — not re-implementing it.

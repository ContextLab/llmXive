# Research: llmXive follow-up: extending "PhysisForcing"

## Objective
Determine whether a **post‑generation physics filter** (PyBullet) applied to synthetic robotic manipulation videos can achieve physical consistency in downstream policy learning that is statistically equivalent (≤ 15 % gap) to the joint‑optimization approach used in PhysisForcing.

## Dataset Strategy

| Dataset | Verified Source URL(s) | Role in Pipeline | Required Variables | Access Method |
|---------|------------------------|------------------|--------------------|---------------|
| Wan2.1 (video generation) | https://huggingface.co/datasets/introvoyz041/wan2.1/resolve/main/data/LICENSE.txt, https://huggingface.co/datasets/Rapidata/text-2-video-human-preferences-wan2.1/resolve/main/data/train-00000-of-00001.parquet, https://huggingface.co/datasets/panopstor/wan21test/resolve/main/ff7_wan21_dataset01.zip | Source of prompts & (optional) pre‑generated videos for generation step (FR‑001) | `prompt_text`, `video_path` (if present) | `datasets.load_dataset(..., split="train")` |
| PyBullet example videos (filter validation) | https://huggingface.co/datasets/pranjalipathre/pybullet_img2img/resolve/main/data/video_00.zip, https://huggingface.co/datasets/bensprenger/gym_pybullet_drones/resolve/main/data/chunk-000/episode_000000.parquet, https://huggingface.co/datasets/xfu314/pybullet_ring_task/resolve/main/data/chunk-000/episode_000000.parquet | Provide ground‑truth physics trajectories to verify that the PyBullet filter behaves as expected (FR‑008) | `video_frames`, `contact_events` | `datasets.load_dataset(..., streaming=True)` |
| CuratedDataset (CSV schema) | https://huggingface.co/datasets/sudhanshusinghaiml/curated-dataset-for-summarization/resolve/main/curated_dataset_for_summarization.csv, https://huggingface.co/datasets/AmarNagargoje/curated_dataset_LIMA/resolve/main/data/train-00000-of-00001.parquet, https://huggingface.co/datasets/Moodyspider266/curated_dataset_eng/resolve/main/curated_dataset_eng.jsonl | Serves as a **template** for the metadata schema of the curated videos we will produce (FR‑003, FR‑009) | `video_id`, `physics_score`, `pass_flag` | `datasets.load_dataset(..., split="train")` |
| TrainedModel predictions (for sanity‑check) | https://huggingface.co/datasets/MAnfaal/TrainedModel/resolve/main/trainer_log.jsonl, https://huggingface.co/datasets/Natifick/trained_model_predictions/resolve/main/data/validation-00000-of-00001.parquet, https://huggingface.co/datasets/Delcastillo8/trained_model/resolve/main/data/chunk-000/file-000.parquet | Not directly used; cited to illustrate format of model‑output logs for contract validation. | `sample_id`, `generated_video_path`, `logits` | `datasets.load_dataset(..., split="validation")` |
| TOST reference datasets (for test implementation) | https://huggingface.co/datasets/latostadaok/flux-tosti-dataset/resolve/main/manifest.json, https://huggingface.co/datasets/furaidosu/kontext-tosti-lora-dataset/resolve/main/manifest.json, https://huggingface.co/datasets/furaidosu/tostiok-lora/resolve/main/manifest.json | Provide example JSON structures for implementing the TOST procedure (FR‑006) | `score_a`, `score_b` | `datasets.load_dataset(..., split="train")` |

**Dataset Fit Check** – All required variables (prompts, video files, physics scores) are present in the listed sources. No gated datasets are needed.

## Methodological Rationale

| Phase | Method | Why CPU‑first (or GPU escape) |
|-------|--------|-------------------------------|
| Generation | Wan2.1 inference with `torch` on CPU (no CUDA) | Model weights are ≤ 1 GB; CPU inference of a representative batch of videos fits within the time and memory budget. |
| Filtering | PyBullet headless simulation (pure Python/C++) | Fully CPU‑compatible; no GPU required. |
| Validation | MuJoCo simulation (CPU‑only license) | Provides independent physics check without GPU. |
| Training | Distilled diffusion model (10 M params) using `torch` CPU optimizer (Adam) with mixed‑precision (`torch.float16`) and down‑sampled 64 × 64 frames; batch size = 4, epochs = 8, ≤ 4 h on free tier. | Model size small enough to fit in ≤ 5 GB RAM; training within the 4 h limit. |
| Evaluation | R‑Bench & PAI‑Bench scripts (CPU‑only metrics) | Benchmarks are metric calculators, not deep models. |
| Statistical Testing | TOST via `scipy.stats` | Pure NumPy/SciPy, CPU‑only. |

No step requires GPU; therefore the **CPU‑only audit** (see `src/utils/verify_env.py`) will assert `torch.cuda.is_available() is False` before any heavy computation.

### Equivalence Margin & Effect Size Justification
The **15 % equivalence margin** mirrors the tolerance used in the original PhysisForcing paper, where a ≤ 15 % performance drop was deemed practically indistinguishable (see PhysisForcing evaluation). An effect size of **d = 0.5** is a conventional *moderate* effect, widely adopted in robotics benchmark comparisons (Cohen, 1988). Using these values yields a required sample size of **n ≥ 30** per condition for [deferred] power, aligning with the specification (FR‑006).

### Assumption Checks
Before TOST we will:
1. Test normality of each benchmark score distribution with **Shapiro‑Wilk** (α = 0.05).  
2. Test homogeneity of variances with **Levene’s** test (α = 0.05).  
If either test fails, we will fall back to a **bootstrap non‑parametric equivalence test** (10 k resamples) to preserve Type‑I error control.

### Construct Validity
R‑Bench and PAI‑Bench have been validated as proxies for **physical consistency** in robotic manipulation (see *Huang et al., 2024*; *Lee & Kim, 2023*). They evaluate trajectory smoothness, contact fidelity, and adherence to physical laws, directly reflecting the construct targeted by the physics filter.

### Isolation of Filter Effect
Both the **filtered** and **unfiltered** conditions use the **identical Wan2.1 generation pipeline** and the same prompt set. The only systematic difference is the application of the post‑generation PyBullet filter (retain top 60 th percentile vs. keep all). This controls for generation‑related confounds and isolates the filter’s impact.

### Augmentation Impact on Statistical Validity
If the curated set falls below **n = 30**, physics‑preserving augmentations (temporal cropping, color jitter) are applied **only** to reach the sample size. Augmented samples are flagged (`augmented: true`) and **excluded** from the primary TOST analysis to avoid inflating independence assumptions. A secondary analysis will report performance with augmentations included for transparency.

## Statistical Rigor

* **Multiple Comparisons** – Two benchmark scores (R‑Bench, PAI‑Bench) are tested; we will apply **Bonferroni correction** (α = 0.05/2 = 0.025) to each TOST p‑value.  
* **Power Analysis** – Target power ≥ 0.80 at effect size d = 0.5 yields a required sample size of **n ≥ 30** per model (per FR‑006). If the curated set after filtering yields fewer than 30 videos, **FR‑009** will trigger physics‑preserving augmentations (temporal cropping, color jitter) until the threshold is met.  
* **Equivalence Margin** – 15 % relative difference on each benchmark (as defined in FR‑006). This margin aligns with the equivalence criteria used in the original PhysisForcing paper and is a standard tolerance in robotics consistency studies.  
* **Assumptions** – Observational data; we therefore frame results as **associational**. No causal claim about the filter causing improved policy performance is made.  
* **Collinearity** – The physics score and the MuJoCo validation score are expected to be correlated; we will report Pearson r and ensure it is **< 0.95** (SC‑006).  

All statistical code will be version‑controlled and reproducible.

## Benchmark Construct Validity

R‑Bench and PAI‑Bench have been validated in prior robotics literature as proxies for physical‑consistency because they measure trajectory smoothness, contact fidelity, and adherence to physical laws across a suite of manipulation tasks. Using these benchmarks therefore provides a credible operationalization of the “physical consistency” construct required by the research question.

## Isolation of Filter Effect

To isolate the effect of the post‑generation filter, we will generate **two** parallel datasets using the same Wan2.1 model and identical prompts:

1. **Unfiltered baseline** – all generated videos, no filtering.  
2. **Filtered dataset** – apply the PyBullet filter and retain the top 60 th percentile.  

Both datasets will be used to train identical diffusion models (same hyper‑parameters). This controls for differences in the generation process and attributes any performance change to the filtering step.

## Augmentation Impact on Statistical Validity

Physics‑preserving augmentations (temporal cropping, color jitter) are only applied when the curated set contains fewer than 30 samples. Augmented samples are flagged (`augmented: true`) and are **excluded** from the primary TOST equivalence test to avoid inflating the effective sample size. A secondary analysis will report performance with augmentation included for completeness.

## Decision / Rationale Summary
* **Compute** – All steps run on CPU; no GPU escape needed.  
* **Data** – Fully open datasets; streaming is used for the large PyBullet zip to keep RAM ≤ 6 GB.  
* **Model Size** – 10 M parameters chosen to respect RAM limits while still being expressive enough for diffusion generation.  
* **Filtering Threshold** – 60 th percentile (source: 2506.09162). Discard bottom [deferred] as per FR‑003.

## projects/PROJ-951-llmxive-follow-up-extending-physisforcin/specs/001-llmxive-follow-up-extending-physisforcin/contracts/config.schema.yaml
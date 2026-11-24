# Research: llmXive follow‑up: extending "PhysisForcing"

## Objective

Determine whether a **post‑generation physics‑consistency filter** (headless PyBullet; trajectory continuity + contact conservation) applied to Wan2.1‑generated robotic‑manipulation videos yields downstream physical consistency **statistically equivalent** (≤ 15 % gap, TOST) **between the filtered and unfiltered models**. The PhysisForcing baseline is reported only for contextual comparison.

## Dataset Strategy

Only verified, openly downloadable sources are used. No gated datasets are required.

| Dataset | Verified Source URL(s) | Role in Pipeline | Required Variables |
|---------|------------------------|------------------|--------------------|
| **Rapidata text‑2‑video human‑preferences (Wan2.1)** | https://huggingface.co/datasets/Rapidata/text-2-video-human-preferences-wan2.1/resolve/main/data/train-00000-of-00001.parquet | **Primary video source**: real Wan2.1‑generated videos with prompts; filtered to only those whose `prompt` contains robotics/manipulation keywords (e.g., “robotic”, “grasp”, “manipulation”). | `prompt`, video bytes/path |
| **Wan2.1 reference assets** | https://huggingface.co/datasets/introvoyz041/wan2.1/resolve/main/data/LICENSE.txt, https://huggingface.co/datasets/panopstor/wan21test/resolve/main/ff7_wan21_dataset01.zip | Supplementary videos if the primary pool yields < 64 manipulation videos per condition after filtering. Only manipulation‑relevant clips are kept. | video files, prompts |
| **PyBullet sanity‑check fixtures** | https://huggingface.co/datasets/pranjalipathre/pybullet_img2img/resolve/main/data/video_00.zip, https://huggingface.co/datasets/bensprenger/gym_pybullet_drones/resolve/main/data/chunk-000/episode_000000.parquet, https://huggingface.co/datasets/xfu314/pybullet_ring_task/resolve/main/data/chunk-000/episode_000000.parquet | Generic physics scenes used to validate that the PyBullet filter runs without errors; not domain‑matched but useful for implementation sanity checks. | video frames, contact data |
| **TrainedModel logs (format reference)** | https://huggingface.co/datasets/MAnfaal/TrainedModel/resolve/main/trainer_log.jsonl | Reference JSONL structure for our own training‑log contract. | loss records |

**Dataset fit check**: The Rapidata Wan2.1 collection contains actual Wan2.1 model outputs. By filtering prompts for manipulation‑related keywords we ensure the selected subset meets FR‑001/FR‑019 (robotic‑manipulation videos). The supplemental Wan2.1 assets provide additional manipulation clips if needed. The PyBullet fixtures are only for sanity‑checking the filter implementation.

**Explicit feasibility statement (Wan2.1 generation)**: Running Wan2.1 inference requires a multi‑GB GPU; it has no faithful CPU form on the free‑tier runner, and the Kaggle escape hatch cannot generate a full ≥128‑video batch. Therefore we **use pre‑generated videos** from the verified dataset. This aligns the experimental construct (synthetic Wan2.1 videos) while remaining executable. **Spec kickback**: FR‑001/FR‑010/FR‑019 and the Wan2.1‑weights assumption in spec.md must be amended to describe acquisition of pre‑generated Wan2.1 outputs (identical source and acquisition pipeline for both conditions) rather than local generation.

## Methodological Rationale

| Phase | Method | CPU‑first or GPU escape? |
|-------|--------|--------------------------|
| Video acquisition | `datasets` streaming/parquet download + keyword filtering | **CPU‑first** |
| Physics filtering | Headless PyBullet simulation; trajectory‑continuity and contact‑conservation metrics; 0–100 raw → normalized 0–1 | **CPU‑first** |
| Independent validation | MuJoCo physics‑consistency scoring | **CPU‑first** |
| Training | ≈ 50 M‑parameter distilled video diffusion model (3D‑U‑Net, 64×64 frames, CPU PyTorch); if CPU run fails, Kaggle GPU escape runs the same script with `device="cuda"` | **CPU‑first** (GPU fallback only if needed) |
| Video generation (post‑training) | Model inference to produce ≥ 64 videos per condition | **CPU‑first** |
| Evaluation | R‑Bench / PAI‑Bench scoring + MuJoCo validator | **CPU‑first** |
| Statistics | TOST, Shapiro‑Wilk, Levene, Mann‑Whitney fallback via `scipy.stats` | **CPU‑first** |

## Statistical Rigor

- **Multiple comparisons**: Two benchmarks (R‑Bench, PAI‑Bench) are evaluated, but the primary inferential decision is based on the filtered‑vs‑unfiltered TOST (or Mann‑Whitney fallback). Benchmark‑specific scores are reported descriptively.
- **Power / sample size**: FR‑006 specifies α = 0.05, power ≥ 0.80, d = 0.5 → n ≥ 64 per condition (total ≥ 128). The pipeline guarantees ≥ 64 generated videos per model; if fewer are produced, additional raw videos are fetched before training.
- **Causal framing**: The only systematic manipulation is the post‑generation filter; thus the filtered‑vs‑unfiltered comparison is causally interpretable. The PhysisForcing baseline is **descriptive only** because it differs in architecture, resolution, and training data.
- **Measurement validity**: R‑Bench and PAI‑Bench are used as proxies for physical consistency per FR‑018, supported by prior work (RoboBench 2023). The independent MuJoCo validator provides a direct physics‑simulation construct.
- **Collinearity**: PyBullet and MuJoCo scores are correlated but not identical; SC‑006 explicitly reports the correlation (≤ 0.95) and treats them as related but distinct measures.

## Equivalence Margin & Effect Size (per spec)

- **15 % margin** — FR‑015 (spec‑justified; treated as given).
- **d = 0.5, α = 0.05, power ≥ 0.80 → n ≥ 64 per condition** — FR‑016 (spec‑stated power‑table calculation).

## Assumption Checks & Fallback (FR‑013, FR‑017)

1. **Normality** — Shapiro‑Wilk (α = 0.05).
2. **Homogeneity of variances** — Levene (α = 0.05).
3. **Independence** — guaranteed by design (each video generated once; no augmentation duplicates).

If either assumption fails, the pipeline runs a **Mann‑Whitney U test** (two‑sample non‑parametric) with the same 15 % equivalence margin, reporting the p‑value and equivalence flag.

## Filter Threshold

The curated‑dataset minimum is the **60th percentile** with raw score = 60 (source: 2506.09162, https://arxiv.org/abs/2506.09162), i.e. **normalized threshold 0.60**. Any video with a normalized score < 0.60 is discarded. `filter_discard_percent` (default 40) is recorded for reporting but does not drive selection.

## Go/No‑Go Sanity Gate

Training a 50 M‑parameter video diffusion model for 10 epochs on ≤ ~96 curated 64×64 videos on 2 CPU cores may not yield a model whose generated videos are meaningfully scoreable; without a gate, the downstream TOST could be vacuous. Therefore, after MuJoCo validation (T10) we **verify that at least 80 %** of the generated videos achieve a MuJoCo physics‑consistency score **≥ the 60th‑percentile** of the original uncurated batch (US‑2 scenario 2). If this condition is **not met**, the pipeline **aborts** further evaluation (T12–T15) and **records a null‑result** entry indicating that the filtered dataset did not produce sufficiently consistent samples. **Interpretation of a null result**: the gate failing is itself a legitimate scientific finding — it means sample exclusion alone (post‑generation filtering) did not recover physical consistency at the level achieved by training‑time physics‑informed optimization in the PhysisForcing setting, and the report states this explicitly rather than running an uninterpretable equivalence test. Only when the gate passes do we proceed to benchmark evaluation (T12) and the TOST equivalence test (T13).

## Decision / Rationale Summary

- **Compute**: Everything CPU‑first; optional Kaggle GPU escape only for training if the CPU run fails (real `device="cuda"` re‑run, never a fabricated stand‑in).
- **Data**: Fully open, programmatically downloadable, checksummed; streaming used for the parquet source to respect RAM limits.
- **Video source**: Real Wan2.1 outputs from the verified Rapidata dataset, filtered for manipulation content — honest and executable; local Wan2.1 inference is infeasible and therefore omitted (spec kickback flagged above).
- **Sample size**: n ≥ 64 per condition enforced by fetching additional raw videos if needed.
- **Statistical rigor**: Primary equivalence test is filtered vs. unfiltered; PhysisForcing baseline is reported descriptively; assumptions are diagnosed; fallback non‑parametric test is appropriate for independent samples; go/no‑go gate prevents a vacuous TOST.

## Quickstart Alignment

All steps from acquisition → filtering → training → video generation → evaluation → statistical testing are captured in `quickstart.md`, ensuring end‑to‑end reproducibility on a fresh runner. The go/no‑go gate (`src/evaluation/check_gate.py`) is explicitly documented there as well.
# Research: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

## Overview
We will empirically assess the **subspace sufficiency hypothesis** (US‑1) and the **OPD‑specific geometric advantage hypothesis** (US‑2) using the GSM8K benchmark. The methodology follows the functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑006) laid out in the specification.

## Decision / Rationale
- **Compute platform**: CPU‑first on GitHub Actions (several vCPU, adequate RAM). All components (model loading, training, SVD) have efficient CPU implementations; no GPU is required. This satisfies US‑3 and the Constitution’s Extreme Resource Constraints clause.
- **Dataset**: GSM8K is openly available via the verified URLs (see “Verified datasets” block). We will download the parquet files directly using `datasets.load_dataset(..., streaming=False)` to obtain the full test set (approximately a few GB) and stream the training split if needed.
- **Model**: TinyLlama‑1.1B quantized to 4‑bit GGML via `llama-cpp-python` (CPU‑compatible) to keep memory < 7 GB.
- **Statistical methods**:
 - **Power analysis** (FR‑009) performed separately for OPD and SFT experiments using `statsmodels.stats.power.TTestIndPower`. For OPD we use σ = 0.015 (He 2023). For SFT we estimate σ from a pilot run of multiple seeds; if the pilot cannot be completed we conservatively assume σ = 0.020. If the computed power for any test is **< 0.80**, the result is flagged **“inconclusive”** (FR‑011).
 - **Paired TOST equivalence test** (FR‑006) with Δ = 0.02, α = 0.05 (both one‑sided p‑values < 0.05). The pairing is by seed, because each seed uses the same initialization and data shuffling across conditions.
 - **Paired two‑sample t‑test** for SFT comparisons (OPD‑mask vs. baseline, Random‑mask vs. baseline) (FR‑006). The pairing is again by seed, providing greater power and correctly accounting for within‑seed correlation.
 - **Multiple‑comparison correction**: Not needed (single primary equivalence test and a single paired comparison per mask). If future extensions add tests, a Bonferroni correction will be applied.
- **Randomness control**: Seeds beginning with the initial seed up to the designated upper limit are used across all runs.; the same seed is applied to model initialization, data shuffling, and mask generation (both OPD‑derived and random masks). The random mask is generated once with a fixed seed (`mask_seed = 9999`) and stored as `mask_random.json`; the same mask is reused across all runs for the Random control.
- **Resource monitoring**: `src/utils/resource_monitor.py` records maximum VmRSS (via `/proc/self/status`) and wall‑clock time for each script; CI asserts the limits.

## Dataset Strategy
| Role | Dataset | Source URL (verified) | Loader | Subset / Split |
|------|---------|-----------------------|--------|----------------|
| Primary benchmark (train) | GSM8K training split | ` | `datasets.load_dataset("parquet", data_files=..., split="train")` | Full training set |
| Primary benchmark (test) | GSM8K test split | ` | `datasets.load_dataset("parquet", data_files=..., split="test")` | Full test set |
| Held‑out generalization subset | Stratified subset of test set (by difficulty) | Same test URL (stratified sampling performed locally) | ```python\nimport pandas as pd\nfrom datasets import load_dataset\n\nds = load_dataset('parquet', data_files='data/raw/gsm8k_test.parquet', split='test')\n# Compute difficulty as number of reasoning steps in the reference solution\n\ndef count_steps(example):\n return len(example.get('steps', []))\n\nds = ds.map(lambda x: {'difficulty': count_steps(x)})\n# Stratify by difficulty categories (easy/medium/hard) and sample a representative proportion overall\ntrain, heldout = ds.train_test_split(test_size=0.2, stratify_by='difficulty')\n``` | Held‑out generalization subset used for all evaluation |
| SVD reference (optional) | Not required; placeholder URLs listed in spec are unrelated to GSM8K and will not be used. | — | — | — |

**Difficulty definition**: Difficulty is operationalized as the number of reasoning steps in the reference solution (the `steps` field in GSM8K). We compute the step count for each example and use it as a categorical variable to stratify the held‑out subset, ensuring balanced representation of easy, medium, and hard problems.

*No other external datasets are needed; all URLs are from the verified list.*

## Statistical Analysis Plan
1. **Power Calculation** (pre‑test)
 - **OPD baseline**: Input σ = 0.015 (He 2023).
 - **SFT masked experiments**: Estimate σ from a pilot of several seeds; if unavailable, assume σ = 0.020.
 - Compute achieved power for each test (N = 30 seeds). If power < 0.80, flag the corresponding result as **inconclusive** (FR‑011).

2. **Paired TOST Equivalence** (US‑1)
 - For each seed, compute the accuracy of the Full‑OPD baseline and the Frozen‑Subspace OPD on the held‑out generalization subset.
 - Perform lower‑bound test (H0: μ_frozen ≤ μ_full − Δ) and upper‑bound test (H0: μ_frozen ≥ μ_full + Δ) using the **paired differences** across seeds.
 - Declare equivalence if both one‑sided p‑values `< 0.05`. Report achieved power.

3. **Paired two‑sample t‑test** (US‑2)
 - Compare Frozen‑Subspace SFT vs. Full‑OPD baseline (paired by seed).
 - Compare Frozen‑Subspace Random vs. Full‑OPD baseline (paired by seed).
 - Report mean accuracy drop (percentage points) and two‑sided p‑value. Accept hypotheses per SC‑002 (drop < 3 pp & p > 0.05 for OPD‑mask; drop ≥ 3 pp & p < 0.05 for random mask).

4. **Loss‑Plateau Detection** (FR‑010)
 - For each run, compute epoch‑wise loss; define plateau as Δloss < 0.001 over two consecutive epochs.
 - Record the epoch at which plateau first occurs.
 - Verify that Frozen‑Subspace SFT plateaus within the early training epochs. and Full‑OPD does not plateau until a sufficiently advanced training epoch. (US‑2).

5. **Multiple‑Comparison Adjustment**
 - Not needed because each hypothesis is tested once per mask type; however, the plan notes the decision and will apply a Bonferroni correction if future extensions add tests.

## Edge‑Case Handling
| Edge case | Detection | Mitigation |
|-----------|-----------|------------|
| SVD requires > 10 % of parameters to explain [deferred] variance | After SVD, compute cumulative variance ratio; if > 0.10 of total parameters needed, log warning and abort equivalence test (report as *insufficient subspace*). |
| Large seed‑to‑seed variability (σ > 0.02) | Compute empirical σ; if exceeds 0.02, flag *high variance* and increase N to 50 seeds (subject to RAM/time limits). |
| Immediate loss divergence in Frozen‑Subspace training | Monitor loss after first step; if loss > 1.5× baseline loss, abort run, log *numerical instability*, and retry with reduced learning rate (factor 0.5). |
| Random mask generation variability | Random mask is generated with a fixed seed (`mask_seed = 9999`) and stored as `mask_random.json`; the same mask is reused across all seeds for the Random control. |
| Power < 0.80 for SFT comparison | Flag the result as **inconclusive** and report the achieved power value; no equivalence claim will be made. |

All warnings are recorded in `logs/edge_cases.json` and included in the final report.

---



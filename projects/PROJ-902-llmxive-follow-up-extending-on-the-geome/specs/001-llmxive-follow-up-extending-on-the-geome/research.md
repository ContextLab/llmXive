# Research: llmXive follow-up – extending “On the Geometry of On‑Policy Distillation”

## Objectives & Hypotheses
| ID | Objective | Hypothesis |
|----|-----------|------------|
| **US‑1** | Verify that the low‑dimensional subspace identified after the first two OPD epochs is sufficient for full‑parameter performance when the rest of the model is frozen. | *Equivalence*: Frozen‑Subspace OPD accuracy ≈ Full‑Parameter OPD accuracy (Δ ≤ 0.02) on a held‑out GSM8K generalization subset. |
| **US‑2** | Test whether the OPD‑identified subspace confers a geometric advantage over a random subspace for standard SFT. | *Geometry*: Frozen‑Subspace SFT does **not** suffer a ≥ 3 % accuracy drop vs. OPD baseline, whereas Random‑Mask SFT does. |
| **US‑3** | Demonstrate that the entire pipeline runs within the CPU‑only free‑tier constraints. | *Feasibility*: Peak RAM ≤ 7 GB, wall‑clock ≤ 6 h per CI job. |

## Dataset Strategy
| Dataset | Source (verified URL) | Role | Split Strategy |
|---------|-----------------------|------|----------------|
| **GSM8K** (questions & answers) | ` | Training & evaluation of OPD & SFT | The **test** split is stratified by problem difficulty (`category`). We further split the test set into: <br>• **Evaluation set** (used for early‑stop monitoring) <br>• **Held‑out generalization subset** (final accuracy & statistical tests). The split uses a fixed random seed (`seed=12345`). |

*No other external datasets are required.*

## Methodology

### 1. Model & Training
* **Base model**: TinyLlama‑430M, loaded with bitsandbytes **8‑bit CPU quantization** (`bnb.nn.Linear8bit`). This runs on CPUs without CUDA.
* **OPD loss**: KL‑divergence between student logits and teacher logits (teacher = same TinyLlama in full precision). Optimizer = AdamW (lr = 5e‑5, weight decay = 0.01).
* **SFT loss**: Cross‑entropy on ground‑truth answers.
* **Training schedule**: **2 epochs**, batch size = 8, deterministic seeding (`torch.manual_seed`, `numpy.random.seed`). Reduced epochs keep each run well under the 6‑hour wall‑clock limit.

### 2. Subspace Identification
* **Parameter trajectory**: For each of the **10** mask‑derivation seeds, collect per‑layer weight deltas `Δθ` after every OPD update step during the first **2** epochs.
* **Randomized SVD**: Implemented per Halko et al. (2011) using `scipy.sparse.linalg.svds` with streaming to keep RAM ≤ 7 GB. Target rank is increased until cumulative variance ≥ 95 % (primary) and also evaluated at [deferred] and [deferred] for sensitivity (SC‑006).
* **Mask creation**: Binary mask per layer where entries corresponding to the selected singular vectors are set to `true`; all others `false`. Stored as JSON `{layer_name: [bool,…]}`.

### 3. Training under Masks
* **Frozen‑Subspace OPD**: Apply the mask; only masked parameters receive gradients.
* **Frozen‑Subspace SFT**: Same mask, but loss is standard SFT.
* **Random‑Mask SFT**: Generate a mask with the same number of active parameters per layer, sampled uniformly at random (seeded).

### 4. Evaluation
* After training, evaluate on the **held‑out generalization subset**, using a sufficiently large sample to assess generalization. Compute **accuracy** (exact match) per seed.

### 5. Statistical Analysis
| Test | Comparison | Metric | Method |
|------|------------|--------|--------|
| **Normality diagnostics** | All seed‑wise accuracy differences | Shapiro‑Wilk, QQ‑plot | If p > 0.05 → assume normal; else fallback to Wilcoxon signed‑rank. |
| **TOST Equivalence** | Frozen‑Subspace OPD vs. Full‑Parameter OPD (paired) | Accuracy difference | Paired TOST, Δ = 0.02, α = 0.05 (or Wilcoxon‑based equivalence if non‑normal). |
| **Paired t‑test / Wilcoxon** | Frozen‑Subspace SFT vs. Full‑Parameter OPD | Accuracy drop | Paired t‑test (α = 0.05) or Wilcoxon signed‑rank if normality fails. |
| **Paired t‑test / Wilcoxon** | Random‑Mask SFT vs. Full‑Parameter OPD | Accuracy drop | Same as above. |
| **Sensitivity sweep** | Same as above across variance thresholds {0.90, 0.95, 0.99} | Accuracy difference | Apply Bonferroni correction (α/3). |

*Power analysis*: Prior to each test, compute required N using `statsmodels.stats.power.TTestPower` with effect size δ (0.02 for OPD, 0.03 for SFT), σ = 0.015 (He 2023), α = 0.05. With **N = 30** seeds, report achieved power; if power < 0.80 (the conventional target), flag the result as **“inconclusive”** (FR‑009, FR‑011, FR‑021).

### 6. Resource Monitoring
* `src/utils/logging.py` records `peak_ram_gb`, `wall_time_sec`, **per‑epoch loss**, `delta_loss`, and `plateau_epoch` (ΔL < 0.001 for two consecutive epochs). All metrics are written to `state.yaml` and validated against `contracts/experiment_results.schema.yaml`.

### 7. CI & Reproducibility
* The GitHub Actions workflow (`.github/workflows/ci.yml`) creates a matrix of jobs:
 - Conditions: `opd_full`, `frozen_opd`, `frozen_sft`, `random_sft`
 - Seeds per job: **≤ 15** (splitting the required 30 seeds across two parallel jobs per condition).
* Each job runs the full pipeline for its assigned seeds, validates the resulting JSON against **both** `contracts/experiment.schema.yaml` **and** `contracts/experiment_results.schema.yaml`. Failures abort the job.
* After all jobs finish, an aggregation step merges per‑run JSON files into a single `state.yaml` artifact and uploads it.

## Compute Feasibility Decision
All heavy computations are **CPU‑first** using 8‑bit quantization on TinyLlama‑430M, which fits comfortably within 7 GB RAM. No GPU is required; the plan therefore stays on the free‑tier runner. If any step unexpectedly exceeds limits, CI will fail and the design will be revisited.

## Expected Deliverables
* `state.yaml` containing:
 * Per‑seed accuracies, RAM, time, loss metrics, plateau epoch.
 * Subspace mask summary (`k`, variance explained).
 * Power analysis results.
 * Statistical test outcomes (p‑values, decisions, “inconclusive” flags).
* Figures (accuracy distributions, loss trajectories, variance‑explained sweep) under `results/figures/`.
* Fully validated CI workflow and contract schemas.

---

## Constitution Check (re‑affirmed)
| Principle | Satisfaction |
|-----------|---------------|
| I. Reproducibility | Deterministic seeds, dataset download, CI matrix. |
| II. Verified Accuracy | Citations pre‑validated; dataset URLs from verified block. |
| III. Data Hygiene | Checksums, no in‑place mutation. |
| IV. Single Source of Truth | All metrics in `state.yaml`. |
| V. Versioning Discipline | Content hashes, pinned dependencies. |
| VI. Geometric Subspace Validation | Paired‑seed TOST and controls with random mask. |
| VII. Extreme Resource Constraints Verification | RAM & time logged; CI enforces limits. |
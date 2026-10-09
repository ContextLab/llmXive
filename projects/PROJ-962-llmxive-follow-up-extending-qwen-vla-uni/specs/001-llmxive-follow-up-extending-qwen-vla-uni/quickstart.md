# Quickstart Guide: Non-Neural Approximation of VLA Priors

## Overview

This guide walks you through the full end‑to‑end CPU‑only pipeline that approximates the Qwen‑VLA model using lightweight Decision‑Tree and Gaussian‑Mixture models. All steps are deterministic, reproducible, and validated against real data from HuggingFace and the verified VLA‑Proxy baseline.

## Prerequisites

- Python 3.11 (or newer)
- `git` and internet connectivity (to download the Qwen‑VLA dataset and VLA‑Proxy baseline)
- At least **7 GB** of RAM (the streaming ingestion path keeps memory usage under the limit)
- No GPU available – the scripts will abort if a CUDA device is detected.

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni

# Create a clean virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install the pinned, CPU‑only dependencies
pip install -r code/requirements.txt
```

## Pipeline Execution

The pipeline consists of **four** sequential stages. Each stage writes its artifacts under `data/` or `artifacts/models/`. All flags are shown with their default values; you may override them as needed.

### 1️⃣ Ingestion & Clustering

```bash
python code/01_ingest_cluster.py \
  --dataset qwen-vla/Hy-Embodied \
  --output-dir data/processed \
  --silhouette-threshold 0.25 \
  --k-reduction-step 1 \
  --max-iterations 50 \
  --download               # forces dataset download; will fail loudly if unreachable
```

**Outputs**
- `data/processed/streaming_stats.json` – global mean / std for streaming normalization (Welford)
- `data/processed/clustering_state.json` – final `k`, silhouette score, method used
- `data/processed/clusters.json` – cluster centroids
- `data/processed/assignments.parquet` – per‑sample cluster IDs
- `data/results/coverage_report.json` – clustering coverage (≥ 0.98 required)

---

### 2️⃣ Model Training (Decision Tree → GMM fallback)

```bash
python code/02_train_models.py \
  --embeddings data/processed/train_embeddings.parquet \
  --assignments data/processed/assignments.parquet \
  --clusters data/processed/clusters.json \
  --output-dir artifacts/models \
  --r2-threshold 0.6 \
  --inference-time-threshold 2.0 \
  --seed 42
```

**Key behaviours**
- Enforces **CPU‑only** execution (exits if `torch.cuda.is_available()`).
- Runs the **Construct Validity Gate** (R² ≥ 0.1) before any model is trained.
- For each cluster:
  1. Trains a Decision Tree (RandomForestRegressor) first.
  2. If the tree meets both `R² ≥ 0.6` **and** inference time `< 2 s/prompt`, it is selected.
  3. Otherwise a Conditional Gaussian Mixture Model (CGMM) is trained and evaluated.
  4. If neither meets the thresholds, the model with the highest R² is kept and a warning is logged.

**Outputs**
- `artifacts/models/cluster_{id}_selected.pkl` – the chosen model (DT or GMM) for each cluster.
- `artifacts/models/cluster_{id}_selection.json` – selection criteria (R², inference time, model type).
- `data/results/model_selection_decision.md` – narrative rationale (see `research.md` for the full description).
- `data/results/hypothesis_failure_report.md` – created only if the Construct Validity Gate fails.

---

### 3️⃣ Inference & Simulation

```bash
python code/04_simulate_eval.py \
  --models-dir artifacts/models \
  --baseline data/processed/vla_proxy_baseline.parquet \
  --output-dir data/results \
  --seed 42
```

**What happens**
1. Generates BERT embeddings for the test prompt set (the same IDs as the VLA‑Proxy baseline).
2. Runs the **non‑neural inference engine** to obtain trajectories.
3. Generates a **random baseline** (uniform sampling within joint limits) using the fixed seed.
4. Executes all three trajectory sets (non‑neural, random, VLA‑Proxy) in a Mock PyBullet environment.
5. Records success/failure, collision counts, and execution time.
6. Verifies that prompt IDs are **identical** across the three baselines (paired‑test requirement).
7. Performs **paired t‑tests** on:
   - Continuous fidelity scores
   - Binary success flags

**Outputs**
- `data/results/simulation_logs.csv` – per‑prompt results (success, collisions, timestamps)
- `data/results/fidelity_scores_per_sample.json` – continuous fidelity metrics
- `data/results/statistical_test_results.json` – p‑values and significance flags (α = 0.05)
- `data/results/memory_profile_e2e.json` – peak and average RAM usage (≤ 7 GB)

---

### 4️⃣ Final Report Generation

```bash
python code/08_generate_report.py \
  --results-dir data/results \
  --models-dir artifacts/models \
  --output data/results/evaluation_report.md
```

The report aggregates clustering coverage, model‑selection statistics, simulation fidelity, and statistical‑test outcomes. It also computes the **complexity reduction factor** (parameter count of VLA‑Proxy vs. the selected non‑neural model) and flags significance according to α = 0.05.

---

## End‑to‑End Validation

For a single‑command run that executes all four stages and writes a full log, use:

```bash
python code/09_run_final_validation.py \
  --dataset qwen-vla/Hy-Embodied \
  --baseline data/processed/vla_proxy_baseline.parquet \
  --output-dir data/results \
  --seed 42
```

The script produces `data/results/final_validation.log` and checks that **all** expected artifacts (16 files) are present, mirroring the summary in `data/results/final_validation_summary.json`.

## Troubleshooting

- **Dataset download fails** → Verify internet access; the script will raise a clear `DataFetchError`.
- **GPU detected** → Set `CUDA_VISIBLE_DEVICES=""` or uninstall the GPU‑enabled PyTorch build; the training script aborts with `RuntimeError: CPU‑only constraint violated`.
- **Clustering coverage < 0.98** → A warning is logged, but the pipeline proceeds; you may increase `--k-reduction-step` or lower the silhouette threshold.
- **Model selection warnings** → Check `data/results/model_selection_decision.md` for per‑cluster R² and inference‑time details.

## References

- Qwen‑VLA dataset on HuggingFace: `qwen-vla/Hy-Embodied`
- VLA‑Proxy baseline: `qwen-vla/vla-proxy-trajectories`
- Scikit‑Learn, Transformers, PyBullet, Datasets library

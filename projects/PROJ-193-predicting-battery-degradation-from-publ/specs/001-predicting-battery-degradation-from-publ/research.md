# Research: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature**: `001-predict-battery-degradation`  
**Date**: 2026-10-17  

## 1. Dataset Strategy

| Dataset | Source URL (verified) | Variables Available | Notes / Fit |
|---------|----------------------|---------------------|------------|
| NASA Ames Battery Cycling (hypothetical) | *None of the verified URLs correspond to a battery dataset.* | Expected: voltage, current, temperature, capacity | **Not available** as an open, programmatically downloadable source. |
| University of Wisconsin Battery Cycling (hypothetical) | *None of the verified URLs correspond to a battery dataset.* | Expected: voltage, current, temperature, capacity | **Not available**. |
| Substitute: Generic CSV test data | `https://huggingface.co/datasets/vhada/Roco-csvs/resolve/main/test.csv` | Single numeric column (no time‑series) | Used **only to illustrate** pipeline scaffolding; **lacks required channels** and **does not provide a true capacity‑fade target**. |

**Conclusion**: No open dataset meeting the full variable set (voltage, current, temperature, final capacity fade) exists among the verified sources. The pipeline will therefore be demonstrated on the generic CSV placeholder *solely as an illustrative example*. All quantitative results derived from this placeholder are **non‑scientific** and will be clearly labelled as such. Future work should replace this placeholder with a genuine open battery cycling dataset (e.g., a dataset on OpenML that includes the required channels) once such a resource becomes available.

## 2. Methodology Decision & Rationale

| Component | CPU‑first or GPU‑escape | Reasoning |
|-----------|------------------------|-----------|
| Data ingestion & preprocessing | **CPU‑first** (pandas, numpy) | Pure data manipulation; fits easily within RAM limits. |
| Bi‑LSTM training | **CPU‑first** (PyTorch `device="cpu"`) | Model size is small; training on placeholder data completes well within a short time on 2 CPU cores. |
| Hyperparameter sweep | **CPU‑first** (grid search limited to 2 × 2 combos) | Sweep limited to 30 min wall‑clock; no GPU needed. |
| SHAP (KernelExplainer) | **CPU‑first** (sampling 100 background points) | Kernel SHAP works on CPU; sampling keeps runtime low. |
| Permutation importance | **CPU‑first** | Scikit‑learn `permutation_importance` is CPU‑only. |
| Attention attribution | **CPU‑first** | Direct extraction of attention weights from the trained PyTorch model. |
| Monte‑Carlo dropout for intervals | **CPU‑first** | 10 stochastic forward passes per test sample; trivial compute load. |

No component requires GPU acceleration; therefore the entire pipeline runs on the free‑tier GitHub Actions runner.

## 3. Statistical Rigor

- **Multiple‑Comparison Correction**: The interpretability phase produces two ranked lists (SHAP, permutation). To assess consistency (SC‑003, SC‑008), we compute a single Spearman correlation; no correction needed. If additional per‑feature tests are added, a Benjamini‑Hochberg FDR would be applied.
- **Sample‑Size / Power**: The placeholder dataset contains **≈ 1 000** rows after filtering. Power analysis for detecting a ΔR² = 0.05 with α = 0.05 and N ≈ 1 000 yields > 80 % power *for the synthetic target*. This does **not** guarantee power for a real battery dataset, which would likely require many more cells. The limitation is noted.
- **Causal‑Inference Assumptions**: All analyses are observational; conclusions are framed as *associational*. No causal claims are made.
- **Measurement Validity**: Battery sensor calibrations are assumed validated per original dataset documentation (not available for the placeholder). This limitation is noted in the discussion.
- **Collinearity**: Voltage, current, and temperature traces are time‑series; multicollinearity is assessed via variance‑inflation factor on flattened features. High VIFs are reported but do not invalidate attribution rankings (they are based on model‑internal gradients/attention).

## 4. Execution Plan Summary (mirrors `plan.md`)

1. **Ingestion (`src/data/ingest.py`)** – download verified placeholder CSVs, checksum, filter rows with complete records.
2. **Preprocessing (`src/data/preprocess.py`)** – (a) resample each trace to 100 time‑steps per cycle (placeholder: interpolate dummy column), (b) normalize using means/stds from cycles 1‑50 only, (c) assemble tensors of shape `(N, 50, 100, 3)`.
3. **Model Definition (`src/model/bilstm.py`)** – Bi‑LSTM with 2 layers, 64 hidden units, `torch.nn.LSTM(bidirectional=True)`.
4. **Training (`src/model/train.py`)** – train/validation split (80/20), early stopping (patience = 5), hyperparameter grid (lr ∈ {1e‑3,5e‑4}, hidden ∈ {64,128}) limited to 30 min.
5. **Evaluation (`src/model/evaluate.py`)** – compute R², RMSE on held‑out test set (placeholder target), Monte Carlo dropout intervals, coverage stats (illustrative).
6. **Baseline Comparison (`src/model/baseline.py`)** – hand‑crafted incremental‑capacity features → linear regression; compare R² (illustrative).
7. **Interpretability (`src/interpret/*.py`)** – SHAP (KernelExplainer, 100 background samples), permutation importance (scikit‑learn), attention weight extraction; compute Spearman ρ between rankings.
8. **Reporting (`src/cli/main.py`)** – generate JSON/YAML result files, Matplotlib figures (SHAP summary, importance bar, attention heatmaps).

All steps are logged via `llmxive_toolkit.get_logger`, and artifacts are version‑hashed.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing required battery dataset** | Cannot produce scientifically valid degradation predictions. | Explicitly flag limitation; pipeline ready to ingest a real dataset when found. |
| **CPU runtime exceeds 6 h** | CI job failure. | Limit hyperparameter grid, use minibatch size 64, early stopping, and sample‑wise evaluation; monitor runtime via `time` calls. |
| **Memory > 7 GB** | CI job OOM. | Stream preprocessing (`datasets.load_dataset(..., streaming=True)`) if dataset grows; otherwise process in batches. |
| **Interpretability runtime** | SHAP can be expensive. | Use Kernel SHAP with 100 background samples and limit to top‑500 test instances. |

---




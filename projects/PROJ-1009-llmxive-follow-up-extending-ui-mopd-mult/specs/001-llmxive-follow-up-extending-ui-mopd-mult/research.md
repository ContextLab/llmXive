# Research: llmXive follow-up: extending "UI-MOPD: Multi-Platform On-Policy Distillation for Continual GUI Agent"

**Feature**: `001-gui-topology-transfer`
**Date**: 2026-10-20

## Objective
Validate, via a clearly-labeled simulation study, the analysis pipeline for quantifying how non-visual structural topology (widget depth, branching factor, navigation-graph connectivity) relates to task-success prediction, and evaluate whether a lightweight structural adapter can match a simulated UI-MOPD baseline's success rate while delivering ≥ 5× latency reduction.

## Spec Scope Mismatch (flagged for kickback)
FR-001/US-1/SC-000 require extraction from **Uni-GUI logs**, and the spec assumes reproducible UI-MOPD baseline metrics. No verified open download of Uni-GUI logs exists, and no open dataset provides GUI-agent execution success paired with widget-tree/navigation-graph structure. This study therefore uses a **simulated** dataset and a **simulated** baseline; the outcome variable is NOT a valid proxy for real cross-platform policy transfer success, and the core research question is **not answered** here — it is deferred until the spec is revised to sanction either a simulation scope or a named obtainable dataset.

## Dataset Strategy
| Role | Dataset | Access Method | Verified URL | Notes |
|------|---------|----------------|--------------|-------|
| Primary (simulated structural features + noisy outcomes) | **Simulated UI-Topology Dataset** (`src/generate/synthetic_dataset.py`) | `python -m src.generate.synthetic_dataset --num-records 10000 --seed 42` | N/A (generated on-the-fly) | [deferred] records (SC-000). Creates widget_depth, branching_factor, graph_connectivity, platform_id, a random control feature, and a binary task_success label from a logistic model **with calibrated independent noise** (see Anti-circularity). |
| Baseline UI-MOPD policy heads | Local simulated artifacts | `pathlib.Path("data/artifacts/policy_heads/")` | N/A (internal) | Simulated from the same generative model to enable paired observations for McNemar's test; validity limited to the simulated setting. |
| Baseline latency & success benchmarks | Simulated baseline metrics | `data/baseline/simulated_ui_mopd_metrics.csv` | N/A | Checksum-validated; represents the "heavy" baseline on the simulated test set only. |

## Anti-circularity design
The simulated label is `task_success ~ Bernoulli(sigmoid(β0 + Σ βi Xi + ε))`. Because the label is derived from the predictors, results cannot support the real-world claim. To keep evaluation informative:
1. **Noise sweep**: ε is calibrated across levels so the Bayes-optimal AUC spans ≈ 0.55 (near-uninformative) to ≈ 0.85. All metrics are reported across the sweep, including levels where FR-002 thresholds fail.
2. **Shuffled-label null control**: labels are permuted to destroy predictor–outcome association; the resulting AUC/Brier form the empirical null against which FR-002 thresholds are interpreted.
3. **Random control feature**: a noise feature is included; its SHAP/permutation importance must be near zero, verifying the importance machinery.

## Power Analysis
Using `statsmodels.stats.power.NormalIndPower` for a two-sample AUC comparison (ΔAUC = 0.05, α = 0.05, power = 0.80) with Bonferroni correction for three predictors yields a minimum N on the order of several thousand. We generate **[deferred]** records (SC-000) to satisfy this and allow stratified splits.

## Decision / Rationale
- **Compute**: All modeling uses CPU-only PyTorch (`torch.device('cpu')`). The GNN (2-layer GraphSAGE, 32 hidden units) fits the RAM budget on the full simulated dataset; if memory spikes, the pipeline falls back to a stratified random sample and a linear regression model (FR-008).
- **Statistical Methods**
  - **Model evaluation**: AUC-ROC and Brier score reported per noise level and against the shuffled-label null (FR-002 thresholds are simulation-conditional).
  - **Feature importance**: SHAP (KernelExplainer) and permutation importance, including the control feature; Bonferroni correction across tests (FR-007).
  - **Sensitivity sweeps**: depth ∈ {3,4,5}, branching_factor ∈ {1.0,1.5,2.0}, graph_connectivity ∈ {0.3,0.5,0.7}; variance of overall success rate reported (SC-006).
  - **Benchmark**: per-step inference latency (`time.perf_counter`) and peak RSS (`psutil`).
  - **Statistical comparison**: McNemar's test on paired binary outcomes, p < 0.05 (SC-005).
  - **Variation evaluation (FR-009)**: adapter evaluated on shuffled-widget-order and altered-resolution variants; degradation reported vs original test set (SC-007).
- **Confounder control**: `platform_id` one-hot covariate; evaluation stratified by platform.
- **Causal framing**: this is a simulation; no causal or real-world associational claim about cross-platform transfer is made.

## Expected Deliverables
1. **`data/derived/structural_records.csv`** – cleaned, checksum-verified table (widget_depth, branching_factor, graph_connectivity, platform_id, task_success, control_feature, structural_ambiguity).
2. **Model artifact** – `outputs/adapter_gnn.pt` (or `adapter_linear.pkl`).
3. **`outputs/feature_importance.csv`** – SHAP + permutation, Bonferroni-adjusted, including control feature.
4. **`outputs/benchmark.csv`** – latency, memory, success rate, McNemar p-value, variation-degradation metrics.
5. **`outputs/adapter_output.csv`** – validated against `contracts/structural_record.schema.yaml`-style contract checks.
6. **Sensitivity figures** – `outputs/sensitivity_*.png`.
7. **Reproducibility manifest** – artifact hashes, seeds, runtime logs in `state/projects/...yaml`.
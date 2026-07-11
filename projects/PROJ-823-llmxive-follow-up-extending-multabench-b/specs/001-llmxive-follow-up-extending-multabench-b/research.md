# Research: llmXive Follow-up: Extending MulTaBench

## 1. Problem Statement & Research Questions

**Primary Question**: Can a lightweight, tabular-conditioned projection module recover the performance gap between a frozen multimodal encoder (CPU) and a fine-tuned multimodal encoder (GPU) on the MulTaBench dataset?

**Secondary Question**: Which structural properties of the tabular data (cardinality, missingness, sparsity, variance) correlate with the efficacy of this recovery mechanism?

**Hypothesis**: Tabular features contain sufficient task-specific signal to modulate frozen unstructured embeddings, yielding a "Recovery Ratio" significantly greater than zero. The efficacy is expected to vary with tabular complexity (e.g., higher cardinality may provide stronger conditioning signals).

## 2. Dataset Strategy

### 2.1 Target Dataset: MulTaBench
The project relies on the **MulTaBench** dataset (arXiv:2605.10616), which contains 40 multimodal tabular datasets with associated text and image modalities.

*   **Verified Source Status**: **UNVERIFIED (Local Artifact Required)**.
    *   **Action Plan**: No public URL exists in the verified dataset block. The implementation assumes the dataset is available locally via the MulTaBench supplementary material or a private repository as per the spec's "Assumption about data availability".
    *   **Data Hygiene Requirement**: The user MUST provide the SHA-256 checksum of the MulTaBench archive in `data/README.md`. The `data_loader.py` will verify this checksum against the local file before proceeding. If the checksum fails, the pipeline aborts.
    *   **Known Limitation**: Reproducibility is conditional on the user providing the correct local artifact. This is a known limitation of the study due to the lack of a public URL.
*   **Data Availability Gaps**: The plan explicitly handles cases where the "GPU-Tuned" baseline is missing for specific datasets (as noted in Edge Cases). These will be flagged and excluded from the primary correlation analysis.

### 2.2 Baseline Data (GPU-Tuned)
*   **Source**: MulTaBench supplementary material (paper).
*   **Status**: **NO verified source found** for a direct download URL.
*   **Handling**: The "GPU-Tuned" metrics will be treated as a static lookup table (JSON/CSV) embedded in the code or loaded from a `data/gpu_baselines.json` file. The plan does not attempt to re-run the original GPU training.

### 2.3 Derived Data
*   **Frozen Embeddings**: Generated locally via `code/embeddings/generator.py`.
*   **Tabular Metadata**: Computed locally via `code/analysis/metadata_stats.py`.

## 3. Methodology & Statistical Rigor

### 3.1 Frozen Embedding Generation (FR-001)
*   **Models**:
    *   **Images**: CLIP ViT-B/32 (pre-trained, frozen).
    *   **Text**: Sentence-BERT (pre-trained, frozen).
*   **Constraints**:
    *   **Device**: CPU only.
    *   **Gradient**: `torch.no_grad()` enforced for backbone.
    *   **Precision**: Default FP32 (no 8-bit quantization to avoid CUDA dependencies).
    *   **Batching**: Max batch size to prevent OOM on available RAM.
*   **Reproducibility**: `random_seed=42` set for all random operations (tokenization, batching order).
*   **Traceability**: A global `run_id` is generated at the pipeline start and injected into every `FrozenEmbedding` parquet file to ensure traceability to the final metrics.

### 3.2 Tabular-Conditioned Projection (FR-002)
*   **Architecture**: Lightweight MLP or Single-Head Attention.
    *   Input: Normalized tabular features (query) + Frozen embedding (value/key).
    *   Output: Modulated embedding vector.
*   **Training**:
    *   **Optimizer**: AdamW (default learning rate).
    *   **Epochs**: 15 (max) with **Early Stopping** (patience=5, min_delta=0.0001) to ensure convergence without arbitrary loss thresholds.
    *   **Constraint**: Backbone weights remain frozen. Only projection weights updated.
    *   **Memory Check**: Peak RAM monitored; if >7GB, batch size reduced dynamically.
*   **Verification**: A unit test `tests/test_projection.py::test_frozen_backbone_gradients` verifies that no gradients flow to the backbone weights.

### 3.3 Statistical Analysis (FR-003, FR-005, FR-006)
*   **Recovery Ratio**:
    $$ R = \frac{P_{cond} - P_{frozen}}{P_{gpu} - P_{frozen}} $$
    Where $P$ is the performance metric (AUC for classification, RMSE/MAE for regression).
    *   *Note*: $P_{frozen}$ is the **re-computed** baseline from this pipeline.
    *   *Definition*: $P_{frozen}$ is calculated by training a lightweight Logistic Regression/MLP head **ONCE** on the frozen embeddings using `random_seed=42`, then freezing the head weights. This resolves the "frozen vs trained" contradiction.
    *   *Sensitivity*: To account for variance in $P_{frozen}$, the head training is repeated with 5 seeds: `[42, 123, 456, 789, 101]`. The final $P_{frozen}$ used in the Recovery Ratio is the **mean** of these 5 runs. The variance is used to construct error bars in the correlation analysis.

*   **Correlation Analysis**:
    *   **Metric**: Pearson correlation coefficient ($r$) between $R$ (mean of 5 seeds) and metadata features (Cardinality, Missingness, Sparsity, Variance).
    *   **Power Limitation**: With N ≤ 40, the study is underpowered to detect small effects (r < 0.3). The analysis will prioritize **Effect Size** (Cohen's d) and **95% Bayesian Credible Intervals** over binary p-value significance.
    *   **Correction**: Benjamini-Hochberg (FDR) procedure applied to the family of 4 correlations ($\alpha \le 0.05$).
    *   **Assumption**: Observational study. Claims are associational. No causal inference.

*   **Significance Testing**:
    *   **Test**: **Bootstrap Permutation Test** (10,000 resamples) comparing the distribution of $(P_{cond} - P_{gpu})$ against zero. This avoids the error of treating the literature-based $P_{gpu}$ as a population parameter with zero variance.
    *   **Result**: Report the p-value from the permutation test and the 95% Confidence Interval of the mean difference.

## 4. Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Runner (standard CPU allocation, ~7GB RAM, ~14GB Disk).
*   **Time Limit**: 6 hours total.
    *   **Embedding Gen**: Target ≤ 60 mins (batched processing).
    *   **Training/Eval**: Target ≤ 5 hours (lightweight MLP, 5 seeds for sensitivity).
*   **Memory**:
    *   **Strategy**: Process datasets sequentially.
    *   **Batch Size**: Max 8 images/text samples per forward pass.
    *   **Garbage Collection**: Explicit `gc.collect()` and `torch.cuda.empty_cache()` (though no GPU) after each dataset.
*   **Libraries**:
    *   `torch`: CPU wheel only (no `cu118`).
    *   `transformers`: Standard CPU build.
    *   `sentence-transformers`: CPU build.
    *   `scikit-learn`: Standard.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MulTaBench data missing locally | Pipeline fails | `data_loader.py` checks for file existence and SHA-256 checksum; fails with clear error. |
| "GPU-Tuned" baseline missing for a dataset | Cannot compute Recovery Ratio | Exclude from correlation analysis; list in "Data Availability Gap" report. |
| OOM on large images | CI job killed | Batch size reduced to 1; if still OOM, skip dataset and log warning. |
| Low variance in tabular features | Correlation undefined | Skip feature in analysis; report "Zero Variance" in metadata stats. |
| Low Statistical Power (N<=40) | False negatives | Report Bayesian Credible Intervals and Effect Sizes; acknowledge limitation in final report. |
| Baseline Variance (P_frozen) | Invalid correlation | Use 5-seed sensitivity analysis to estimate and propagate variance in the Recovery Ratio. |
# Implementation Plan: VLM Proxy Dimension Mimicry & Bias Characterization

**Branch**: `PROJ-899-vlm-proxy-mimicry` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-evalverse-pi/spec.md`

## Summary
This plan implements a CPU-tractable pipeline to determine which **VLM-generated scores** in the **verified VLM proxy datasets** (VLM_SingleAction2, vlm_split, vlmsareblind) are predictable by low-level features (optical flow, audio). The study explicitly reframes the goal as **"VLM Bias Characterization"** (measuring the extent to which VLM scores rely on low-level cues) rather than "Human Viability," acknowledging that the ground truth is VLM output and that the datasets contain **action-based** scores, not "cinematic dimensions." The approach calculates Pearson/Spearman correlations with bootstrapped 95% CIs using `scipy.stats.bootstrap`, validates against Mean/Shuffled baselines, and performs a full sensitivity analysis on the correlation threshold. All execution is constrained to a limited number of CPU cores, ~7GB RAM, and 6 hours, utilizing streaming for dataset access. The sample size N is dynamically determined by the available clips in the verified datasets.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (streaming), `scipy` (bootstrap), `pandas`, `numpy`, `scikit-learn`, `librosa` (audio), `opencv-python` (video), `pyarrow`, `statsmodels` (FDR), `tracemalloc`.  
**Storage**: Local scratch space for streaming shards; `data/processed/` for final artifacts (CSV/JSON).  
**Testing**: `pytest` with contract validation against YAML schemas.  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, ~7GB RAM).  
**Project Type**: Data Analysis Pipeline / CLI Tool.  
**Performance Goals**: Process **all available clips (N = dynamic)** within 6 hours; Peak RAM < 6.5GB (safety margin).  
**Constraints**: CPU-only (no CUDA); Streaming mode mandatory; No hardcoded metrics (all derived from real computation); **No synthetic data**.  
**Scale/Scope**: Verified VLM proxy datasets (N determined at runtime, expected to be within a moderate range); Dimensions discovered dynamically (Action-based).

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility (Principle I)**:
    *   **Action**: `requirements.txt` will pin exact versions. All scripts will accept a `--seed` argument (default `42`).
    *   **Action**: External data fetched via `datasets.load_dataset(..., streaming=True, trust_remote_code=True)` from verified HuggingFace URLs only.
    *   **Action**: No random data generation; all results derived from the real verified dataset stream.

2.  **Verified Accuracy (Principle II)**:
    *   **Action**: **All citations in `plan.md` and `research.md` will strictly reference the "Verified datasets" block provided in the prompt.** No fabricated URLs.
    *   **Action**: The plan explicitly acknowledges the "VLM Mimicry" nature of the study and does not claim human ground truth.
    *   **Action**: A pre-commit check will scan `plan.md` for any URLs not in the verified block.

3.  **Data Hygiene (Principle III)**:
    *   **Action**: Raw data is never modified. Derived artifacts (`correlations.csv`, `baseline_results.csv`, etc.) are written to `data/processed/` with new filenames.
    *   **Action**: PII scan will be run on `data/` artifacts before commit.

4.  **Single Source of Truth (Principle IV)**:
    *   **Action**: `data/processed/dimension_viability.csv` will be the *only* source for the "VLM-Reliance-High" classification. The paper generation step will read directly from this file.
    *   **Action**: The `confidence` column in the data model is handled explicitly: "low" confidence (CI lower < 0.85 but point estimate > 0.85) results in a classification of "VLM-Reliance-Low" or "Ambiguous", **not** "feature-sufficient". This ensures the binary classification logic remains unambiguous.

5.  **Versioning Discipline (Principle V)**:
    *   **Action**: The pipeline will compute SHA-256 hashes for every input shard and output file, recording them in `state/.../artifact_hashes`.

6.  **Low-Level Feature Fidelity (Principle VI)**:
    *   **Action**: Correlation logic explicitly separates "optical flow magnitude" from "audio spectral centroid".
    *   **Action**: The threshold is applied *only* to the calculated Pearson r, not hardcoded in decision logic without the calculation.

7.  **Resource-Constrained Validation (Principle VII)**:
    *   **Action**: `src/data/profiles.py` will implement memory tracking (`tracemalloc`) per clip.
    *   **Action**: If a single clip exceeds 50MB RAM, the pipeline will abort with a "Constraint Violation" error.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-evalverse-pi/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── correlation_result.schema.yaml
    ├── baseline_result.schema.yaml
    ├── permutation_result.schema.yaml
    ├── profiling_result.schema.yaml
    └── viability_result.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── loader.py          # Streaming dataset loading
│   ├── profiles.py        # Memory/CPU profiling logic (outputs profiling_logs.json)
│   └── extractors.py      # Optical flow, audio feature extraction
├── models/
│   ├── metrics.py         # Correlation, bootstrap, permutation tests, FDR
│   └── evaluate.py        # Baseline calculations (Mean, Shuffled)
├── cli/
│   └── run_pipeline.py    # Orchestration: Load -> Extract -> Correlate -> Report
├── reports/
│   └── generate.py        # Final viability report generation
└── utils/
    └── config.py          # Seed, threshold, and path configuration

tests/
├── contract/
│   └── test_schemas.py    # Validates output CSVs against YAML schemas
├── integration/
│   └── test_pipeline.py   # End-to-end small sample run
└── unit/
    └── test_metrics.py    # Unit tests for bootstrap logic

data/
├── raw/                   # (Empty, streaming only)
└── processed/
    ├── scores.csv                 # Input: VLM scores (extracted from stream)
    ├── correlations.csv           # Output: Correlation results
    ├── baseline_predictions.csv   # Output: Baseline metrics (RMSE, R2)
    ├── permutation_raw.csv        # Output: Raw permutation results
    ├── max_t_stats.csv            # Output: Max-T aggregated stats
    ├── permutation_results.csv    # Output: FDR corrected p-values
    ├── dimension_viability.csv    # Output: Final classification
    ├── profiling_logs.json        # Output: Memory/time logs
    ├── batch_raw_logs.json        # Output: Batch processing logs
    ├── sensitivity_matrix.json    # Output: Sensitivity analysis matrix
    └── scaling_projection.json    # Output: Linear scaling projection
```

**Structure Decision**: Single project structure selected to minimize overhead and maximize memory efficiency for the 7GB constraint. All processing is pipelined (stream -> extract -> aggregate) to avoid holding the full dataset in memory.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Streaming Architecture | Verified datasets may exceed 7GB RAM. | Loading the full dataset would cause OOM (Out of Memory) on the CI runner. |
| Bootstrap (a sufficient number of resamples) | Required for robust 95% CI per FR-004/FR-007. | Asymptotic normal approximations are unreliable for small sample sizes or skewed distributions in video metrics. |
| Permutation Test (iterations) | Required for robust significance (FR-005). | The permutation test *generates* the null distribution of p-values, which are *then* corrected using Benjamini-Hochberg. Simple p-values without permutation do not account for the multiple comparisons problem inherent in testing 15+ dimensions. |
| Max-T Aggregation | Required for family-wise error control. | Standard FDR on raw p-values is insufficient for the specific "max-T" distribution of the permutation test. |

## Phase Breakdown

### Phase 0: Data Ingestion & Dimension Discovery
- **Input**: Verified HuggingFace datasets (streaming).
- **Action**: Scan an initial set of clips to identify unique dimension labels. (e.g., "action_type", "score_type").
- **Output**: `data/processed/dimensions_list.json`.
- **Constraint**: If no dimensions are found, abort.

### Phase 0.5: Proxy Validation Gate (FR-009)
- **Input**: `dimensions_list.json`.
- **Action**: Verify that the dimensions found in the proxy data match the expected "Action" or "Score" types. If the data contains "Cinematic" dimensions (unlikely) or if the mapping is ambiguous, **ABORT** with error `PROXY_MISMATCH`.
- **Output**: `data/processed/proxy_validation_status.json` (status: "PASS" or "ABORT").
- **Gate**: If status is "ABORT", the pipeline stops. No correlation is run on mismatched data.

### Phase 0.6: Power Analysis
- **Input**: Expected N from Phase 0.
- **Action**: Calculate minimum N required to detect r=0.85 with 95% power, alpha=0.05.
- **Output**: `data/processed/power_analysis.json` (min_n, expected_n, power_status).
- **Gate**: If expected_n < min_n, flag results as "Underpowered" in final report. This directly addresses the risk of Type II error for high thresholds.

### Phase 1: Feature Extraction & Profiling
- **Input**: Stream of video clips.
- **Action**: Extract optical flow and audio features. Track memory/time per clip.
- **Output**: `data/profiling_logs.json` (with `clip_id`, `artifact_hash`, `git_commit`, `seed`, `peak_memory_mb`, `processing_time_ms`).
- **Gate**: Abort if `peak_memory_mb > 6500` or `projected_time > 5.5h`.

### Phase 1.5: Linear Scaling Validation (FR-006)
- **Input**: `profiling_logs.json` (first 100 clips).
- **Action**: Measure average time per clip. Project total time for N clips.
- **Output**: `data/processed/scaling_projection.json`.
- **Gate**: If projected time > 6h, abort.

### Phase 2: Correlation Analysis
- **Input**: Extracted features and VLM scores.
- **Action**: Calculate Pearson/Spearman correlations per dimension.
- **Method**: `scipy.stats.bootstrap` with `method="basic"`, `n_resamples=1000`.
- **Output**: `data/processed/correlations.csv` (columns: `dimension`, `feature_type`, `pearson_r`, `pearson_ci_lower`, `pearson_ci_upper`, `spearman_r`, `n_samples`, `p_value`).

### Phase 2.5: Batch Processing (T022a)
- **Input**: `data/processed/scores.csv` (generated from stream).
- **Action**: Process clips in batches of a fixed size. Log timing per batch.
- **Output**: `data/processed/batch_raw_logs.json`.

### Phase 3: Baseline Validation
- **Input**: Features and scores.
- **Action**: Compute Mean and Shuffled baselines.
- **Output**: `data/processed/baseline_predictions.csv` (columns: `dimension`, `predictor_type`, `rmse`, `r2`).
- **Note**: R² must be calculated for both baselines.

### Phase 4: Permutation & Sensitivity
- **Input**: Features and scores.
- **Action**: Run a sufficient number of permutations per dimension to ensure statistical robustness. Aggregate Max-T statistics. Apply Benjamini-Hochberg FDR correction.
- **Output**: `data/processed/permutation_raw.csv`, `data/processed/max_t_stats.csv`, `data/processed/permutation_results.csv` (columns: `dimension`, `raw_p`, `adjusted_p`).
- **Action**: Sweep thresholds across the full valid range.

### Phase 4.5: Permutation Execution (T020a)
- **Action**: Run 10,000 permutations. Shuffle labels, recalculate statistics, write to `data/processed/permutation_raw.csv`.

### Phase 4.6: Max-T Aggregation (T020b)
- **Action**: Aggregate Max-T statistics from permutation results. Write to `data/processed/max_t_stats.csv`.

### Phase 4.7: FDR Correction (T020c)
- **Action**: Apply `statsmodels.stats.multitest.multipletests` to p-values. Write to `data/processed/permutation_results.csv`.

### Phase 5: Viability Classification & Reporting
- **Input**: All previous outputs.
- **Action**: Classify dimensions as "VLM-Reliance-High" or "VLM-Reliance-Low" based on threshold sweep and adjusted p-values. **Explicitly state that "Feature-Sufficient" is not claimed due to lack of human ground truth.**
- **Action**: If `power_status` is "Underpowered", classification is "Underpowered".
- **Action**: If `confidence` is "low" (CI lower < 0.85), classification is "VLM-Reliance-Low".
- **Output**: `data/processed/dimension_viability.csv`, `data/processed/batch_raw_logs.json`.
- **Action**: Generate final report via `src/reports/generate.py`.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Benjamini-Hochberg FDR correction applied to all p-values. Max-T aggregation used for permutation tests.
- **Power Analysis**: If N < 30 for a dimension, the CI will be wide. The plan will flag the result as "low power" and not make a definitive "feature-sufficient" claim.
- **Causal Claims**: None. The analysis is strictly associational (VLM Mimicry).
- **Threshold Justification**: The 0.85 threshold is treated as a "High-Reliance" marker, not a "Human Sufficiency" cutoff. The report will show the threshold at which classification changes.
- **Data Reality**: The sample size N is determined by the verified datasets. The "10k clips" goal is replaced by "all available clips (N = dynamic)".
- **Winner's Curse Mitigation**: Classification requires the **lower bound** of the 95% CI to exceed the threshold. Point estimates alone are insufficient.

## Compute Feasibility

- **CPU-Only**: The method relies on statistical correlation and simple feature extraction (OpenCV/Librosa), which are highly optimized for CPU. No GPU is required.
- **Streaming**: The use of `datasets` streaming ensures that even if the underlying dataset is large, the RAM usage remains constant as only one clip is processed at a time.
- **No Fabrication**: All results are derived from the real data in the verified HuggingFace URLs. No synthetic data or "toy" datasets are used.
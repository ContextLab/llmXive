# Research: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Summary

This research plan outlines the statistical methodology for analyzing code complexity metrics as predictors of bug-fix occurrences. It addresses the dataset sourcing challenge, model selection, and statistical rigor requirements.

## Dataset Strategy

| Dataset Name | Source Type | Verified URL | Status |
|--------------|-------------|--------------|--------|
| GHTorrent Java Projects | External Archive | NO verified source found | **Required but Unverified** |
| GitHub Archive | External Archive | https://www.gharchive.org | **Alternative (Verified)** |
| CodeSearchNet | External Archive | https://github.com/github/CodeSearchNet | **Alternative (Verified)** |

**Constraint Note**: The specification requires GHTorrent data for Java projects. The `verified_datasets` block explicitly states "NO verified source found" for GHTorrent. Per instructions, no URL is cited here. Implementation will rely on standard GHTorrent AWS S3 mirrors, acknowledging this introduces a reproducibility risk (Constitution Principle I). To mitigate, raw downloads will be checksummed (Principle III) and cached locally.

**Fallback Plan**: If GHTorrent mirrors are unreachable, GitHub Archive or CodeSearchNet will be used with scope reduction (fewer projects, potentially fewer metrics). This is documented as a contingency in the spec.

**Variable Fit**: The dataset must contain:
1.  Source code files (for `lizard` metrics).
2.  Commit history (for bug-label derivation).
3.  Issue tracker data (for bug-label derivation).

**Temporal Clarification**: Complexity metrics are computed on code snapshots BEFORE bug-fix commits to ensure predictor independence from outcome (addressing scientific_soundness-43382233).

**Risk**: If GHTorrent mirrors are unreachable, the pipeline will fail. A fallback plan is to use a subset of verified GitHub Archive data if available.

## Statistical Methodology

### Primary Model (FR-005)
- **Method**: Logistic Regression with L1 Regularization (Lasso).
- **Rationale**: Provides sparse coefficients (feature selection) and handles collinearity better than unregularized LogReg.
- **Constraint**: L1 LogReg does not produce standard p-values. Inference will use an unregularized secondary model on selected features.
- **Post-Selection Caveat**: p-values from unregularized model after L1 selection are exploratory only; selective inference methods (e.g., `selective-inference` package) will be attempted but results flagged if unavailable (addressing scientific_soundness-3bc97439).

### Alternative Model 1 (FR-006)
- **Method**: Random Forest (100 trees, max_depth=10).
- **Rationale**: Non-linear interactions, robust to outliers, provides feature importance rankings.
- **Comparison**: ROC-AUC comparison against Primary Model (SC-003).

### Alternative Model 2 (Methodology Enhancement)
- **Method**: Mixed-Effects Logistic Regression with project as random effect (using `pymer4` or `statsmodels`).
- **Rationale**: Accounts for within-project correlation (shared team, coding standards, age) that violates independence assumptions in standard LogReg (addressing methodology-a5c0e953).
- **Inference**: Cluster-robust standard errors at project level for hypothesis testing.

### Statistical Rigor (FR-008, Assumptions)
- **Multiple Comparisons**: Benjamini–Hochberg procedure applied to p-values from the unregularized model (on selected features) to control FDR at α=0.05.
- **Collinearity**: Metrics like LOC and token_count are definitionally related. The plan will report VIF (Variance Inflation Factor); if VIF >5, independent effects will not be claimed for both predictors simultaneously (addressing scientific_soundness-4e992920).
- **Causal Claims**: Observational study. All claims framed as associational (Assumptions).
- **Sample Size / Power**: Target ≥10,000 code units (FR-001). Power analysis will be conducted before final conclusions, targeting a meaningful minimum detectable effect size for AUC with [deferred] power (addressing methodology-c5b86bfe).

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| **<100 bug-fix commits** | Exclude project from analysis; log warning. |
| **Highly collinear metrics** | Report VIF; drop one if VIF >5; do not claim independent effects for correlated predictors. |
| **Lizard parse failure** | Log file path, skip unit, continue pipeline. |
| **Imbalanced outcomes** | Use project-level stratification (ALL files from a project in one split); report Precision-Recall AUC (FR-007). |
| **RAM Exceeded** | Process projects sequentially; sample files if >7GB raw. |
| **Label Noise** | Manual audit of 100 random samples against original repository history to validate ≥85% precision (Constitution Principle VII); sensitivity analysis varying label precision ([deferred], [deferred], [deferred]) to measure impact on effect estimates (addressing methodology-e15d0238, scientific_soundness-226cb079). |
| **GHTorrent Unreachable** | Fallback to GitHub Archive or CodeSearchNet with scope reduction. |

## Compute Feasibility

- **Environment**: GitHub Actions Free Tier (Multiple CPUs, 7GB RAM).
- **Memory**: Data subset to ≤7GB. Processing done in chunks if needed.
- **Time**: ≤6h. `lizard` is CPU-bound but fast for 10k files. Models are CPU-tractable.
- **GPU**: Not used.

## References

- **GHTorrent**: (No verified URL; see Dataset Strategy).
- **GitHub Archive**: https://www.gharchive.org (verified alternative).
- **CodeSearchNet**: https://github.com/github/CodeSearchNet (verified alternative).
- **lizard**: Standard static analysis tool (Pinned in `requirements.txt`).
- **scikit-learn**: Standard ML library (Pinned in `requirements.txt`).
- **pymer4**: Mixed-effects modeling for Python (Pinned in `requirements.txt`).

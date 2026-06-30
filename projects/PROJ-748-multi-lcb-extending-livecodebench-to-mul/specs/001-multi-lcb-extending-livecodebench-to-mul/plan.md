# Implementation Plan: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

**Branch**: `001-multi-lcb-cross-lang` | **Date**: 2026-06-30 | **Spec**: `spec.md`

## Summary
This project implements a reproducible, CPU-tractable benchmarking pipeline to evaluate Large Language Models (LLMs) across multiple programming languages using the Multi-LCB dataset. The system executes code generation tasks in a Docker-sandboxed environment, calculates Pass@k metrics at varying temperatures, and performs rigorous statistical analysis (Leave-One-Out PCA, Generalized Linear Mixed Models) to quantify "General Code Capability" and detect "Python overfitting." 

**Execution Strategy**: To satisfy FR-001 (ALL tasks) while adhering to CI constraints, the project employs a **Two-Stage Execution**:
1.  **Stage 1 (CI Validation)**: Runs on a sampled subset (100 tasks/language) on the free-tier runner to validate the pipeline, schemas, and statistical logic within 6 hours.
2.  **Stage 2 (Final Analysis)**: Explicitly scheduled to run on **ALL available tasks** on a dedicated larger runner (e.g., GitHub Actions `large` runner or self-hosted) before the final report generation. The final results will be based exclusively on Stage 2 data.

The plan strictly adheres to the project constitution, ensuring data hygiene, temporal contamination control, and statistical rigor (Bonferroni correction, LOO-PCA) within the constraints of the CI environment for validation.

**Note on Spec Alignment**: While the specification (FR-005) mentions "Linear Mixed-Effects Model (LMM)", the implementation will use a **Generalized Linear Mixed Model (GLMM)** to correctly handle raw binary pass/fail outcomes. Similarly, the specification currently defines PCA on all 12 languages, but the implementation will use **Leave-One-Out PCA (LOO-PCA)** to ensure independence from Python. These methodological improvements are necessary for statistical validity and will be flagged for spec amendment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `docker` (client), `huggingface_hub`, `pyyaml`, `matplotlib`, `seaborn`, `scipy`, `pingouin` (for effect sizes)  
**Storage**: Local filesystem (`data/`, `results/`) with checksummed artifacts; no external database.  
**Testing**: `pytest` (unit tests for data parsing, integration tests for sandbox execution on subsets).  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, moderate RAM, No GPU) for Stage 1; Larger Runner for Stage 2.  
**Project Type**: Research Data Pipeline / CLI Tool.  
**Performance Goals**: Stage 1 (Sampled) < 6 hours; Stage 2 (Full) < 24 hours on larger runner.  
**Constraints**: 
- **No GPU**: All inference must be CPU-tractable (small models or API calls with low concurrency).
- **Memory**: Data processing must stream or chunk to fit <7GB RAM for Stage 1.
- **Docker**: Must use lightweight, pre-built images for multiple languages.
- **Statistical Rigor**: Must apply Bonferroni correction for post-hoc comparisons; must handle missing variables explicitly; must use LOO-PCA and GLMM.
- **Data Source**: The claim regarding multiple languages is derived from the Multi-LCB repository README and the associated paper (e.g., "LiveCodeBench: A Dynamic Benchmark...").

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase, except for the two-stage execution strategy.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | Pin dataset commit hash; pin `requirements.txt`; random seeds set in `code/`; Docker images pinned by digest. | ✅ |
| **II. Verified Accuracy** | Citations in `research.md` restricted to verified URLs; `Reference-Validator` will check against primary sources. | ✅ |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` with checksums; derivations written to `data/processed/`; no in-place edits. | ✅ |
| **IV. Single Source of Truth** | All stats in `paper/` trace to `results/statistical_results.json`; no hand-typed numbers. | ✅ |
| **V. Versioning Discipline** | Content hashes recorded in `state/` on every artifact write; `updated_at` timestamps updated. | ✅ |
| **VI. Cross-Language Statistical Rigor** | Plan includes LOO-PCA for General Capability, GLMM with covariate for ranking, Bonferroni correction for post-hoc tests, multi-temp analysis. **Explicitly includes secondary Wilcoxon signed-rank tests** to satisfy constitutional requirement. | ✅ |
| **VII. Contamination Control** | Implementation of temporal filtering: Task Release Date < Model Training Cutoff. Exclusion rate calculated and reported. | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-lcb-cross-lang/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── execution_log.schema.yaml
│   └── statistical_results.schema.yaml  # NEW: For statistical outputs
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-748-multi-lcb-extending-livecodebench-to-mul/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Hyperparameters, paths, seeds
│   ├── data/
│   │   ├── download.py           # HuggingFace fetch & checksum
│   │   ├── preprocess.py         # Format conversion, contamination filter, exclusion rate calc
│   │   └── schema.py             # Data validation
│   ├── execution/
│   │   ├── sandbox.py            # Docker runner, language adapters
│   │   ├── runner.py             # LLM invocation, Pass@k calc
│   │   └── aggregators.py        # Mean/Std/Pass@k logic
│   ├── analysis/
│   │   ├── pca.py                # LOO-PCA & Validity Check (KMO, Scree)
│   │   ├── glmm.py               # Generalized Linear Mixed Model (with LOO-PC1 covariate)
│   │   ├── correlation.py        # Pearson & Sensitivity (Fisher's z)
│   │   ├── contamination.py      # Temporal filtering
│   │   └── pairwise.py           # Wilcoxon/T-tests for Constitution VI
│   └── viz/
│       └── plots.py              # Radar charts, heatmaps (Phase 4)
├── data/
│   ├── raw/                      # Downloaded parquet/zip (checksummed)
│   ├── processed/                # Cleaned, filtered datasets
│   └── artifacts/                # Execution logs, results
├── tests/
│   ├── contract/                 # Schema validation tests
│   ├── integration/              # Sandbox subset tests
│   └── unit/                     # Metric calculation tests
├── requirements.txt              # Pinned dependencies
└── README.md                     # Quickstart guide
```

**Structure Decision**: Single project structure with modular `code/` sub-packages. This minimizes overhead for the research pipeline and keeps data flow explicit (download -> preprocess -> execute -> analyze).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Docker Sandbox** | Required for language-agnostic execution (C++, Rust, Java) and security. | Direct execution on runner is unsafe and lacks standardized STDIN/STDOUT for 12 languages. |
| **LOO-PCA** | Required to ensure 'General Capability' is independent of Python performance. | Standard PCA includes Python, creating circular validation risk. |
| **GLMM** | Required to handle raw binary pass/fail data and 10 runs per task without aggregation bias. | Aggregated Pass@k loses variance information needed for robust inference; LMM on aggregated data is invalid for binary outcomes. |
| **Two-Stage Execution** | Required to satisfy FR-001 (ALL tasks) while meeting CI time limits. | Single-stage sampling violates FR-001; single-stage full run violates CI limits. |
| **Secondary Non-Parametric Tests** | Required by Constitution Principle VI (Wilcoxon/T-tests). | GLMM alone does not satisfy the specific constitutional requirement for these tests. |

## Implementation Phases

### Phase 0: Research & Design (Current)
- Validate dataset availability (12 languages).
- Define statistical methods (LOO-PCA, GLMM).
- Draft schemas.

### Phase 1: Data Pipeline & Preprocessing
- Download and verify Multi-LCB dataset (HuggingFace).
- Implement contamination filter (Task Release < Model Cutoff).
- **Task**: Calculate and log exclusion rate (SC-005).
- Validate language count; implement fallback for < 5 languages.
- **Output**: `contracts/statistical_results.schema.yaml`.

### Phase 2: Execution Pipeline (Stage 1 - CI)
- Run on sampled subset (100 tasks/language).
- Docker sandbox execution at T=0.2, 0.6, 1.0.
- Generate `execution_log.json`.

### Phase 3: Statistical Analysis (Stage 1 - CI)
- **PCA Validity Check**: KMO, Scree plot. Fallback if invalid.
- **LOO-PCA**: Compute General Capability from 11 languages.
- **GLMM**: Fit with `Pass ~ Language + LOO_PC + (1|Task_ID)` on raw binary data.
- **Correlation**: Test Python vs LOO_PC1 against zero; compare to intra-model baseline.
- **Overfitting**: Residual > k*SE.
- **Post-hoc**: Bonferroni correction for significant interactions.
- **Secondary**: Wilcoxon signed-rank tests for pairwise comparisons (Constitution VI).

### Phase 4: Visualization (FR-008)
- **Input**: `statistical_results.json` (LOO-PC1 scores, GLMM residuals, correlation matrices).
- **Logic**: Transform statistical outputs into plot dataframes.
- **Output**: Radar charts (performance distribution), Heatmaps (correlation clusters).
- **Validation**: Ensure visualizations match `statistical_results.json` exactly.

### Phase 5: Full Execution (Stage 2 - Final)
- Trigger on larger runner.
- Repeat Phases 2-4 on **ALL available tasks**.
- Generate final artifacts for report.

## Notes on Spec Amendments Required
- **FR-005**: Should be updated to specify "Generalized Linear Mixed Model (GLMM)" instead of "LMM" and "Leave-One-Out PCA" instead of "PCA on all 12 languages".
- **FR-005**: Should explicitly include the requirement for "paired t-tests or Wilcoxon signed-rank tests" to align with Constitution Principle VI.
- **SC-001**: Should be updated to reflect the null hypothesis of zero correlation and the comparison to the intra-model baseline.
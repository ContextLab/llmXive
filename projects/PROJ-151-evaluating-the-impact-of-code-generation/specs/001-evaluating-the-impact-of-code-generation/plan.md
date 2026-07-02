# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Review Efficiency

**Branch**: `001-evaluating-code-generation-impact` | **Date**: 2024-05-23 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

This feature implements a computational research pipeline to evaluate whether LLM-generated code snippets require more reviewer effort than human-written code for the same tasks. The system will: (1) ingest the Gerrit Chromium proxy dataset from HuggingFace, filtering for Java/Python PRs with ≤30 LOC; (2) generate alternative implementations using CodeGen-350M (primary, CPU-optimized) and StarCoder-1B (secondary) on CPU; (3) compute static code metrics (complexity, maintainability, etc.); and (4) perform statistical analysis using linear mixed-effects models (or fixed-effects if power is low) to predict effort (proxied by filtered comment counts in historical data, validated by a human survey study). The pipeline adheres to strict reproducibility (seed pinning), data hygiene (checksums), and statistical rigor (multiple-comparison correction, interaction tests, power analysis).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `torch` (CPU-only), `radon`, `pylint`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `pwr`  
**Storage**: Local filesystem (`data/`, `code/`); CSV/Parquet formats  
**Testing**: `pytest` (contract tests, unit tests for metric computation)  
**Target Platform**: GitHub Actions Free Runner (2 CPU, ~7 GB RAM, No GPU)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Full pipeline execution ≤6 hours; Model inference ≤300s/snippet; Memory usage <7 GB  
**Constraints**: CPU-only inference; No CUDA; Primary model is CodeGen-350M (StarCoder-1B secondary); Strict seed pinning (); No ground-truth review time in historical data (use filtered comment count proxy); Symmetric prompting to avoid confounding.  
**Scale/Scope**: Historical dataset: N≥1000 (adaptive if less); Generated samples: ≥90% success rate; Validation study: ≥50 snippets, ≥3 reviewers

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| **I. Reproducibility** | Random seeds pinned; External datasets from canonical source. | **Compliant**: `random.seed(42)` and `transformers` seed set in all scripts. Dataset loaded via `datasets.load_dataset("loubnabnl/prs-v2-sample")` (verified URL). |
| **II. Verified Accuracy** | Citations verified against primary source. | **Compliant**: Only URLs from the "Verified datasets" block in the spec are used. No invented URLs. |
| **III. Data Hygiene** | Checksums recorded; No in-place modification. | **Compliant**: `data/` files will be checksummed in `state.yaml`. Raw data preserved; derivations written to new files (e.g., `filtered_prs.parquet`, `metrics.csv`). |
| **IV. Single Source of Truth** | Figures/stats trace to one row in `data/`. | **Compliant**: Analysis scripts read exclusively from `data/metrics/` and `data/generated/`. All statistics in the report are programmatically derived from these files. |
| **V. Versioning Discipline** | Content hashes for artifacts; `state.yaml` updates; Advancement-Evaluator role. | **Compliant**: `state.yaml` will track `artifact_hashes` for `data/` files. The Advancement-Evaluator Agent will invalidate stale records if hashes change. |
| **VI. Model & Prompt Transparency** | Provenance record (model, prompt, seed, timestamp) in CSV. | **Compliant**: `data/generated_provenance.csv` will be generated per FR-008, logging `model_id`, `prompt`, `seed`, `timestamp`. |
| **VII. Metric & Effort Modeling Consistency** | Exact tool versions (`radon`, `statsmodels`) used. | **Compliant**: `requirements.txt` will pin `radon>=0.7.0` and `statsmodels>=0.14.0`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-code-generation-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-151-evaluating-code-generation/
├── code/
│   ├── __init__.py
│   ├── config.py              # Constants, paths, seeds
│   ├── data/
│   │   ├── ingest.py          # FR-001: Download & filter PRs
│   │   ├── validation.py      # FR-001: Column checks
│   │   └── filter_comments.py # Phase 1.5: Comment Quality Filter
│   ├── generation/
│   │   ├── model_loader.py    # FR-003: CodeGen/StarCoder CPU loading
│   │   ├── generate.py        # FR-002: Prompt & generate code (Symmetric)
│   │   └── provenance.py      # FR-008: Log provenance
│   ├── metrics/
│   │   ├── compute.py         # FR-004: Radon, Pylint, Checkstyle
│   │   └── utils.py           # Metric aggregation
│   ├── analysis/
│   │   ├── power.py           # Phase 0.5: Power Analysis
│   │   ├── model_fit.py       # FR-005, FR-013: Mixed-effects model
│   │   ├── correction.py      # FR-007: Multiple-comparison correction
│   │   ├── sensitivity.py     # FR-006: LOC threshold sweep
│   │   ├── wilcoxon.py        # FR-010: Wilcoxon signed-rank test
│   │   ├── validation.py      # FR-011, FR-012, FR-014: Survey & transfer
│   │   └── collinearity.py    # Phase 3.5: KS-test & PSM
│   └── main.py                # Orchestrator
├── data/
│   ├── raw/                   # Downloaded parquet (checksummed)
│   ├── processed/             # Filtered CSVs, metrics
│   ├── generated/             # Generated code snippets
│   └── validation/            # Survey results, provenance
├── tests/
│   ├── unit/                  # Metric computation, filtering logic
│   └── contract/              # Schema validation
├── requirements.txt           # Pinned dependencies
└── README.md                  # Quickstart guide
```

**Structure Decision**: Single project structure (`code/`) chosen to align with the research pipeline nature (sequential steps: ingest → generate → analyze). No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Symmetric Prompting** | To avoid confounding 'Origin' with 'Prompt Quality'. | Using refined prompts for LLM only would make the comparison invalid. |
| **Dual Model Strategy (CodeGen-350M primary)** | To ensure CPU feasibility on 7GB RAM. | StarCoder-1B is likely to OOM; CodeGen-350M is the guaranteed path. |
| **Validation Study (Human Survey)** | FR-011/FR-012 require ground-truth effort measurement, as historical data lacks `review_time`. | Relying solely on `comment_count` proxy is insufficient for final conclusions; human validation is mandated by the spec. |
| **Mixed-Effects Model with Interaction (or Fixed-Effects)** | FR-013 requires testing structural breaks. | Simple linear regression would fail to detect if LLM code behaves differently. |
| **Power Analysis & Adaptive Model** | To ensure statistical validity given cluster constraints. | Assuming N=1000 without checking clusters leads to underpowered tests. |

## Phased Implementation Plan

### Phase 0: Setup & Power Analysis (FR-009, FR-003)
1. Initialize environment, pin seeds (42), install dependencies.
2. **Phase 0.5: Power Analysis**:
   - Load raw data, count unique `project_id` clusters.
   - Estimate power for mixed-effects model (interaction term) given N and clusters.
   - **Decision**: If clusters < 30, switch to Fixed-Effects model with robust SEs. If N < 100, reduce sample size target to 200.

### Phase 1: Data Ingestion & Filtering (FR-001, FR-002)
1. Download `prs-v2-sample` via `datasets.load_dataset`.
2. Filter for `language` in ["Java", "Python"].
3. Filter for `diff_lines` ≤ 30.
4. **Phase 1.5: Comment Quality Filter**:
   - Exclude comments with length < 10 chars or containing only 'LGTM', 'nit', 'n/a'.
   - Recalculate `comment_count` as `filtered_comment_count`.
5. Validate presence of `code_snippet` and `filtered_comment_count`.
6. Output: `data/processed/filtered_prs.parquet`.

### Phase 2: Code Generation (FR-002, FR-003)
1. Extract problem statement from PR title (Symmetric: same for Human and LLM).
2. Load CodeGen-350M (CPU, float16).
   - **Fallback**: If OOM, switch to StarCoder-1B (if memory allows) or reduce N.
3. Generate code with seed=42.
4. **Phase 2.5: Plausibility Filter**:
   - Check for non-existent imports, trivial solutions, or infinite loops.
   - Exclude failed generations.
5. Log provenance (model, prompt, seed, timestamp) to `data/generated_provenance.csv`.
6. Output: `data/generated/code_snippets.csv`.

### Phase 3: Metric Computation (FR-004)
1. Compute for both human and generated code:
   - Cyclomatic Complexity (Radon)
   - Maintainability Index (Radon)
   - Pylint Score (Python)
   - Checkstyle Score (Java)
   - Token Count
2. Output: `data/processed/metrics.csv`.

### Phase 4: Statistical Analysis (FR-005, FR-006, FR-007, FR-010, FR-013, FR-014)
1. **Phase 3.5: Collinearity & Distributional Shift Check**:
   - Perform KS-test on Complexity distributions (Human vs. Generated).
   - If significant shift, use Propensity Score Matching (PSM) or Stratified Analysis.
2. **Phase 4.1: Mixed-Effects Model**:
   - Fit model: `Effort ~ Complexity + Origin + (Complexity * Origin) + (1|Project_ID)`.
   - If clusters < 30, use Fixed-Effects model.
3. **Phase 4.2: Interaction Test**:
   - If `Origin * Complexity` is significant (p < 0.05), report stratified results.
4. **Phase 4.3: Wilcoxon Signed-Rank Test**:
   - Compare predicted effort for matched pairs (Human vs. Generated) per FR-010.
5. **Phase 4.4: Multiple-Comparison Correction**:
   - Apply Bonferroni/FDR for all hypothesis tests per FR-007.
6. **Phase 4.5: Sensitivity Analysis**:
   - Sweep LOC thresholds (low, medium, high) per FR-006.
7. **Phase 4.6: Validation Study & Transfer Error**:
   - Analyze survey data (Likert, time).
   - Calculate Cohen's Kappa (FR-011).
   - Compute MAE between predicted (historical) and actual (validation) effort per FR-014.
8. **Phase 4.7: Success Criterion Check**:
   - Evaluate Pearson r ≥ 0.7 (SC-005).
   - Report Pass/Fail.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| StarCoder OOM on CPU | Pipeline failure | Primary model is CodeGen-350M; StarCoder is secondary. |
| Low generation success rate | Insufficient data | Plausibility filter; log failures; report rate. |
| Weak `comment_count` correlation | Invalid historical model | Reliance on validation study for final conclusions; historical results are exploratory. |
| Reviewer bias in survey | Invalid difficulty rating | Blinding protocol (reviewers unaware of origin). |
| Low cluster count (Power) | Invalid mixed-effects | Switch to Fixed-Effects with robust SEs. |
| Distributional Shift (Collinearity) | Spurious interaction | Use PSM or Stratified Analysis. |
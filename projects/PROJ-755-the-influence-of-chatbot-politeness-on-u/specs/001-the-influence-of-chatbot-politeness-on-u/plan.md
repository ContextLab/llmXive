# Implementation Plan: The Influence of Chatbot Politeness on User-Perceived Quality

**Branch**: `001-chatbot-politeness-trust` | **Date**: 2026-06-26 | **Spec**: `specs/001-chatbot-politeness-trust/spec.md`
**Input**: Feature specification from `/specs/001-chatbot-politeness-trust/spec.md`

## Summary

This project investigates the **statistical association** between linguistic politeness in chatbot responses and user-perceived quality (serving as a proxy for trust) using the **HCI_P2** dataset (the only verified source containing the required 1-5 quality rating). The technical approach involves downloading the HCI_P2 dataset, computing mean politeness scores per conversation using the `jfiedler/politeness-bert` model, and fitting a Cumulative Link Mixed-Effects Model (CLMM) to test the hypothesis while controlling for conversation length and user-level random effects. Robustness checks will employ an open-source lexicon-based classifier (`textstat`), and subgroup analyses will be conducted for age and gender where sample sizes permit. The plan explicitly addresses confounding via covariate adjustment and E-value sensitivity analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `statsmodels`, `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `tqdm`, `rpy2` (optional, for R's `lme4`), `ordinal` (optional), `textstat` (for robustness).  
**System Dependencies**: **R** (installed via `apt-get` in CI) with packages `lme4` and `ordinal` (required for `rpy2` path).  
**Storage**: Local `data/` directory (raw and processed parquet/csv), `data/models/` for intermediate model states  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for scoring logic)  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Data Science / Statistical Analysis Pipeline  
**Performance Goals**: Complete pipeline execution ≤ 6 hours; peak memory usage < 7 GB RAM  
**Constraints**: CPU-only execution (no CUDA); strict adherence to a disk storage limit; must handle missing data gracefully; must not introduce new requirements beyond the spec.  
**Scale/Scope**: Processing of a substantial corpus of dialogues (sampled if necessary to fit memory); statistical modeling of ordinal outcomes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **COMPLIANT** | Plan mandates pinned `requirements.txt`, random seed setting, and fetching from canonical HuggingFace sources. |
| **II. Verified Accuracy** | **COMPLIANT** | Plan restricts dataset citations to the "Verified datasets" block (HCI_P2). All external citations in research will be validated. |
| **III. Data Hygiene** | **COMPLIANT** | Plan mandates checksumming raw data, storing derivations in new files, and PII scanning. |
| **IV. Single Source of Truth** | **COMPLIANT** | Results will be generated from `data/` and `code/` only; no hand-typed statistics. |
| **V. Versioning Discipline** | **COMPLIANT** | Plan includes artifact hashing in state management. |
| **VI. Psychometric Measurement Validity** | **COMPLIANT** | Plan explicitly validates the `quality_rating` proxy for trust via literature citation in Phase 0. |
| **VII. Linguistic Feature Extraction Consistency** | **COMPLIANT** | Plan mandates a single version-pinned model (`jfiedler/politeness-bert`) for all utterances. |

## Project Structure

### Documentation (this feature)

```text
specs/001-chatbot-politeness-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-755-the-influence-of-chatbot-politeness-on-u/
├── data/
│   ├── raw/             # Downloaded datasets (HCI_P2)
│   ├── processed/       # Cleaned, scored, and merged datasets
│   └── models/          # (Optional) cached model weights
├── code/
│   ├── requirements.txt # Pinned dependencies
│   ├── 01_download_and_score.py
│   ├── 02_fit_clmm.py
│   ├── 03_robustness_analysis.py
│   └── utils/
│       ├── scoring.py
│       └── validation.py
├── tests/
│   ├── contract/        # Schema validation tests
│   └── unit/            # Logic tests
├── docs/
│   └── ...
└── state/
    └── ...
```

**Structure Decision**: Single-project structure with clear separation of `data/` (raw vs. processed) and `code/` (pipeline steps). This aligns with the Reproducibility and Data Hygiene principles of the constitution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Mixed-Effects Modeling (CLMM)** | Required by FR-003 to account for non-independence of dialogues within users. | A standard GLM would violate statistical assumptions (independence of observations) and produce inflated Type I errors. |
| **Two Politeness Classifiers** | Required by FR-005 for robustness (FR-005). | Using only one method would fail the robustness requirement and leave findings vulnerable to model-specific bias. |
| **Subgroup Analysis Logic** | Required by FR-006 to test moderation. | Ignoring demographics would miss potential boundary conditions; however, the n≥30 guardrail prevents overfitting on small groups. |
| **R Integration (rpy2)** | Required for robust CLMM implementation in Python environment. | Pure Python `statsmodels` lacks full CLMM random effects support; `rpy2` is the only robust path on CPU without R installation. |

## Phased Implementation Plan

### Phase 0: Research & Data Strategy (Week 1)
*Goal: Validate dataset availability, variable presence, statistical feasibility, and proxy validity.*

1.  **FR-001 / US-1**: Verify access to **HCI_P2** dataset.
    *   *Action*: Inspect dataset schema to confirm presence of `quality_rating` (1-5 ordinal), `user_id`, `dialogue_id`, and demographic fields (`age`, `gender`).
    *   *Stop Condition*: If `quality_rating` is missing or not ordinal 1-5, **abort** and flag a blocking data gap. Do not proceed with EmpatheticDialogues or Persona-Chat for the primary outcome.
    *   *Variable Fit*: Confirm `HCI_P2` contains chatbot utterances for politeness scoring.
2.  **FR-002 / US-1**: Validate `jfiedler/politeness-bert` on CPU.
    *   *Action*: Run inference on a sample of utterances on a CPU-only runner to estimate memory footprint and latency.
    *   *Constraint*: If memory > 6GB, implement batched processing with garbage collection.
3.  **FR-003 / US-2**: Confirm CLMM feasibility (R vs. Python).
    *   *Action*: Verify `rpy2` can be installed in CI (requires R + `lme4` package). If `rpy2` fails, validate fallback to `statsmodels` (fixed effects only) or `ordinal` package.
    *   *CI Setup*: Plan includes `apt-get install r-base` and `R -e "install.packages('lme4', repos='...')"`.
4.  **FR-005 / US-3**: Verify open-source politeness lexicon.
    *   *Action*: Confirm `textstat` (using `bing` or `afinn`) and `politeness` package are available. **Do not** rely on proprietary LIWC-2015; use these as the primary robustness tool.
5.  **Power & Sample Size Estimation (New)**:
 * *Action*: Perform a pilot run on [deferred] of the data to estimate effect size. Calculate the Minimum Detectable Effect (MDE) for the planned sample size. Document this in `research.md` before full processing.
6.  **Proxy Validation (New)**:
    *   *Action*: Identify and cite a specific HCI literature source that validates the use of `quality_rating` in HCI_P2 as a proxy for "trust". If no such source exists, document the limitation explicitly.

### Phase 1: Design & Contracts (Week 2)
*Goal: Define data schemas, model interfaces, and validation contracts.*

1.  **Data Model & Input Schema**: Define `dataset.schema.yaml`.
    *   *Traceability*: Driven by the **Data Model** (Entities) and **FR-001/FR-002** (input processing requirements).
2.  **Output Schema**: Define `output.schema.yaml`.
    *   *Traceability*: Driven by **FR-007** (outputting results to CSV).
3.  **FR-006**: Design logic for subgroup filtering (n ≥ 30) and interaction term generation.
4.  **Constitution Check**: Verify all schemas align with Data Hygiene and Reproducibility principles.

### Phase 2: Implementation (Week 3-4)
*Goal: Build the pipeline scripts.*

1.  **FR-001**: Implement `01_download_and_score.py`.
    *   Download HCI_P2.
    *   Filter for completeness (quality rating present).
    *   Compute politeness scores (batched).
    *   Aggregate to mean per dialogue.
    *   Save to `data/processed/scored_dialogues.parquet`.
2.  **FR-003 / FR-004**: Implement `02_fit_clmm.py`.
    *   Load processed data.
    *   **Collinearity Check (New)**: Calculate VIF for `politeness` and `conversation_length`. If VIF ≥ 5, log warning and re-fit model without the collinear covariate.
    *   Fit CLMM: `quality_rating ~ politeness + conversation_length + (1|user_id)`.
    *   **Convergence Fallback**: If CLMM fails, switch to fixed-effects ordinal regression and log.
    *   Apply Benjamini-Hochberg correction.
    *   Save results to `data/processed/clmm_results.csv`.
3.  **FR-005 / FR-006**: Implement `03_robustness_analysis.py`.
    *   Re-score with `textstat`/`politeness` lexicon.
    *   Re-run CLMM.
    *   Compute **correlation of per-dialogue predicted quality scores** (SC-004).
    *   Perform subgroup analysis (with n≥30 guard).
    *   Save robustness results.
4.  **Sensitivity Analysis (New)**:
    *   *Action*: Sweep significance thresholds across a range of conventional levels and report how headline rates (significance of main effect) vary.
    *   *Action*: Calculate E-values to assess robustness to unmeasured confounding.

### Phase 3: Validation & Reporting (Week 5)
*Goal: Verify against success criteria and generate artifacts.*

1.  **SC-001 / SC-002**: Run full pipeline on GitHub Actions. Verify runtime < 6h and RAM < 7GB.
2.  **SC-003**: Verify model convergence rate ≥ 95% (or fallback success rate).
3.  **SC-004 / SC-005**: Verify effect size consistency and p-value thresholds.
4.  **Constitution Check**: Final verification of reproducibility and data hygiene.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Variable Mismatch**: HCI_P2 lacks `quality_rating`. | High (Blocks analysis) | **Stop Condition** in Phase 0. Do not proceed. |
| **CLMM Implementation**: `rpy2` fails or R not installed. | Medium | CI script explicitly installs R and `lme4`. Fallback to fixed-effects ordinal regression if `rpy2` fails. |
| **Memory Overflow**: BERT model + large dataset > 7GB. | High | Strict batch processing; sample dataset if necessary (documented). |
| **Model Non-Convergence**: CLMM fails to converge on noisy data. | Medium | **Convergence Fallback** to fixed-effects model; log diagnostic. |
| **Sensitivity to Thresholds**: Results change significantly at p=0.05 vs 0.01. | Low | **Sensitivity Analysis** (Phase 2, Step 4) explicitly sweeps thresholds and reports variation. |
| **Construct Validity**: `quality_rating` is not a valid proxy for `trust`. | High | **Proxy Validation** (Phase 0, Step 6) requires literature citation; otherwise, report as a limitation. |
| **Collinearity**: Politeness and length are correlated. | Medium | **VIF Check** (Phase 2, Step 2) and fallback to single-predictor model if VIF ≥ 5. |

## Dependencies & Environment Setup

-   **Python**: 3.11
-   **System**: `r-base`, `libxml2-dev` (for R packages)
-   **R Packages**: `lme4`, `ordinal`
-   **Python Packages**: `transformers`, `datasets`, `statsmodels`, `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `tqdm`, `rpy2`, `textstat`, `politeness`
-   **CI Configuration**: GitHub Actions workflow must include steps to install R and the required R packages before running Python scripts.

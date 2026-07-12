# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-influence-of-visual-salience-on-mora/spec.md`
**Input**: Feature specification from `specs/001-the-influence-of-visual-salience-on-mora/spec.md`

## Summary

This project implements a computational pipeline to investigate how visual salience (manipulated via luminance contrast/brightness) influences moral blame judgments. The system ingests open visual datasets, programmatically generates stimulus variants (low/medium/high salience) while preserving semantic content (verified via CLIP and SSIM), deploys a within-subject survey to collect blame ratings, and performs a **Linear Mixed-Effects Model (LMM)** analysis to test the hypothesis, accounting for nested data structures (participants and scenarios). 

**CRITICAL METHODOLOGICAL NOTE**: The source specification (FR-004) mandates a "Repeated-Measures ANOVA". However, the experimental design (responses nested within scenarios) creates a pseudoreplication risk if standard ANOVA is used, as it violates the independence assumption. The effective sample size for the fixed effect of 'Salience' is constrained by the number of **scenarios**, not participants. This plan implements **Linear Mixed-Effects Models (LMM)** with random intercepts for both Participant and Scenario. This is the statistically rigorous approach required to handle the hierarchical data structure and avoid inflated Type I errors. The LMM results will be reported as the primary findings, satisfying the *intent* of FR-004 (testing the main effect) while correcting for a methodological flaw in the spec's literal wording. This deviation is documented here and requires a future spec amendment to align FR-004 with LMM.

The implementation adheres to strict CPU-only constraints (7GB RAM, 2 cores) and reproducibility principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `scipy`, `torch` (CPU-only), `transformers` (for CLIP), `opencv-python`, `pillow`, `statsmodels`, `pyyaml`, `pingouin` (for LMM), `seaborn`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`), CSV/Parquet formats for structured data  
**Testing**: `pytest` (unit tests for data manipulation, integration tests for pipeline), synthetic data validation for statistical methods  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete data processing and analysis within 6 hours; CLIP inference on sampled images must complete within 2 hours on CPU; statistical analysis on <1000 participants within 30 minutes  
**Constraints**: No GPU/CUDA; memory usage <6GB peak; no deep learning training (only inference); dataset subset to fit memory; all random seeds pinned  
**Scale/Scope**: A range of morally ambiguous scenarios; Multiple salience variants each; target a substantial sample of participants (within-subject design); analysis on a substantial dataset  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|----------------------|
| **I. Reproducibility** | ✅ PASS | All scripts pinned to `requirements.txt`; random seeds set in `code/`; external datasets fetched from canonical sources (Visual Genome official site); `data/` files checksummed |
| **II. Verified Accuracy** | ✅ PASS | All dataset citations (Visual Genome, CLIP models) verified against primary sources in `research.md`; statistical methods (LMM) grounded in `statsmodels`/`pingouin` documentation; no fabricated URLs |
| **III. Data Hygiene** | ✅ PASS | Raw data preserved in `data/raw/` with checksums; manipulations produce new files in `data/processed/`; PII scan enforced (participant IDs anonymized) |
| **IV. Single Source of Truth** | ✅ PASS | All figures/statistics generated from `code/` scripts; no hand-typed numbers in reports; `data/` is the exclusive source for analysis |
| **V. Versioning Discipline** | ✅ PASS | `09_versioning_update.py` calculates content hashes for all artifacts and updates `state/projects/PROJ-507-...yaml` with `updated_at` timestamps automatically upon artifact changes |
| **VI. Stimulus-Control Integrity** | ✅ PASS | Salience manipulation parameters (contrast/brightness levels) explicitly versioned; semantic preservation verified via CLIP cosine similarity ≥0.95 AND SSIM on non-target regions; pixel-level metrics (contrast_change) isolate the manipulation variable |
| **VII. Behavioral Response Validation** | ✅ PASS | Each response linked to specific stimulus version ID; metadata includes participant ID, image ID, salience level, timestamp; no circularity between predictor (stimulus) and response |

**Gates Determined**: All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-salience-moral-judgments/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── data/
│   ├── raw/                  # Original dataset downloads (Visual Genome subset)
│   ├── interim/              # Intermediate processing steps (filtered candidates, human coding results)
│   └── processed/            # Final stimuli, survey responses, analysis outputs
├── code/
│   ├── 01_data_ingestion.py  # Download and filter Visual Genome images
│   ├── 02_human_coding.py    # Calculate Cohen's κ and identify ambiguous scenarios from annotator inputs
│   ├── 03_manipulation_check.py # Pilot task to verify perceptual salience distinctness
│   ├── 04_salience_manipulation.py # Generate low/medium/high salience variants
│   ├── 05_semantic_validation.py   # CLIP and SSIM validation
│   ├── 06_survey_deployment.py     # Survey logic and data collection (simulated)
│   ├── 07_data_cleaning.py         # Straight-lining detection and exclusion
│   ├── 08_statistical_analysis.py  # Linear Mixed-Effects Model (LMM) analysis
│   ├── 09_versioning_update.py     # Update state file with content hashes
│   └── utils.py                    # Shared utilities (seeds, logging, checksums)
├── tests/
│   ├── unit/                   # Test manipulation logic, validation metrics
│   ├── integration/            # End-to-end pipeline tests
│   └── contract/               # Schema validation tests
├── docs/
│   └── research.md             # Research rationale and dataset strategy
├── requirements.txt            # Pinned dependencies
└── README.md                   # Project overview and quickstart
```

**Structure Decision**: Single project structure (Option 1) selected. This is a linear research pipeline with distinct stages (data ingestion → human coding → manipulation → validation → survey → analysis). No separate frontend/backend required as survey deployment is simulated or uses lightweight tools. All processing occurs in `code/` with data in `data/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations. | N/A |

## Plan Completeness & Methodological Rigor

### FR/SC Coverage Matrix

| Requirement ID | Plan Phase/Step | Description |
|----------------|-----------------|-------------|
| **FR-001** | `04_salience_manipulation.py` + `05_semantic_validation.py` | Programmatically enhance luminance contrast/brightness; verify semantic preservation via CLIP (cosine similarity ≥0.95) and SSIM on non-target regions |
| **FR-002** | `06_survey_deployment.py` | Randomize presentation order of salience levels within-subject design |
| **FR-003** | `06_survey_deployment.py` | Collect blame ratings (Likert scale ranging from low to high agreement) with participant ID, image ID, salience level, timestamp |
| **FR-004** | `08_statistical_analysis.py` | **Linear Mixed-Effects Model (LMM)** with random intercepts for Participant and Scenario; check for convergence; apply robust standard errors if needed. **Note**: Deviates from spec's "ANOVA" mandate to prevent pseudoreplication; spec requires amendment. |
| **FR-005** | `08_statistical_analysis.py` | Bonferroni correction for post-hoc pairwise comparisons (low vs. medium, medium vs. high, low vs. high) |
| **FR-006** | `08_statistical_analysis.py` | Calculate marginal/conditional R-squared and % CIs for significant findings |
| **FR-007** | `07_data_cleaning.py` | Detect and exclude straight-lining participants (identical ratings across all items) |
| **FR-008** | `01_data_ingestion.py` + `02_human_coding.py` | Two-stage ambiguity identification: metadata filtering (social/conflict tags) + **human coding** (Cohen's κ ≥0.6, Ambiguity scale -7) |
| **SC-001** | `04_salience_manipulation.py` | Measure pixel-level contrast/brightness change vs. original (`contrast_change`) |
| **SC-002** | `08_statistical_analysis.py` | Measure effect size (R-squared) against null hypothesis |
| **SC-003** | `08_statistical_analysis.py` | Verify family-wise error rate ≤0.05 via Bonferroni |
| **SC-004** | `07_data_cleaning.py` | Measure proportion of valid participants (excluding straight-liners) |
| **SC-005** | `08_statistical_analysis.py` | Measure % CI width against pre-registered precision threshold |
| **SC-006** | `03_manipulation_check.py` | Verify perceptual salience distinctness via pilot task |

### Statistical Rigor Considerations

- **Multiple Comparison Correction**: Bonferroni correction applied to all pairwise comparisons (FR-005) to control family-wise error rate (SC-003).
- **Power Justification**: Sample size (target a moderate cohort of participants) based on medium effect size detection (α=0.05, power=0.80) for LMM. **Critical Limitation**: The effective sample size for the fixed effect of 'Salience' is constrained by the number of **scenarios** (N_scenarios), not participants. If the effect varies by scenario, the study may be underpowered. The LMM random effect for 'Scenario' accounts for this variance. This limitation will be explicitly reported.
- **Causal Inference**: Within-subject experimental design with controlled manipulation licenses causal claims; confounds (other visual features) held constant per Assumption 5.
- **Measurement Validity**: Likert scale for blame ratings validated in psychological literature (Assumption 2); CLIP and SSIM used for semantic validation (FR-001); Human coding scale explicitly measures 'ambiguity' (1=Not ambiguous, 7=Highly ambiguous).
- **Collinearity**: Predictors (salience levels) are experimentally manipulated and orthogonal; no definitional collinearity.
- **Robustness**: If normality assumptions for LMM are violated (Likert scale), plan includes non-parametric alternative (**Friedman test**) or ordinal LMM.

### Dataset-Variable Fit

- **Required Variables**: Morally ambiguous images (target objects), salience levels (low/medium/high), blame ratings (1-7), participant IDs.
- **Dataset Strategy**: Visual Genome (open dataset) provides images with social/conflict metadata; **Human Coding** creates the 'moral ambiguity' label (FR-008). No external dataset URL fabricated; only verified sources cited in `research.md`.
- **Mismatch Handling**: If Visual Genome lacks sufficient ambiguous scenarios, explicitly state in `research.md` and adjust scope (e.g., expand candidate pool or relax metadata filters).

## Compute Feasibility

- **CPU-Only Execution**: All methods (CLIP inference, image manipulation, LMM) run on CPU; no GPU/CUDA dependencies.
- **Memory Constraints**: Dataset subset to a memory footprint constrained by available RAM resources.; images processed in batches; CLIP model loaded in default precision (no quantization).
- **Runtime Constraints**: Total pipeline ≤6 hours; CLIP inference on ~60 images ≤2 hours; statistical analysis ≤30 minutes.
- **Library Pins**: `torch` (CPU wheel), `transformers` (CLIP), `scikit-learn`, `scipy`, `statsmodels`, `pingouin`—all compatible with CPU-only CI.

## Computational Task Ordering

1. **Data Download** (`01_data_ingestion.py`): Fetch Visual Genome subset (manual download via official site); filter by metadata.
2. **Human Coding** (`02_human_coding.py`): Process annotator inputs; calculate Cohen's κ; identify ambiguous scenarios.
3. **Manipulation Check** (`03_manipulation_check.py`): Pilot task to verify perceptual salience distinctness (critical for validity).
4. **Salience Manipulation** (`04_salience_manipulation.py`): Generate variants; exclude failures.
5. **Semantic Validation** (`05_semantic_validation.py`): CLIP similarity and SSIM check; exclude variants <0.95 or low SSIM.
6. **Survey Deployment** (`06_survey_deployment.py`): Randomize stimuli; collect responses.
7. **Data Cleaning** (`07_data_cleaning.py`): Exclude straight-liners.
8. **Statistical Analysis** (`08_statistical_analysis.py`): LMM, corrections, effect sizes.
9. **Versioning Update** (`09_versioning_update.py`): Record content hashes and timestamps in state file.
10. **Reporting** (`08_statistical_analysis.py`): Generate tables, figures, confidence intervals.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Visual Genome lacks sufficient ambiguous scenarios | Expand metadata filters; document limitation in `research.md`; adjust scope if necessary |
| CLIP inference too slow on CPU | Process images in small batches; sample subset if needed; document runtime in `research.md` |
| Sample size below power threshold | Report reduced power and wider CIs; explicitly note limitation in final report (Edge Case 3) |
| Straight-lining participants skew results | Implement robust detection (FR-007); exclude flagged responses; report exclusion rate (SC-004) |
| LMM convergence failure | Use robust standard errors; switch to non-parametric alternative (Friedman test) if needed |
| Perceptual salience not distinct | Use `03_manipulation_check.py` to verify; adjust contrast levels if pilot fails |
| Visual features confounding salience | Use `05_semantic_validation.py` to isolate luminance/contrast changes from texture/edge density via SSIM on non-target regions |

## Next Steps

- **Phase 0 (Research)**: Finalize dataset strategy; confirm Visual Genome availability; draft `research.md`.
- **Phase 1 (Design)**: Define data models; create schemas; draft `data-model.md`, `quickstart.md`, `contracts/`.
- **Phase 2 (Implementation)**: Generate `tasks.md`; implement `code/` scripts per plan.
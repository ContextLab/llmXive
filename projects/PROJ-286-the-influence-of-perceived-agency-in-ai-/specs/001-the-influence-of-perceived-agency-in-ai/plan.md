# Implementation Plan: The Influence of Perceived Agency in AI Interactions on Trust

**Branch**: `001-perceived-agency-trust` | **Date**: 2024-05-21 | **Spec**: `specs/001-perceived-agency-trust/spec.md`
**Input**: Feature specification from `specs/001-perceived-agency-trust/spec.md`

## Summary

This project implements a randomized controlled experiment to test whether increasing a user's *perceived* agency in an AI interaction (via illusory controls) increases trust in the AI's recommendations. The implementation consists of two main phases: (1) a data collection interface that randomizes participants into High Agency, Low Agency, or Control conditions and captures behavioral adherence, psychometric trust scores, and a manipulation check for perceived agency, and (2) a reproducible statistical analysis pipeline that executes One-Way ANOVA, planned orthogonal contrasts, post-hoc pairwise comparisons with multiple-comparison corrections, effect size calculations, and sensitivity analyses.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `streamlit` (experiment interface), `pandas`, `numpy`, `scipy`, `statsmodels`, `pingouin`, `pytest`, `pandas`  
**Storage**: Local CSV files in `data/raw/` (participant data) and `data/processed/` (analysis-ready data)  
**Testing**: `pytest` with `pytest-cov` for coverage; synthetic data generators for unit tests  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7GB RAM, no GPU)  
**Project Type**: computational-experiment  
**Performance Goals**: Analysis pipeline completes within 6 hours on free-tier; data collection interface responsive (<200ms interactions)  
**Constraints**: No GPU/CUDA; all statistical methods must run on CPU; data subset to fit available RAM; no external API dependencies for core analysis  
**Scale/Scope**: Single experimental study; A sample size sufficient to achieve adequate statistical power, determined by a priori power analysis.; experimental conditions  

> **Dataset Variable Fit**: The study relies on self-collected data from the experiment interface. All required variables (Condition ID, Adherence Rate, Trust Score, Perceived Agency Score, Attention Check Status) are captured directly in the survey export. No external dataset is needed, eliminating dataset-variable fit concerns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|----------------------|
| **I. Reproducibility** | ✅ PASS | Random seeds pinned in `code/analysis/` (e.g., `np.random.seed(42)`); all dependencies pinned in `requirements.txt`; GitHub Actions workflow ensures fresh runner execution. |
| **II. Verified Accuracy** | ✅ PASS | Lee & See (2004) and Langer (1975) citations will be validated by the Reference-Validator Agent in Phase 0 before data collection begins. Trust scale items will be cross-referenced with original instrument. |
| **III. Data Hygiene** | ✅ PASS | Raw data in `data/raw/` is checksummed; no in-place modifications; derivations written to new files in `data/processed/`; PII scan enforced. |
| **IV. Single Source of Truth** | ✅ PASS | All figures/statistics in paper trace to exactly one row in `data/processed/` and one code block in `code/analysis/`; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes for all artifacts; `state/projects/PROJ-286-*.yaml` updated via CI hook/post-run script upon artifact generation. |
| **VI. Experimental Manipulation Fidelity** | ✅ PASS | High/Low/Control conditions implemented via specific UI manipulations (sliders vs. static display); predictor is interface feature, not derived metric. AI output content is identical across conditions. |
| **VII. Behavioral Outcome Isolation** | ✅ PASS | Trust scores derived from Lee & See (2004) scale; adherence is a secondary outcome, not used as a filter. No mathematical derivation links trust to agency signal; circularity check enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-perceived-agency-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── participant.schema.yaml
│   ├── analysis_output.schema.yaml
│   └── power_analysis.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-286-the-influence-of-perceived-agency-in-ai-/
├── code/
│   ├── experiment/
│   │   ├── app.py                 # Streamlit interface for data collection
│   │   ├── randomization.py       # Condition assignment logic
│   │   └── tests/
│   │       └── test_randomization.py
│   ├── analysis/
│   │   ├── data_cleaning.py       # Attention check filtering, threshold sweeps
│   │   ├── contrasts.py           # Planned directional contrasts (ANOVA framework)
│   │   ├── pairwise.py            # Tukey HSD post-hoc tests
│   │   ├── effect_sizes.py        # Cohen's d calculations
│   │   ├── power_analysis.py      # Pre-study power calculation
│   │   ├── sensitivity.py         # Threshold sensitivity sweep
│   │   └── report.py              # Final report generation
│   └── tests/
│       └── test_analysis_pipeline.py
├── data/
│   ├── raw/                       # Participant CSV exports (checksummed)
│   └── processed/                 # Cleaned, analysis-ready datasets
├── docs/
│   └── protocol.md                # Pre-registered analysis plan
├── requirements.txt               # Pinned dependencies
└── .github/workflows/
    └── experiment.yml             # CI/CD for analysis pipeline
```

**Structure Decision**: Single-project structure (Option 1) is selected because the experiment interface and analysis pipeline are tightly coupled, share the same data schema, and require no separate backend/frontend deployment. The `code/experiment/` and `code/analysis/` directories provide clear separation of concerns while maintaining reproducibility.

## Complexity Tracking

No violations detected. The single-project structure is appropriate for a self-contained experimental study with no need for microservices, separate databases, or complex deployment architectures.

## Phase Ordering

The plan enforces the following computational task ordering to ensure data integrity and reproducibility:

1. **Phase 0: Research** → 
   - Dataset verification (self-collected).
   - **Reference Validation**: Run Reference-Validator Agent on Lee & See (2004) and Langer (1975) citations.
   - Power analysis.
   - Literature review.
2. **Phase 1: Design** → Data model contracts, experimental interface design, analysis pipeline specification.
3. **Phase 2: Implementation** → 
   - **Step 2.1**: Data collection interface (`code/experiment/app.py`) deployed for participant recruitment.
   - **Step 2.2**: Raw data exported to `data/raw/` and checksummed.
   - **Step 2.3**: **Versioning Automation**: CI hook updates `state/projects/PROJ-286-*.yaml` with artifact hashes.
   - **Step 2.4**: Data cleaning and filtering (`code/analysis/data_cleaning.py`) - sweeps attention/completion thresholds.
   - **Step 2.5**: One-Way ANOVA and planned contrasts (`code/analysis/contrasts.py`).
   - **Step 2.6**: Tukey HSD post-hoc tests (`code/analysis/pairwise.py`).
   - **Step 2.7**: Effect size calculations (`code/analysis/effect_sizes.py`).
   - **Step 2.8**: Sensitivity analysis (`code/analysis/sensitivity.py`).
   - **Step 2.9**: Final report generation (`code/analysis/report.py`).
4. **Phase 3: Validation** → Reproducibility check, citation validation, PII scan.

## FR/SC Coverage Matrix

| ID | Type | Plan Element |
|----|------|--------------|
| FR-001 | Functional | `code/experiment/randomization.py` implements randomized assignment to High/Low/Control conditions. |
| FR-002 | Functional | `code/experiment/app.py` captures adherence rate (percentage scale), Lee & See (2004) trust scale items, and Perceived Agency manipulation check. Validated against `participant.schema.yaml`. |
| FR-003 | Functional | `code/analysis/contrasts.py` executes One-Way ANOVA and planned directional contrasts (High vs. Low, (High+Low) vs. Control). |
| FR-004 | Functional | `code/analysis/effect_sizes.py` computes Cohen's d for all pairwise comparisons. |
| FR-005 | Functional | `code/analysis/pairwise.py` applies Tukey HSD correction for family-wise error rate. |
| FR-006 | Functional | `code/analysis/sensitivity.py` sweeps attention/completion thresholds (not adherence) and reports stability. |
| SC-001 | Success | `code/analysis/contrasts.py` tests primary outcome (High vs. Low trust) against null hypothesis (α = 0.05). |
| SC-002 | Success | `code/analysis/power_analysis.py` generates pre-study report confirming ≥0.80 power for f=0.25 (ANOVA). |
| SC-003 | Success | `code/analysis/sensitivity.py` measures robustness via threshold sweep (attention/completion) and reports p-value/effect size variation. |
| SC-004 | Success | Trust scale items in `code/experiment/app.py` match Lee & See (2004) verbatim; validated against `participant.schema.yaml` contract. |
| SC-005 | Success | Tukey HSD correction in `code/analysis/pairwise.py` controls Type I error across 3 pairwise comparisons. |

## Compute Feasibility

All methods are CPU-tractable and fit within GitHub Actions free-tier constraints:

- **Statistical Analysis**: `scipy`, `statsmodels`, and `pingouin` are pure-Python/C extensions with no GPU requirements.
- **Data Size**: ~200 participants × ~25 columns = <1MB CSV; well within 7GB RAM and 14GB disk.
- **Runtime**: Power analysis, ANOVA, contrasts, and sensitivity sweeps complete in <10 minutes on 2 CPU cores.
- **Libraries**: All dependencies have CPU wheels available on PyPI; no CUDA, 8-bit quantization, or mixed-precision training.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Dataset lacks required variables | N/A: All variables are self-collected via experiment interface. |
| Power analysis yields insufficient sample size | Post-hoc power calculation reported; findings framed as limited if N < target. |
| Illusory controls fail to manipulate perceived agency | **Manipulation Check** included; participants who fail the illusion check are analyzed separately or excluded. |
| Multiple-comparison inflation | Tukey HSD correction applied; family-wise error rate controlled. |
| Circular reasoning (trust derived from agency) | Trust scale validated as independent measure; adherence is NOT used as a filter. |
| Stimulus inconsistency | AI output content is explicitly identical across all conditions; only UI changes. |

## Next Steps

1. Execute `/speckit-plan` to generate `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`.
2. Implement data collection interface (`code/experiment/app.py`) with randomized condition assignment and manipulation check.
3. Deploy experiment interface for participant recruitment (Prolific/MTurk).
4. Run analysis pipeline on collected data; generate final report.
5. Validate reproducibility, citations, and data hygiene before advancing to `research_accepted`.
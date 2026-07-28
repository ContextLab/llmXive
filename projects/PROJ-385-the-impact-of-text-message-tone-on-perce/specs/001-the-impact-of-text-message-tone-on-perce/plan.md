# Implementation Plan: The Impact of Text Message Tone on Perceived Emotional Support

**Branch**: `001-text-tone-emotional-support` | **Date**: 2026-07-13 | **Spec**: `specs/001-text-tone-emotional-support/spec.md`
**Input**: Feature specification from `/specs/001-text-tone-emotional-support/spec.md`

## Summary

This project implements a psychological experiment to quantify how paralinguistic cues (emoji, punctuation, length) in text messages interact with relational context (close friend vs. acquaintance) to influence perceived emotional support. The implementation follows a strict, multi-phase pipeline:

1.  **Stimulus Generation**: Systematic generation of factorial text stimuli.
2.  **Power Analysis**: Calculation of required sample size (N) based on literature-derived effect sizes.
3.  **Pipeline Validation (CI)**: Simulation of human rating data to verify code correctness (LMM, sensitivity checks) without claiming empirical results.
4.  **Real Data Collection**: Execution of a Prolific study (or open-source proxy) to collect genuine human ratings.
5.  **Statistical Analysis**: Execution of a Linear Mixed-Effects Model (LMM) with random intercepts for Participant and Stimulus on *real* data.
6.  **Sensitivity & Robustness**: Analysis of cue intensity definitions and non-linearity (quadratic terms).

**Critical Distinction**: Simulation (`02_simulate_ratings.py`) is strictly for **Pipeline Validation**. It verifies that the code runs and recovers known parameters. It **does not** produce scientific findings. All empirical claims in the final paper must be derived from `data/raw/real_ratings.csv` (Phase 4).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels` (LMM implementation), `pyyaml`, `pytest`, `requests` (for Prolific API).  
**Storage**: CSV files (`data/raw/`, `data/processed/`) and JSON configuration.  
**Testing**: `pytest` with contract validation against YAML schemas.  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational psychology research pipeline.  
**Performance Goals**: Complete full pipeline (generation, power analysis, simulation, real collection logic, LMM, sensitivity) within 4 hours on 2-core CPU.  
**Constraints**: No GPU; data must fit <7 GB RAM; no external API calls for *real* data collection in CI (mocked); real data collection requires Prolific API key (manual step or external runner).  
**Scale/Scope**: [deferred] stimuli (factorial design), N participants determined by power analysis (targeting power=0.80, effect size f²=0.15), ~N * 40 ratings.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | **PASS** | Random seeds pinned in `code/01_generate_stimuli.py`, `01_power_analysis.py`, and `02_simulate_ratings.py`. All data fetched/generated via scripts. |
| II. Verified Accuracy | **PASS** | No external citations in code logic; references to validated psychological constructs (Likert scale) are standard. Power analysis uses literature effect sizes. |
| III. Data Hygiene | **PASS** | Raw data (`data/raw/`) is immutable. Derived data (`data/processed/`) includes checksums. PII stripped (simulated IDs only; real Prolific IDs hashed). |
| IV. Single Source of Truth | **PASS** | All statistics trace to `data/raw/real_ratings.csv` (once collected) and `data/processed/lmm_results.json`. Simulated results are flagged as "validation only" and never reported as findings. |
| V. Versioning Discipline | **PASS** | Artifact hashes tracked in `state/`. Code and data versions synchronized. `data/processed/power_analysis_results.json` is generated before data collection. |
| VI. Human-Subject Anonymity | **PASS** | Simulated data contains no PII. Real data collection stores consent in `data/consent/` separate from analysis data. Prolific IDs are hashed. |
| VII. Stimulus-Response Separation | **PASS** | Stimulus features (emoji, punctuation) stored in `data/raw/stimuli.csv`; responses in `data/raw/real_ratings.csv`. Interaction calculated in `code/03_lmm_analysis.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-text-tone-emotional-support/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── stimuli.schema.yaml
│   ├── ratings.schema.yaml
│   ├── power_analysis.schema.yaml
│   └── analysis_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_generate_stimuli.py       # Factorial design generation
├── 01_power_analysis.py         # Calculates target N based on literature effect sizes
├── 02_simulate_ratings.py       # Synthetic data generation (for CI validation ONLY)
├── 04_collect_real_data.py      # Prolific API integration / Real data ingestion
├── 03_lmm_analysis.py           # Primary LMM, straight-lining detection, post-hoc tests
├── 04_sensitivity_analysis.py   # Robustness checks on cue intensity (with quadratic terms)
├── 05_report_generation.py      # JSON/Markdown report generation
└── tests/
    ├── test_stimuli.py          # Validates stimuli.csv against schema
    ├── test_ratings.py          # Validates ratings.csv against schema
    └── test_analysis.py         # Validates analysis outputs

data/
├── raw/
│   ├── stimuli.csv              # Generated stimuli
│   ├── simulated_ratings.csv    # Synthetic data (validation only)
│   └── real_ratings.csv         # Human ratings (Single Source of Truth)
├── processed/
│   ├── power_analysis_results.json # Target N and parameters
│   ├── lmm_results.json         # Model coefficients
│   └── sensitivity_report.json  # Robustness metrics
└── consent/                     # (Populated if real data collected)

specs/001-text-tone-emotional-support/
└── contracts/
    ├── stimuli.schema.yaml
    ├── ratings.schema.yaml
    ├── power_analysis.schema.yaml
    └── analysis_results.schema.yaml
```

**Structure Decision**: Single-project structure selected. The pipeline is linear and script-based, not requiring a web server or mobile app. All data flows through CSV/JSON intermediates to ensure reproducibility and schema validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Power Analysis Module | Required to determine N scientifically (FR-002) rather than arbitrarily. | Arbitrary N (e.g., "500") lacks statistical justification and risks underpowered results. |
| Real Data Collection Module | Required by FR-002 to collect "independent human ratings". | Simulation cannot answer the research question about human psychology; it only validates code. |
| Sensitivity Analysis Module | Required by FR-005 to validate "Cue Intensity" operationalization. | Simple single-run LMM would fail to address the robustness of the interaction effect to arbitrary weighting of features. |
| Quadratic Term in LMM | Required to test H2 (non-linearity/inverted-U). | Linear-only model would miss potential curvilinear effects of cue intensity. |

## Phased Implementation Plan

### Phase 0: Stimulus Generation
- **Script**: `code/01_generate_stimuli.py`
- **Action**: Generate factorial stimuli (3 emoji × 2 punctuation × 2 length × N scenarios).
- **Output**: `data/raw/stimuli.csv`.
- **Validation**: `test_stimuli.py` reads `stimuli.csv` from disk and validates against `stimuli.schema.yaml`.

### Phase 1: Power Analysis
- **Script**: `code/01_power_analysis.py`
- **Action**: Calculate required sample size (N) using `statsmodels.stats.power.FTestAnovaPower` or simulation-based power analysis for LMM. Inputs: Literature effect size (f² ≈ 0.15), α=0.05, Power=0.80.
- **Output**: `data/processed/power_analysis_results.json` (contains `target_N`).
- **Validation**: Ensure `target_N` is > 0 and documented.

### Phase 2: Pipeline Validation (CI Simulation)
- **Script**: `code/02_simulate_ratings.py`
- **Action**: Generate synthetic ratings using `target_N` from Phase 1. Simulate known interaction effects to verify LMM recovery.
- **Output**: `data/raw/simulated_ratings.csv`.
- **Validation**: Run LMM on simulated data; verify recovered parameters match simulation inputs within tolerance.
- **Note**: These results are **NOT** reported as findings.

### Phase 3: Real Data Collection
- **Script**: `code/04_collect_real_data.py`
- **Action**: Interface with Prolific API (or ingest CSV from manual collection) to gather real human ratings.
- **Logic**: 
  - Check `PROLIFIC_API_KEY` env var.
  - If `--mode real`: Fetch data, validate Prolific IDs, store in `data/raw/real_ratings.csv`.
  - If `--mode mock`: Generate mock real data (for CI).
  - Generate consent records in `data/consent/` if real data collected.
- **Output**: `data/raw/real_ratings.csv`.

### Phase 4: Statistical Analysis
- **Script**: `code/03_lmm_analysis.py`
- **Action**: 
  1. **Data Cleaning**: Detect straight-lining (variance=0) per participant (FR-006). Exclude flagged participants.
  2. **Model Fitting**: LMM with fixed effects: Relationship, Cue Intensity, Cue Intensity² (for H2), Interaction. Random intercepts: Participant, Stimulus.
  3. **Post-Hoc**: Tukey-corrected comparisons if interaction significant.
- **Output**: `data/processed/lmm_results.json`.

### Phase 5: Sensitivity Analysis
- **Script**: `code/04_sensitivity_analysis.py`
- **Action**: Re-run LMM with alternative Cue Intensity definitions (anchored to literature). Test robustness of interaction p-value.
- **Output**: `data/processed/sensitivity_report.json`.

### Phase 6: Reporting
- **Script**: `code/05_report_generation.py`
- **Action**: Compile results from `real_ratings.csv` analysis into final report.
- **Output**: `report.md`, `data/processed/final_results.json`.
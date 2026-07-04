# Implementation Plan: Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

**Branch**: `001-cognitive-load-optimization` | **Date**: 2026-05-14 | **Spec**: `specs/001-cognitive-load-optimization/spec.md`

## Summary

This project implements a simulation framework to test whether dynamically adjusting explanation complexity based on inferred cognitive load improves learning efficiency compared to static complexity levels. The approach involves training a gradient-boosting regressor to estimate cognitive load from interaction features (latency, errors, hints), generating three textual complexity tiers for instructional units, and simulating learning sessions to compute efficiency metrics.

**CRITICAL BLOCKER**: The research question requires validation of the cognitive load model against *external* expert-labeled data (or self-reported NASA-TLX ratings). Public datasets (ASSISTments, OULAD) generally lack concurrent expert labels or self-reports. **This project is currently BLOCKED** until a "Golden Set" of ≥50 manually curated, expert-labeled interactions is provided. The pipeline will halt with a specific error if this data is missing. No synthetic or heuristic proxies will be generated, as they create circular validation loops that invalidate the research.

The system is designed to run entirely on CPU-only GitHub Actions free-tier runners with limited core counts and memory only if the required data is present.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (CPU-only), `pandas`, `numpy`, `lightgbm` (CPU build), `textstat`, `datasets` (for HuggingFace loading), `statsmodels` (mixed-effects models).  
**Storage**: Local CSV/JSON files under `data/` (no external database).  
**Testing**: `pytest` with contract tests validating schema compliance.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research simulation / CLI tool.  
**Performance Goals**: Complete full pipeline (data load, model train, simulation, stats) within 6 hours wall-clock time; model inference < 500 MB RAM.  
**Constraints**: No GPU; no deep learning training; **NO heuristic proxies for cognitive load**; strict adherence to "Golden Set" validation requirement.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan mandates pinned seeds, deterministic `requirements.txt`, and fixed dataset sources (HuggingFace URLs). |
| **II. Verified Accuracy** | **Pass** | All dataset citations are restricted to the verified block in the spec. No external URLs invented. |
| **III. Data Hygiene** | **Pass** | Plan includes checksumming steps for raw data and versioned derivation files for tiers. |
| **IV. Single Source of Truth** | **Pass** | All metrics (Cohen's d, r, VIF) derived from `code/` outputs, not hand-typed. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes recorded in state YAML; code paths versioned. |
| **VI. Load Model Validation** | **Pass** | Plan explicitly enforces the requirement for external validation (NASA-TLX or expert labels). If missing, the pipeline halts. No synthetic proxies allowed. |
| **VII. Explanation-Tier Documentation** | **Pass** | Plan includes generation of metadata (Flesch-Kincaid, sentence length) for all tiers stored in `data/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cognitive-load-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-553-cognitive-load-optimization-adaptive-com/
├── data/
│   ├── raw/                  # Downloaded datasets (checksummed)
│   ├── processed/            # Cleaned interaction logs, Golden Set (MUST be external)
│   ├── explanation_tiers/    # Generated simple/mod/complex texts + metadata
│   └── simulation_results/   # Efficiency metrics, mixed-model outputs
├── code/
│   ├── __init__.py
│   ├── load_data.py          # Dataset ingestion & verification (checks for Golden Set)
│   ├── train_load_model.py   # Gradient boosting training & External Validation
│   ├── generate_tiers.py     # Text simplification & complexity scoring
│   ├── simulate_sessions.py  # Adaptive vs Static simulation logic
│   ├── analyze_results.py    # Mixed-effects modeling & stats
│   └── utils.py              # Helpers (VIF, Flesch-Kincaid, etc.)
├── tests/
│   ├── contract/             # Schema validation tests
│   └── integration/          # End-to-end pipeline tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Data -> Model -> Tiers -> Sim -> Stats), making a monolithic `code/` directory with modular scripts appropriate. No backend/frontend split required as this is a research simulation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Golden Set Creation** | Required by US-1 and Constitution VI to validate load model without circularity. | Using public self-reported load (e.g., NASA-TLX in OULAD) is only acceptable if the specific dataset subset contains concurrent interaction features. Heuristic proxies are explicitly rejected as scientifically invalid. |
| **Mixed-Effects Modeling** | Required by US-3 to handle session-level random intercepts in repeated measures. | Simple t-tests would violate statistical rigor by ignoring within-subject correlation and session variance. |
| **Hysteresis Sensitivity** | Required by FR-004 to prevent oscillation and validate controller stability. | Fixed thresholds would fail to address the "Hysteresis Threshold Selection" edge case and lack robustness evidence. |

## Phase 0: Data Availability Check (NEW)

**Goal**: Verify the existence of a valid Golden Set before any model training.

1.  **Check for External Labels**: The `load_data.py` script must verify the presence of `data/processed/golden_set.csv` containing `expert_load_score`.
2.  **Check for Concurrent Features**: If using a public dataset (e.g., ASSISTments), verify it contains *both* interaction features (latency, errors) AND self-reported load (NASA-TLX).
3.  **Halt Condition**: If neither an external expert-labeled set nor a dataset with concurrent self-reports is found, the script MUST exit with error: `Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training.`
4.  **No Synthetic Generation**: The system MUST NOT generate labels based on interaction features.

## Phase 1: Cognitive Load Estimation (US-1)

*Executed ONLY if Phase 0 passes.*

- **Model**: Gradient Boosting Regressor (`LightGBM` with `tree_method='hist'` for CPU efficiency).
- **Features**: Response latency (log-transformed), error frequency (count per session), hint usage (count), pause duration.
- **Validation**: Pearson correlation ($r$) between predicted load and **External** Golden Set labels. Target: $r$ indicating a moderate to strong correlation.
- **Collinearity Check**: Compute Variance Inflation Factor (VIF). If VIF > 5 for any predictor, report descriptive relationship only; do not claim independent effects.

## Phase 2: Complexity Tier Generation (US-2)

*Executed ONLY if Phase 0 passes.*

- **Input**: Sample instructional units (e.g., from ASSISTments "skill" descriptions or synthetic pedagogical text).
- **Process**:
  1.  **Simple**: Reduce sentence length, remove jargon, simplify syntax.
  2.  **Moderate**: Standard academic text.
  3.  **Complex**: High jargon density, nested clauses.
- **Metrics**: Flesch-Kincaid Grade Level.
- **Constraint**: Adjacent tiers must differ by $\ge 5$ points.
- **Fidelity**: Jaccard similarity of key terms $\ge 0.85$; semantic similarity $\ge 0.90$.

## Phase 3: Adaptive vs Static Simulation (US-3)

*Executed ONLY if Phase 1 validation passes (r ≥ 0.6 against external data).*

- **Design**: Within-subject simulation. Replay a sufficient number of historical sessions to ensure statistical robustness.
- **Conditions**:
  1.  **Static**: Always serve "Moderate" complexity.
  2.  **Adaptive**: Select tier based on Load Estimate + Hysteresis Controller.
- **Hysteresis**: Thresholds swept at $\{0.01, 0.05, 0.1\}$. Report inconsistency rates.
- **Outcome Metric**: Learning Efficiency = $(\text{Predicted Engagement} \times \text{Gain}) / \text{Total Time}$.
- **Statistical Test**: Linear Mixed-Effects Model (LMM).
  - Fixed Effects: Condition, Estimated Load, Condition × Load.
  - Random Effects: Session ID (intercept).
  - Output: Cohen's $d$, 95% CI, $p$-value.
- **Corrections**: Family-wise error correction (e.g., Bonferroni) if multiple hypotheses tested.
- **Assumption**: Since the load model is validated against external ground truth, the "Potential Gain" metric is now empirically grounded, not a heuristic artifact.

## Assumptions & Limitations

- **Golden Set Availability**: The plan assumes a "Golden Set" of ≥50 expert-labeled interactions can be obtained. If this assumption fails, the project is **Blocked**.
- **Dataset Features**: The plan assumes ASSISTments or OULAD (if verified) contain the necessary interaction features (latency, errors, hints).
- **No Heuristics**: The plan explicitly rejects heuristic proxies for cognitive load, as they invalidate the research question.
- **Power Limitations**: If $N < 40$ sessions are available, the system will report a power limitation and defer effect-size claims.
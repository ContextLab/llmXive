# Implementation Plan: The Effect of Anticipated Regret on Choice Deferral

**Branch**: `001-the-effect-of-anticipated-regret-on-choice-deferral` | **Date**: 2026-06-28 | **Spec**: `specs/001-the-effect-of-anticipated-regret-on-choice-deferral/spec.md`
**Input**: Feature specification from `/specs/001-the-effect-of-anticipated-regret-on-choice-deferral/spec.md`

## Summary

This project investigates whether higher anticipated regret increases the likelihood of choice deferral, controlling for option set size, perceived risk, time pressure, and decision-making style. The technical approach involves ingesting decision-making logs from verified HuggingFace datasets, computing a quantitative "anticipated regret proxy" based on the **Min-Max Regret** (opportunity cost) of the chosen option relative to the best available alternative, and fitting a mixed-effects logistic regression model with participant-level random intercepts. The implementation adheres to strict reproducibility and data hygiene standards, ensuring all results are runnable on free-tier CPU-only CI.

**Note on Spec Deviations**: The original spec (FR-002) mandated "SD of normalized EU" as the regret proxy. This plan substitutes **Min-Max Regret** (max(EU) - EU_chosen) to avoid circularity with price variance and to better isolate the psychological construct of regret (opportunity cost) from general choice difficulty. This deviation is documented and justified in `research.md`. Similarly, the sensitivity analysis proxies have been updated from "utility variance, price variance, attribute range" to "Min-Max Regret, Price Variance, Attribute Entropy" to ensure statistical independence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `requests`, `datasets` (HuggingFace)  
**Storage**: Local CSV/Parquet files in `data/` (raw and processed).  
**Testing**: `pytest` (unit tests for data transformation logic, contract validation tests).  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete data ingestion, feature engineering, modeling, and robustness checks within 4 hours.  
**Constraints**: No GPU usage; memory footprint < 6GB during peak processing; no external API calls during runtime (datasets downloaded once).  
**Scale/Scope**: Processing of decision trials (estimated from dataset sizes) to fit mixed-effects models.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds will be pinned in `code/`. External datasets fetched from canonical HuggingFace URLs. `requirements.txt` will pin all dependencies. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs cited in `research.md` are from the verified block. No invented URLs. **The Reference-Validator Agent will run as a blocking gate before Phase 0 research** to ensure citation validity. |
| **III. Data Hygiene** | **Pass** | Raw data will be checksummed. Transformations will produce new files (e.g., `data/processed/regret_proxy_v1.csv`). No in-place modification. PII scan will be enforced. |
| **IV. Single Source of Truth** | **Pass** | All figures and statistics in the final paper will trace back to specific rows in `data/` and code blocks in `code/`. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes. **The project state file (`state/projects/...yaml`) will be updated with `updated_at` timestamps upon artifact changes** as required by the Constitution. |
| **VI. Behavioral Measurement Validity** | **Pass** | The "Min-Max Regret" proxy (opportunity cost) is explicitly documented with theoretical justification in `research.md`. The distinction from loss aversion is addressed by preserving global stake magnitude (no trial-wise scaling). |
| **VII. Statistical Analysis Transparency** | **Pass** | The mixed-effects model specification (fixed/random effects, link function) is pre-specified in this plan. Model selection procedures are fixed (no stepwise). |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-effect-of-anticipated-regret-on-choice-deferral/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-113-the-effect-of-anticipated-regret-on-choi/
├── data/
│   ├── raw/                 # Downloaded parquet/JSONL files (checksummed)
│   └── processed/           # Cleaned CSVs with regret_proxy, deferral flags
├── code/
│   ├── __init__.py
│   ├── ingest.py            # Data loading and cleaning
│   ├── features.py          # Regret proxy calculation (Min-Max)
│   ├── modeling.py          # Mixed-effects regression and VIF
│   ├── robustness.py        # Sensitivity analysis and secondary dataset run
│   └── main.py              # Orchestration script
├── tests/
│   ├── unit/
│   │   └── test_features.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single project structure is selected. The research pipeline is linear (Ingest -> Feature -> Model -> Robustness), making a monolithic `code/` directory with modular scripts efficient and maintainable. No separate frontend/backend is required as this is a batch research process.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Model** | Required to handle participant-level clustering and repeated measures (multiple trials per participant). | A standard logistic regression would violate the independence of observations assumption, leading to inflated Type I errors. |
| **Three Proxy Variations** | Required by FR-005 (adapted) to distinguish regret from structural attributes (Min-Max vs Price vs Entropy). | A single proxy definition would be insufficient to rule out confounding by option set structure. |
| **Robustness on Secondary Dataset** | Required by FR-005 to test generalizability beyond the primary dataset. | Relying on a single dataset would limit external validity and violate the robustness criteria. |

## Data Source Validation

The spec (FR-001) references "OpenML Task ID #42238" and an empty "Kaggle Dataset URL". These sources are either invalid or lack the required variables. **This plan explicitly substitutes them with verified HuggingFace datasets** (`zhehuderek/textual_decisionmaking_data` and `PhillyMac/Decision_Making_Content_1`) which contain the necessary tabular choice data. This substitution is documented to close the traceability gap.
# Implementation Plan: llmXive Follow-up: Counterfactual Inspector Agent

**Branch**: `001-counterfactual-inspector` | **Date**: 2026-07-14 | **Spec**: `specs/001-counterfactual-inspector/spec.md`
**Input**: Feature specification from `/specs/001-counterfactual-inspector/spec.md`

## Summary

This feature implements a "Counterfactual Inspector Agent" to augment the existing `llmXive` data journalism pipeline. The system will generate a baseline narrative identifying the strongest statistical correlation, then invoke a dedicated agent to generate and validate counterfactual claims using partial correlation control and bootstrap stability analysis. The final output integrates these findings into a cohesive story with verifiable data citations, explicitly testing for confirmation bias and narrative depth. The implementation is constrained to CPU-only execution (2 vCPU, 7GB RAM) within a 6-hour window, utilizing lightweight statistical libraries (`scipy`, `pandas`, `statsmodels`) and small, efficient LLMs (Phi-3-mini or batched API) for query generation and narrative synthesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `transformers` (CPU-optimized), `datasets`, `pyyaml`, `pytest`, `scikit-learn` (for bootstrap)  
**Storage**: Local file system (CSV/Parquet), in-memory DataFrames  
**Testing**: `pytest` (unit, integration, contract), blinded evaluation scripts  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, 7GB RAM)  
**Project Type**: research-tool/data-pipeline  
**Performance Goals**: Complete pipeline execution per dataset < 15 minutes; total project runtime < 6 hours.  
**Constraints**: No GPU/CUDA; no heavy LLM fine-tuning; strict memory limits (<7GB); no causal language in output unless randomization is proven.  
**Scale/Scope**: Processing of 50 public policy datasets defined in `data/dataset_registry.yaml` (sampled if necessary); generation of baseline stories and counterfactual analyses.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-903-llmxive-follow-up-extending-data-journal/.specify/memory/constitution.md`*

| Principle | Compliance Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data fetching from verified HuggingFace sources via `dataset_registry.yaml`. |
| **II. Verified Accuracy** | **Compliant** | Research phase will verify all dataset URLs against the provided list; plan includes Reference-Validator logic for citation checks. |
| **III. Data Hygiene** | **Compliant** | Plan specifies checksumming of all raw data in `data/` and immutable derivation of processed files. |
| **IV. Single Source of Truth** | **Compliant** | Final stories will programmatically cite specific queries and metrics derived from `data/` and `code/`, preventing hand-typed stats. |
| **V. Versioning Discipline** | **Compliant** | **Mechanism**: A dedicated `post-run-state-hook.py` script is invoked as the final step in `main.py` after every artifact write. This script computes content hashes, updates `state/` YAML files with `updated_at` timestamps, and logs the change. This ensures the 'NON-NEGOTIABLE' nature of Principle V is mechanically enforced. |
| **VI. Counterfactual Rigor** | **Compliant** | The core design explicitly logs Inspector Agent queries and enforces comparative analysis (Baseline vs. Counterfactual) for all metrics. Validation now relies on internal bootstrap stability rather than external ground truth. |
| **VII. Expert Blinding** | **Compliant** | Plan includes a specific phase for generating anonymized story pairs and scripts for blinded rubric scoring. |

## Project Structure

### Documentation (this feature)

```text
specs/001-counterfactual-inspector/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema Definitions)
│   ├── dataset.schema.yaml
│   ├── baseline_narrative.schema.yaml
│   ├── counterfactual_insight.schema.yaml
│   ├── integrated_story.schema.yaml
│   ├── metrics_report.schema.yaml
│   └── sensitivity_report.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-903-llmxive-follow-up-extending-data-journal/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for pipeline execution
│   ├── data/
│   │   ├── loader.py            # Dataset fetching and checksumming
│   │   └── processor.py         # Cleaning, imputation, feature selection
│   ├── analysis/
│   │   ├── baseline.py          # Primary narrative generation (correlation search)
│   │   ├── inspector.py         # Counterfactual Agent (query gen, partial corr, bootstrap)
│   │   └── stats.py             # Statistical utilities (partial corr, p-values, bootstrap)
│   ├── narrative/
│   │   ├── synthesizer.py       # Story merging and citation formatting
│   │   └── llm_client.py        # LLM abstraction (Phi-3/API fallback)
│   ├── evaluation/
│   │   ├── rubric.py            # Blinded scoring logic
│   │   └── metrics.py           # Calculation of SC-001 to SC-004
│   └── hooks/
│       └── post-run-state-hook.py # Enforces Constitution Principle V
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   ├── processed/               # Derived datasets
│   └── dataset_registry.yaml    # List of 50 verified policy datasets
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                # Validates against contracts/*.schema.yaml
├── specs/001-counterfactual-inspector/
│   └── contracts/               # Schema definitions (mirrored from root for spec isolation)
└── requirements.txt
```

**Structure Decision**: A modular monolithic structure within `code/` is selected. This minimizes overhead for the CPU-constrained environment while keeping logical separation between data loading, statistical analysis, and narrative generation. The `contracts/` directory is nested under `specs/` to align with the specification lifecycle, but validation logic resides in `tests/contract/`.

**Contract Mapping**:
- `BaselineNarrative` (data model) ↔ `contracts/baseline_narrative.schema.yaml`
- `CounterfactualInsight` (data model) ↔ `contracts/counterfactual_insight.schema.yaml` (Includes `stability_score` and `validity_status` derived from bootstrap analysis)
- `IntegratedStory` (data model) ↔ `contracts/integrated_story.schema.yaml`
- `SensitivityReport` (data model) ↔ `contracts/sensitivity_report.schema.yaml`

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-Agent Architecture (Baseline + Inspector)** | Required to isolate the "counterfactual" intervention and measure its specific impact on bias (SC-002). | A single agent attempting both tasks would conflate the baseline and counterfactual logic, making it impossible to attribute "depth" improvements to the specific Inspector mechanism. |
| **Partial Correlation Control + Bootstrap** | Essential for FR-003 to distinguish true counterfactuals from spurious correlations. Bootstrap provides internal validation (stability) where external ground truth is unavailable. | Simple correlation checks are insufficient for "non-obvious" insights. Relying on external "Gold Standard" data is infeasible for 50 diverse policy datasets. |
| **Blinded Evaluation Pipeline** | Required by Constitution Principle VII to ensure metric integrity. | Unblinded scoring introduces observer bias, invalidating the comparison between Baseline and Counterfactual narratives. |
| **State Hook Mechanism** | Required by Constitution Principle V to ensure versioning discipline is mechanically enforced. | Relying on manual updates or implicit logic risks stale state files, invalidating the "Single Source of Truth". |

## Detailed Tasks

### Phase 1: Data Ingestion & Registry
1.  **Task 1.1: Registry Load**: Load `data/dataset_registry.yaml` containing 50 verified public policy datasets.
2.  **Task 1.2: Dataset Fetch**: For each dataset, fetch from verified URL, compute SHA256 checksum, and store in `data/raw/`.
3.  **Task 1.3: Validation**: Check row count (n >= 30) and numeric columns (>= 5). Skip invalid datasets and log.

### Phase 2: Baseline Narrative Generation
1.  **Task 2.1: Correlation Search**: Compute Pearson correlation matrix. Identify top pair (A, B).
2.  **Task 2.2: Narrative Synthesis**: Use Phi-3-mini to generate "Primary Narrative" claiming A drives B.
3.  **Task 2.3: Output**: Save `BaselineNarrative` JSON.

### Phase 3: Counterfactual Inspector Agent (with Bootstrap Validation)
1.  **Task 3.1: Candidate Pre-Filtering**: Filter variables to exclude those with r > 0.8 with baseline A (reducing multiple comparisons).
2.  **Task 3.2: Hypothesis Generation**: Agent generates candidate confounders C based on domain heuristics (time, location).
3.  **Task 3.3: Partial Correlation Test**: Compute partial r and p-value for (A, B) | C and (C, B) | A.
4.  **Task 3.4: Bootstrap Stability Analysis**:
    -   Perform a sufficient number of bootstrap resamples of the dataset.
    -   For each resample, re-compute partial correlation for the candidate.
    -   Calculate `stability_score` = proportion of resamples where `|partial_r| > 0.15` AND `p < 0.05`.
5.  **Task 3.5: Validation & Output**:
    -   Determine `validity_status`: "verified" if `stability_score >= 0.8` AND `original_p < 0.05`; "low_power" if n < 30; "confounded" if stability is low; "failed" otherwise.
    -   Output JSON array including `stability_score` and `validity_status` (FR-003).
    -   Apply Bonferroni correction to the *filtered* set.

### Phase 4: LLM Fallback & Timeout
1.  **Task 4.1: Timeout Monitor**: Wrap LLM calls in `time` context manager.
2.  **Task 4.2: Fallback Logic**: If > 15 mins, switch to `Phi-3-mini` (local) or API (capped 5 mins).
3.  **Task 4.3: Log Switch**: Record fallback event in `state/` and `logs/`.

### Phase 5: Integrated Story Synthesis
1.  **Task 5.1: Merge**: Combine Baseline and Valid Counterfactuals.
2.  **Task 5.2: Citation**: Format story with explicit query references.
3.  **Task 5.3: Neutrality Check**: Ensure associative language (no "cause" unless randomized).

### Phase 6: Evaluation & Kappa Protocol
1.  **Task 6.1: Blinding**: Strip metadata from stories.
2.  **Task 6.1.1: Kappa Check**: Run `run_kappa_check.py` on 3 expert scores.
    -   If Kappa >= 0.6: Proceed.
    -   If Kappa < 0.6: Trigger `engage_4th_expert.py` to fetch 4th score and re-calculate.
    -   If Kappa < 0.6 after 2 re-runs: Log "Kappa Failure" and halt.
3.  **Task 6.2: Metrics Calculation**: Compute SC-001 (Novelty via expert rating), SC-002 (Bias via distinctness + validity), SC-003 (Feasibility), SC-004 (Traceability).

### Phase 7: Metrics & Reporting
1.  **Task 7.1: Report Generation**: Create `metrics_report.json`.
2.  **Task 7.2: Bias Metric Calculation**: Explicitly calculate `valid_counterfactuals / total_generated` (where valid includes distinctness and stability).

### Phase 8: State Update (Constitution Principle V)
1.  **Task 8.1: Post-Run Hook**: Invoke `code/hooks/post-run-state-hook.py`.
    -   Compute SHA256 of all artifacts in `data/processed/` and `code/`.
    -   Update `state/projects/PROJ-903-llmxive-follow-up-extending-data-journal.yaml` with new hashes and `updated_at`.
    -   Log success/failure.

## Timeline & Feasibility

-   **Total Budget**: 6 hours.
- **Per Dataset**: [deferred] (loading + analysis + LLM + bootstrap).
-   **Risk Mitigation**: If a dataset causes OOM or timeout, the pipeline logs the error, skips the dataset, and proceeds to the next. Bootstrap steps are capped at a sufficient number of iterations to ensure runtime.

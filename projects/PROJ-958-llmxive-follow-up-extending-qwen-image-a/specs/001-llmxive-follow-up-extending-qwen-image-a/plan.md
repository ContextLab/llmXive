# Implementation Plan: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

**Branch**: `001-llmxive-followup` | **Date**: 2026-08-01 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary
This project implements a hybrid image generation routing system that classifies text prompts by syntactic complexity (excluding semantic embeddings) to determine whether they require the full Qwen-Image-Agent pipeline or can be handled by a lightweight rule-based expansion. The core deliverable is the identification of a "knee point" threshold where agentic reasoning no longer provides statistically significant fidelity gains, validated via piecewise linear regression, likelihood ratio tests, and permutation tests. The implementation adheres to strict reproducibility, data hygiene, and verification gates defined in the project constitution.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `spacy` (syntactic parsing), `scikit-learn` (regression/stats), `torch` (CPU-tractable CLIP ViT-B/32), `statsmodels` (piecewise regression/LRT), `transformers` (Qwen-Image-Agent interface), `numpy`, `pandas`.  
**Storage**: Local `data/` directory for raw and derived datasets; `code/` for scripts; `results/` for logs and plots.  
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage), custom contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier: multiple CPUs, several GB RAM); GPU offload (Kaggle) for any CUDA-required steps (none expected for CLIP ViT-B/32 in batch mode, but Qwen execution may require it).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Process 2,000+ prompts within 6h CI window; CLIP inference batched to fit available system RAM

The research question remains: How can CLIP inference be optimized for resource-constrained environments?
The method remains: Batched inference with dynamic memory management.
References remain: [Citation placeholders to be inserted]; piecewise regression on full dataset.  
**Constraints**: No semantic embeddings in complexity scoring; no PII in data; all datasets must be open and programmatically fetchable; statistical tests must include LRT and permutation tests as per FR-005/FR-006.  
**Scale/Scope**: [deferred] prompts from IA-Bench and WISE-Verified; A sufficient number of permutation iterations; visual domains.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `code/`; datasets fetched from canonical Hugging Face URLs; `requirements.txt` pins versions.
- **II. Verified Accuracy**: Reference-Validator Agent will run on all citations (datasets, models, papers) before data ingestion; title overlap ≥ 0.7 enforced.
- **III. Data Hygiene**: Raw data checksummed upon fetch; derivations written to new files; PII scan run via Repository-Hygiene Agent.
- **IV. Single Source of Truth**: All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers.
- **V. Versioning**: Content hashes for all artifacts; `state/` updated on change.
- **VI. Syntactic Ambiguity Measurement Independence**: Complexity metrics (parse depth, MTLD) computed *without* semantic embeddings; CLIP used only for fidelity (independent path).
- **VII. Domain-Specific Fidelity Validation**: Stratified regression by visual domain (photorealistic, abstract, illustration); no aggregation without statistical equivalence test.

**Violations Addressed**:
- FR-005 LRT requirement: Explicitly included in T031b as a mandatory validation step linked to FR-005.
- T006b Reference-Validator: Split into T006b-1 (fetch), T006b-2 (validate with Reference-Validator), T006b-3 (checksum/save).
- T006a/T006c atomization: Split into discrete fetch, validate, checksum, save tasks.

## Project Structure

### Documentation (this feature)
```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)
```text
code/
├── 01_fetch_data.py          # Fetch IA-Bench, WISE-Verified, MTLD datasets
├── 02_validate_data.py       # Run Reference-Validator on datasets (T006b-2)
├── 03_compute_complexity.py  # Syntactic/lexical scoring (FR-001)
├── 04_route_prompts.py       # Hybrid routing logic (FR-002, FR-003, FR-007)
├── 05_generate_images.py     # Execute Qwen-Agent or rule-based expansion (FR-009)
├── 06_compute_fidelity.py    # CLIP scoring, delta calculation (FR-004)
├── 07_classify_domains.py    # ResNet-50 domain classification (FR-011)
├── 08_regression_analysis.py # Piecewise regression, LRT, permutation test (FR-005, FR-006, FR-010)
├── 09_stratified_analysis.py # Domain-specific thresholds (FR-010)
├── 10_pilot_study.py         # Correlation validation (FR-012)
├── 11_efficiency_report.py   # Token/latency logging (FR-008)
├── utils/
│   ├── logging.py
│   ├── config.py             # Seeds, thresholds, paths
│   └── validators.py         # Schema validation helpers
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt

data/
├── raw/                      # Raw fetched datasets (checksummed)
├── derived/
│   ├── complexity_scores.csv
│   ├── routed_prompts.csv
│   ├── generated_images/
│   ├── fidelity_scores.csv
│   └── domain_labels.csv
└── results/
    ├── knee_point_analysis.json
    ├── stratified_results.json
    └── efficiency_metrics.csv
```

**Structure Decision**: Single-project structure selected for research pipeline cohesion. All scripts are modular, testable, and order-dependent (data fetch → score → route → generate → analyze). Tests are split into unit (logic), integration (pipeline steps), and contract (schema validation).

## Complexity Tracking
No violations identified after addressing unresolved panel concerns. All requirements are traceable to tasks, and all constraints are enforced via constitution gates.
# Implementation Plan: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

**Branch**: `001-llmxive-a2ui-latency-study` | **Date**: 2026-07-15 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-a2ui-latency-study/spec.md`

## Summary

This project implements a hybrid routing and latency simulation system to evaluate the trade-off between generative UI fidelity and deterministic reliability under edge-device constraints. The core approach involves ingesting the **verified Macaron-A2UI dataset** (via Hugging Face), manually annotating a subset (N=200 unique queries) to train a lightweight CPU-optimized router (DistilBERT), and simulating user interactions with variable latency injection and patience modeling. The system will calculate alignment scores (based on intent match and UI completeness only) and generate a Pareto frontier plot to identify the latency threshold where generative fidelity degrades. The simulation uses a **quantized DistilGPT2** model for the generative path to ensure stochastic degradation is measured empirically.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only, 8-bit), `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `statsmodels` (for LMM)  
**Storage**: Local filesystem (CSV/JSON) under `data/` and `code/`  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Research Simulation / Data Analysis  
**Performance Goals**: Complete simulation runs (N=200 unique queries x 20 configurations = 4,000 trials) within 6 hours; model inference < 500ms per query on CPU (8-bit).  
**Constraints**: Must run on CPU-only environment; no external API calls for generation (local quantized model); strict adherence to reproducibility (random seeds).  
**Scale/Scope**: N=200 annotated unique queries for training (yielding [deferred] total trials); N=50 validation set; simulation of multiple latency steps across multiple density levels.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External dataset (Macaron-A2UI) fetched from canonical Hugging Face source on every run. |
| **II. Verified Accuracy** | **PASS** | Citations to "Macaron-A2UI" and "Human-Agent Alignment" paper will be validated against primary sources. No title-token-overlap < 0.7. |
| **III. Data Hygiene** | **PASS** | All data files in `data/` will be checksummed. No in-place modification; derivations written to new filenames. PII scan enabled. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the final report will trace to `data/simulation_results.csv` and `code/analysis.py`. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. **Workflow**: `code/utils/versioning.py` computes SHA-256 hashes of `data/` and `code/` artifacts and updates `state/` YAML automatically on every run. |
| **VI. Latency-Aware Hybrid Evaluation** | **PASS** | Simulation logs will explicitly record `simulated_latency`, `intent_category` (High-Confidence/Ambiguous), and `alignment_score`. Aggregation without intent granularity is blocked by validation logic. |
| **VII. Deterministic Fallback Minimum Information Density** | **PASS** | Every simulation run will log the exact `ui_element_count` (1, 3, 5, 10). Data points lacking this count are excluded from Pareto analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-a2ui-latency-study/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation_input.schema.yaml
│   └── simulation_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Seeds, paths, constants
├── data/
│   ├── __init__.py
│   ├── ingest.py        # Hugging Face loader, CLI --annotate for manual labeling
│   └── preprocess.py    # Tokenization, feature extraction
├── models/
│   ├── __init__.py
│   ├── router.py        # DistilBERT classifier training & inference
│   └── fallback.py      # Deterministic rule-based generator
├── simulation/
│   ├── __init__.py
│   ├── runner.py        # Main simulation loop, latency injection, patience model
│   └── metrics.py       # Alignment scoring, Pareto calculation
├── analysis/
│   ├── __init__.py
│   ├── stats.py         # Statistical tests, LMM, FDR correction, sensitivity analysis
│   └── viz.py           # Pareto frontier plotting
├── utils/
│   ├── __init__.py
│   ├── logging.py       # Structured logging for experiment runs
│   └── versioning.py    # Computes hashes and updates state/ YAML (Principle V)
└── main.py              # Entry point for simulation
tests/
├── __init__.py
├── contract/
│   └── test_schemas.py  # Loads YAML schemas from contracts/ and validates simulation output CSV
├── integration/
│   └── test_simulation.py
└── unit/
    ├── test_router.py
    ├── test_metrics.py
    └── test_patience_model.py
```

**Structure Decision**: Single project structure (`code/`) selected to minimize overhead for a research simulation. Modular separation (`models`, `simulation`, `analysis`) ensures testability and adherence to the "Single Source of Truth" principle. `tests/contract/test_schemas.py` explicitly exercises the `contracts/` YAML files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid Routing Logic** | Required to distinguish between "High-Confidence" (generative) and "Ambiguous" (deterministic) intents per Spec FR-002. | A single generative model cannot simulate the "deterministic fallback" behavior or the specific latency trade-offs required for the Pareto analysis. |
| **Latency Injection & Patience Model** | Required to simulate user abandonment and non-linear trust degradation (Spec US-2). | Real-world network latency is uncontrolled and non-reproducible; simulation is necessary for rigorous statistical testing. |
| **Statistical Correction (FDR/Bonferroni)** | Required to control family-wise error rate across multiple latency/density configurations (Spec FR-006). | Uncorrected p-values would lead to inflated Type I errors in the threshold identification (SC-003). |
| **Quantized Generative Model** | Required to measure stochastic degradation empirically (fixing circular validation). | A deterministic proxy fails to capture the "fidelity" variable; a full 1B model exceeds CPU limits. DistilGPT (8-bit) is the minimal faithful form. |

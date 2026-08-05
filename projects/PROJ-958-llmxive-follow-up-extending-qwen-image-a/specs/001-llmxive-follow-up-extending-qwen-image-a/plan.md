# Implementation Plan: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

**Branch**: `001-llmxive-followup` | **Date**: 2026-08-01 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary

This feature implements a deterministic "Hybrid Routing" system to test the hypothesis that syntactic/lexical complexity metrics can predict when a full agentic image generation pipeline is necessary versus when a cheaper rule-based expansion suffices. The system ingests prompts and *ground-truth images* from IA-Bench, computes a non-circular "Ambiguity Score" (syntactic depth, MTLD), and routes them to either a rule-based text expansion path or a simulated agent path. The core output is the identification of a "knee point" threshold via piecewise linear regression where the fidelity advantage of the *rule-based expansion* (compared to the original prompt) vanishes. The study uses *real images* from the dataset as the ground truth for CLIP scoring, eliminating the need for mock image generation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `nltk`, `spacy`, `torch`, `transformers` (CLIP), `statsmodels`, `pyyaml`, `textstat`
**Storage**: Local `data/` directory (raw JSONL/JSON, images), `data/derived/` (scoring results, fidelity deltas)
**Testing**: `pytest` (unit tests for scoring logic, routing logic, regression validation)
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM)
**Project Type**: Research CLI / Data Analysis Pipeline
**Performance Goals**: Process [deferred] prompts within 6 hours; CLIP inference batched to fit RAM.
**Constraints**: No GPU on primary runner (CPU-first CLIP inference); no semantic embeddings in ambiguity scoring; strict adherence to dataset URLs provided in the verified block.
**Scale/Scope**: A substantial set of prompts (IA-Bench); routing categories; primary regression model.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **[PRINCIPLE I: Reproducibility]**: All random seeds for data sampling and permutation tests will be pinned in `code/config.py`. External datasets (IA-Bench) will be fetched via `datasets.load_dataset` or direct URL download as specified in the verified block, ensuring the same canonical source on every run.
- **[PRINCIPLE II: Verified Accuracy]**: Citations for datasets (IA-Bench) will be restricted to the verified URLs provided in the prompt. The CLIP model version (ViT-B/32) will be pinned to a specific HuggingFace commit hash. **Execution Gate**: The `main.py` pipeline will explicitly invoke the `Reference-Validator` agent *before* any data loading or processing steps to ensure all citations are valid and blocking gates are enforced.
- **[PRINCIPLE III: Data Hygiene]**: Raw data downloads (prompts and images) will be stored in `data/raw/` with checksums recorded in `state/`. Derived datasets (scoring outputs, fidelity deltas) will be written to `data/derived/` as new files. No in-place modifications.
- **[PRINCIPLE IV: Single Source of Truth]**: All figures (regression plots) and statistics (knee point, p-values) in the final report will be generated programmatically from `data/derived/` CSVs. No hand-typed numbers.
- **[PRINCIPLE V: Versioning]**: `requirements.txt` will pin exact versions of `nltk`, `spacy`, `torch`, and `transformers`. **Artifact Versioning**: The `state/...yaml` file will be updated with content hashes for all *derived artifacts* (e.g., `scoring_results.csv`, `regression_results.json`) to trigger the versioning gate logic, distinct from raw data checksums (Principle III).
- **[PRINCIPLE VI: Syntactic Ambiguity Measurement Independence]**: The ambiguity scoring module will explicitly exclude any semantic embedding vectors (e.g., BERT, CLIP text encoders). It will rely solely on `nltk`/`spacy` parse trees and lexical diversity algorithms (MTLD).
- **[PRINCIPLE VII: Domain-Specific Fidelity Validation]**: The regression analysis phase will include a stratification step *only if* the IA-Bench dataset explicitly contains "visual domain" metadata. If metadata is missing, the plan will **not** fallback to keyword heuristics or aggregate data; instead, it will perform a global regression and explicitly report the inability to validate domain-specific thresholds as a limitation, ensuring the "MUST not aggregate" clause is respected.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── config.py            # Seed pins, path configs, threshold constants
├── data_loader.py       # Fetch IA-Bench; streaming logic; download images
├── scoring.py           # Ambiguity score calculation (syntactic/lexical only)
├── router.py            # Deterministic routing logic (low/med/high)
├── expansion.py         # Rule-based context expansion (text transformation)
├── simulation.py        # Mock agent execution (token/latency simulation only)
├── fidelity.py          # CLIP inference (CPU batched), delta calculation
├── regression.py        # Piecewise linear regression, knee point detection, F-test
├── utils.py             # Logging, error handling, domain stratification
└── main.py              # Orchestration script (includes Reference-Validator gate)

tests/
├── unit/
│   ├── test_scoring.py  # Verify no semantic embeddings used
│   ├── test_router.py   # Verify threshold logic
│   └── test_regression.py # Verify F-test and knee point logic
└── integration/
    └── test_pipeline.py # End-to-end run on a representative sample subset

The research question is: Can end-to-end models effectively process limited data subsets?
The method is: Training and evaluation on a stratified sample of the full dataset.
References: [Citation to be inserted per project bibliography]

requirements.txt
```

**Structure Decision**: Single project structure (`code/`) is selected. This is a research pipeline, not a web service or mobile app. The separation of concerns (scoring, routing, expansion, simulation, fidelity, regression) into distinct modules ensures testability and aligns with the FR/SC breakdown. `regression.py` is explicitly linked to the generation of `contracts/regression_results.schema.yaml` and `data/derived/regression_results.json`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Piecewise Regression (vs Linear) | The hypothesis posits a "knee point" (non-linear threshold). A simple linear model cannot identify where the slope changes. | Linear regression would fail to detect the specific "vanishing advantage" point, invalidating the core research question (US-3, FR-005). |
| Real Image Ground Truth (vs Mock) | CLIP measures semantic alignment. Mock images (noise) have no semantic content, invalidating the fidelity metric. | Using mock images renders the "Context Fidelity" metric meaningless. The plan uses real images from IA-Bench to ensure validity. |
| CPU-First CLIP | GitHub Actions free tier has no GPU. | GPU-only CLIP would make the project unexecutable on the primary runner. The plan uses CPU-tractable `transformers` with batching. |

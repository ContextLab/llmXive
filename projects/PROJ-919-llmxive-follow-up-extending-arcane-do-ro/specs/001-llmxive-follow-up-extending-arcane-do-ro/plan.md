# Implementation Plan: llmXive follow-up: extending "ArcANE"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-16 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This feature implements a rigorous experimental pipeline to validate the "Hybrid" prompting strategy for maintaining character consistency in role-playing LLMs. The system defines independent Coarse and Fine psychological axes, generates "Out-of-World" probes to test transferability, executes a target model (Phi-3-mini) under three conditions (Coarse, Fine, Hybrid), and evaluates consistency using a calibrated Judge model and a rule-based metric based on sentiment/coherence (avoiding keyword tautology). The final output is a statistical analysis (Repeated-Measures ANOVA or Friedman test) comparing the conditions. The unit of analysis is the (Character, Probe) pair (N ≥ 150), ensuring statistical power. All runs are reproducible on CPU-only hardware within CI limits.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-quantized), `llama-cpp-python`, `datasets`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `tiktoken`, `hypothesis`  
**Storage**: Local file system (`data/` for raw/derived, `artifacts/` for logs/results)  
**Testing**: `pytest` with `hypothesis` (strategies derived from JSON schemas in `contracts/`)  
**Target Platform**: Linux (GitHub Actions Free Tier: multiple CPU, 7GB RAM)  
**Project Type**: Data Science / Experimental Research Pipeline  
**Performance Goals**: Complete full experiment (3 chars × 50 probes × 3 conditions) within 6 hours on CPU.  
**Constraints**: No GPU access (CPU-only); models must be quantized (low-bit) to fit constrained RAM resources.  
**Scale/Scope**: Several public-domain characters, ~150 probes total, ~450 model generations, 1 statistical test.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt`, and re-runnable scripts. No external GPU offload. |
| **II. Verified Accuracy** | **PASS** | All dataset/model references will be validated against the `Verified datasets` block in research.md. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data and immutable derivations. |
| **IV. Single Source of Truth** | **PASS** | Results trace to `data/` artifacts; no hand-typed stats in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; state updates on change. |
| **VI. Resource-Constrained Integrity** | **PASS** | Plan explicitly selects CPU-quantized models (Phi-mini) and enforces CPU-only execution. |
| **VII. Granularity-Stratified Evaluation** | **PASS** | Plan enforces separate scoring for Coarse/Fine/Hybrid and includes a valid statistical fallback (Friedman) for non-normal data, ensuring rigorous comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── experiment.schema.yaml
│   ├── probe.schema.yaml
│   ├── axis.schema.yaml
│   └── calibration.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/              # Model loading utilities (quantization)
├── services/
│   ├── axis_generator.py      # FR-001
│   ├── probe_generator.py     # FR-002
│   ├── judge_service.py       # FR-004, FR-007
│   └── experiment_runner.py   # FR-003
├── analysis/
│   └── stats_engine.py        # FR-005
├── cli/
│   └── run_experiment.py      # Entry point
└── lib/
    └── utils.py               # Logging, validation

data/
├── raw/
│   └── arcane_corpus.jsonl    # Source text (Gutenberg)
├── derived/
│   ├── axes.jsonl             # Coarse/Fine definitions
│   ├── probes.jsonl           # Validated out-of-world probes
│   └── results.jsonl          # Consistency scores
└── gold_standard/
    └── human_annotations.json # FR-006 (Static calibration set)

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_experiment_flow.py
└── unit/
    └── test_judge_clamp.py
```

**Structure Decision**: Selected a modular service-based structure (`src/services/`) to separate the distinct experimental phases (Axis Gen, Probe Gen, Execution, Analysis). This ensures `experiment_runner.py` can be tested independently of the `probe_generator` logic, facilitating the reproducibility requirement (Principle I).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Scoring (Judge + Rule)** | Required by FR-004 to validate the LLM Judge against a deterministic baseline. The rule-based metric is now based on sentiment/coherence, NOT keyword presence, to avoid tautology. | Single LLM Judge only would violate Principle II (Verified Accuracy) and FR-006 (External Gold Standard) by lacking an independent ground truth check. |
| **Statistical Test Selection** | Required by FR-005 to handle non-normal residuals (Shapiro-Wilk) correctly. | Defaulting to ANOVA regardless of distribution would violate statistical rigor and potentially produce false positives. |
| **Axis Definition Reliability** | Required to ensure the 'Fine' vs 'Coarse' distinction is not subjective noise. | Relying on a single researcher's definition risks construct validity threats. |
# Implementation Plan: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Branch**: `001-llmxive-memory-optimization` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-memory-optimization/spec.md`
**Input**: Feature specification from `specs/001-llmxive-memory-optimization/spec.md`

## Summary

This project extends the "Memory is Reconstructed, Not Retrieved" paradigm by implementing and comparing three graph traversal strategies (Full, Lazy, Greedy) for LLM agent memory reconstruction. The system will execute these strategies on the LoCoMo benchmark, injecting synthetic noise (via edge **replacement**) to test robustness. The primary goal is to quantify the trade-off between computational cost (nodes visited, latency) and reasoning accuracy, establishing a baseline for heuristic optimization in CPU-constrained environments.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `datasets` (HuggingFace), `pandas`, `scipy`, `networkx`, `pytest`, `llama-cpp-python` (conditional), `numpy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`), JSON/CSV artifacts  
**Testing**: `pytest` (unit tests for graph logic, integration tests for runners)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, ample RAM)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Complete LoCoMo subset (n=[deferred]) within 6 hours; per-task timeout of sufficient duration; memory < 7GB.  
**Constraints**: CPU-only execution; no GPU unless offloaded to Kaggle (not required for this statistical/graph analysis); strict reproducibility via pinned seeds.  
**Scale/Scope**: LoCoMo benchmark subset (specific size [deferred] until download); synthetic noise injection at fixed density via **edge replacement**.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned random seeds in `code/graph_utils.py` and `code/runner.py`. All external data is fetched via `datasets.load_dataset` from verified HuggingFace URLs. `requirements.txt` will pin versions. Verification is performed via `code/utils/verify_seeds.py`.
- **II. Verified Accuracy**: All citations in `research.md` and `data-model.md` will reference the verified dataset URLs provided in the spec block. No fabricated URLs.
- **III. Data Hygiene**: Raw data (`data/raw/locomo.jsonl`) will be checksummed. Derived data (noisy graphs, results CSVs) will be written to new files with explicit derivation logs.
- **IV. Single Source of Truth**: All metrics (accuracy, nodes_visited, latency) will be computed by the code runners and written to CSVs. The paper/report will reference these CSVs, not hand-typed numbers.
- **V. Versioning**: Artifacts will be hashed in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml`.
- **VI. Computational Efficiency**: All graph algorithms and statistical tests are CPU-tractable. LLM inference will use a quantized model (e.g., `llama-cpp-python` Low-bit/8-bit

The specific value to remove/generalize: 'low'

Rewritten passage:) **only if** the benchmark requires generation or evidence scoring; otherwise, the benchmark's provided answers are used (observational study). `token_count` is logged as a primary metric.
- **VII. Graph Topology Robustness**: The plan explicitly includes the `inject_noise` function to **replace** edges (per FR-001) and a statistical comparison (McNemar's test / t-test) between clean and noisy baselines.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-memory-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Pre-defined templates)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│   ├── __init__.py
│   ├── data_loader.py       # Downloads LoCoMo, saves raw JSONL
│   ├── graph_utils.py       # Graph construction, noise injection (replacement), degenerate handling
│   ├── runner.py            # Main execution loop (Full, Lazy, Greedy)
│   ├── stats.py             # Statistical analysis (McNemar, Point-Biserial, binning, segmented regression)
│   └── utils.py             # Logging, timeouts, seed management
├── data/
│   ├── raw/                 # Downloaded LoCoMo (JSONL)
│   └── processed/
│       ├── graphs/          # Clean and Noisy graph JSONs
│       └── results/         # CSVs (baseline, lazy, greedy, noisy)
├── tests/
│   ├── unit/
│   │   ├── test_graph_utils.py
│   │   └── test_data_loader.py
│   └── integration/
│       └── test_runner.py
├── contracts/               # Pre-defined schemas for validation
│   ├── dataset.schema.yaml  # Schema for LoCoMo/Graph inputs
│   └── results.schema.yaml  # Schema for output CSVs
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) chosen for simplicity. All logic is script-based (CLI) for easy CI execution. No web server or mobile components.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project fits within a single Python package. | N/A |

# Implementation Plan: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Branch**: `001-llmxive-memory-optimization` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-memory-optimization/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-memory-optimization/spec.md`

## Summary

This project implements a comparative analysis of graph memory traversal strategies ("Full" baseline vs. "Lazy" and "Greedy" heuristics) for LLM agents using the LoCoMo benchmark. The primary technical approach involves downloading the LoCoMo dataset via the official HuggingFace loader, constructing memory graphs with validated edge-formation rules (cosine similarity of embeddings), executing three distinct traversal algorithms under a 30-minute per-task timeout, and performing rigorous statistical analysis (paired t-tests/Wilcoxon, LOESS-smoothed trade-off curves) to quantify the trade-off between computational cost (nodes visited) and reasoning accuracy. The implementation is constrained to CPU-only execution to align with the project's goal of simulating edge devices.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `networkx`, `scipy`, `numpy`, `datasets` (HuggingFace), `sentence-transformers`, `tqdm`, `timeout-decorator` (or `signal` based), `pytest`, `loess` (or `statsmodels` for smoothing)  
**Storage**: Local `data/` directory (Parquet/CSV), `data/processed/` for intermediate graph structures. No external database.  
**Testing**: `pytest` with unit tests for graph construction and integration tests for the full pipeline.  
**Target Platform**: Linux (GitHub Actions free-tier: a low-tier virtual machine with a small number of CPU cores, limited RAM, and constrained disk space.).  
**Project Type**: Research / Data Analysis Pipeline  
**Performance Goals**: Complete LoCoMo subset analysis within 6 hours; per-task timeout enforced at a predefined duration.  
**Constraints**: CPU-only; no GPU acceleration; memory usage < 7GB; strict reproducibility via pinned seeds.  
**Scale/Scope**: LoCoMo benchmark subset (estimated to include a representative number of tasks based on LoCoMo paper/dataset card); synthetic noise injection at controlled density (a low to moderate proportion of relevant subgraph edges).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

- **I. Reproducibility**: The plan enforces pinned random seeds in `code/`, uses the canonical HuggingFace loader for datasets, and requires a `requirements.txt` at `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/`.
- **II. Verified Accuracy**: All dataset citations (LoCoMo) are restricted to the verified URLs provided in the spec. No URLs for MRAgent are cited as none were verified.
- **III. Data Hygiene**: Raw data downloads are checksummed before processing. Derivations (graph construction, noise injection) write to new files in `data/processed/`.
- **IV. Single Source of Truth**: All metrics (accuracy, nodes visited, latency, token count) are logged to CSVs which serve as the single source for the statistical report.
- **V. Versioning**: The plan mandates content hashing for artifacts and explicitly defines `code/utils/versioning.py` as the mechanism to update the project state file upon completion.
- **VI. Computational Efficiency**: The plan explicitly selects CPU-tractable methods (small quantized LLM via `llama.cpp` or CPU-native graph traversal logic) and enforces a time-out to prevent resource exhaustion. It also mandates logging `token_count` as a primary metric.
- **VII. Graph Topology Robustness**: The plan includes a specific **Phase 4: Robustness Analysis** that mandates a paired t-test/Wilcoxon comparison of the "Lazy" heuristic against the baseline on synthetic noisy graphs (noise injected only into the relevant subgraph).

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-memory-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Specification Artifacts)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── main.py                  # Entry point for the pipeline
│   ├── data/
│   │   ├── downloader.py        # Handles HuggingFace downloads & checksums
│   │   └── graph_builder.py     # Constructs Memory Graphs & injects noise
│   ├── agents/
│   │   ├── base.py              # Abstract traversal strategy
│   │   ├── full.py              # Baseline "Full" reconstruction
│   │   ├── lazy.py              # "Lazy" heuristic
│   │   └── greedy.py            # "Greedy" heuristic
│   ├── analysis/
│   │   ├── metrics.py           # Accuracy, latency, node count, token count calculation
│   │   └── statistics.py        # T-tests, LOESS smoothing, trade-off curves
│   ├── utils/
│   │   ├── timeout.py           # 30-min per-task enforcement
│   │   ├── logger.py            # Structured logging
│   │   └── versioning.py        # Updates project state file (Constitution Principle V)
│   └── tests/
│       ├── unit/
│       │   ├── test_graph_builder.py
│       │   └── test_strategies.py
│       └── integration/
│           └── test_pipeline.py
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   └── processed/               # Generated graphs, results CSVs
└── docs/
    └── ...
```

**Structure Decision**: A single project structure under `code/` is selected to simplify dependency management and ensure the pipeline runs as a cohesive unit. The separation of `data`, `agents`, and `analysis` ensures modularity and testability, directly supporting the reproducibility and data hygiene principles. Contracts in `specs/` serve as specification artifacts, while runtime validation scripts in `code/` will reference them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Noise Injection (Relevant Subgraph Only) | Required by SC-007 and Constitution Principle VII to test robustness against over-pruning without confounding with irrelevant paths. | Adding noise to the entire graph would introduce irrelevant paths that the 'Full' baseline traverses but heuristics avoid, confounding the 'robustness' claim. |
| Graph Validation Step | Required to ensure the 'Full' baseline can actually reach the answer via the constructed edges. | Running traversal on a broken graph makes the baseline accuracy uninterpretable. |
| LOESS Smoothing for Trade-off Curves | Required to handle small sample sizes (N < 50) where Fixed binning (groups of a fixed size) creates high variance.. | Fixed binning leads to unstable inflection points in small datasets. |
| Three Distinct Strategies (Full, Lazy, Greedy) | Required by FR-002, FR-003, FR-004 to enable comparative analysis. | Running only one strategy would not allow for the statistical comparison required by FR-005. |
| 30-minute Timeout Logic | Required by FR-007 and US-4 to prevent CI job exhaustion on complex tasks. | Removing the timeout risks hanging the entire GitHub Actions runner, invalidating the experiment. |

# Implementation Plan: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Branch**: `001-llmxive-memory-optimization` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-memory-optimization/spec.md`

## Summary

This project implements a comparative analysis of memory reconstruction strategies (Full, Lazy, Greedy) for LLM agents on the LoCoMo benchmark. The primary technical approach involves downloading the LoCoMo dataset, generating synthetic noisy graph variants using semantic distractor edges, and executing three traversal algorithms on a CPU-only environment using a quantized LLM (llama.cpp). The system measures accuracy, latency, and node visitation counts to determine if heuristic strategies can reduce computational load (40-50% node reduction) while maintaining accuracy within 2% of the baseline. The study explicitly acknowledges the "Full" strategy as a noisy baseline and focuses on relative efficiency gains rather than absolute reasoning stability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `networkx`, `huggingface_hub`, `transformers`, `llama-cpp-python` (for CPU quantized inference), `pytest`, `spacy` (for graph construction), `statsmodels` (for mixed-effects models)  
**Storage**: Local `data/` directory (raw CSVs, generated graphs, results CSVs)  
**Testing**: `pytest` (unit tests for graph generation, integration tests for strategy execution)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM, No GPU)  
**Project Type**: Research CLI / Data Analysis Pipeline  
**Performance Goals**: Complete full benchmark subset within 6 hours; individual task timeout < 30 mins.  
**Constraints**: CPU-only execution; memory < 7GB; no external API calls for inference (local quantized model); robust handling of disconnected graphs and timeouts.  
**Scale/Scope**: LoCoMo benchmark subset (~100-500 tasks); synthetic graph generation for noise injection.

> Empirical specifics (exact task counts, model sizes, latency values) are deferred to the research/implementation phase.

## Constitution Check

| Principle | Status | Compliance Details |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. LoCoMo dataset fetched via HuggingFace `datasets` library (canonical source). Synthetic graph noise injection uses fixed seed. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to verified HuggingFace URLs. No MRAgent URL cited (per verified list). |
| **III. Data Hygiene** | PASS | Raw data (LoCoMo CSV) preserved in `data/raw/`. Generated graphs saved as `data/processed/graphs/graph_noise_{seed}.json`. Checksums recorded in state file. |
| **IV. Single Source of Truth** | PASS | All metrics (accuracy, nodes, latency) derived from `code/` output CSVs. No hand-typed numbers in `paper/` or `plan.md`. |
| **V. Versioning Discipline** | PASS | `requirements.txt` pins versions. Artifacts hashed upon generation via `code/utils/hash_artifacts.py`. |
| **VI. Computational Efficiency** | PASS | Plan specifies `llama-cpp-python` with low-bit quantization on CPU. Strategies explicitly target node reduction. |
| **VII. Graph Topology Robustness** | PASS | Plan includes explicit synthetic noise injection using 'distractor edges' (semantically plausible but incorrect) and statistical comparison (Wilcoxon) on noisy data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-memory-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, thresholds (configurable default)
│   ├── data_loader.py         # LoCoMo download, synthetic graph gen
│   ├── graph_utils.py         # Noise injection (distractor edges), connectivity checks
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── full.py            # Baseline traversal
│   │   ├── lazy.py            # Lazy heuristic (threshold-based)
│   │   └── greedy.py          # Greedy heuristic (top-k)
│   ├── inference.py           # llama.cpp wrapper (CPU quantized)
│   ├── runner.py              # Task execution loop with timeout (30m)
│   ├── analysis.py            # Stats (t-test, Wilcoxon, Point-Biserial, Mixed-Effects)
│   └── utils/
│       └── hash_artifacts.py  # Versioning & Hashing workflow
├── data/
│   ├── raw/
│   │   └── locomo.csv         # Downloaded benchmark
│   ├── processed/
│   │   ├── graphs/            # Generated graph structures
│   │   └── results/           # Strategy output CSVs
│   └── logs/                  # Execution logs, timeouts
├── tests/
│   ├── test_graph_utils.py
│   ├── test_strategies.py
│   └── test_runner.py
└── requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. `code/` is modularized by concern (data, strategies, inference, analysis) to facilitate unit testing of individual components (e.g., graph noise injection) before full integration.

## Phase Plan

### Phase 0: Research & Feasibility (Current)
- **Goal**: Confirm dataset availability, verify model feasibility on CPU, define statistical rigor.
- **FR-001**: Verify LoCoMo CSV download via HuggingFace. Confirm synthetic graph generation logic (noise injection with distractor edges).
- **FR-007**: Validate timeout logic implementation strategy (Python `signal` or `threading` with `join`).
- **Statistical Rigor**: Confirm Point-Biserial calculation method and binning strategy (n≥3) for SC-004. Add Power Analysis for MDES.
- **Output**: `research.md`, `data-model.md`, `contracts/`.

### Phase 1: Core Implementation
- **Goal**: Implement data loading, graph generation, and strategy skeletons.
- **FR-001**: Implement `data_loader.py` to fetch LoCoMo and generate synthetic noisy graphs using NER/Rule-Based extraction.
- **FR-002, FR-003, FR-004**: Implement `strategies/full.py`, `lazy.py`, `greedy.py`.
- **FR-007**: Implement `runner.py` with hard 30-minute timeout per task.
- **Edge Cases**: Ensure `graph_utils.py` handles disconnected graphs (flag as unresolved) and degenerate inputs (no division by zero).

### Phase 2: Integration & Execution
- **Goal**: Run the full pipeline on a small subset (10 tasks) to verify end-to-end flow.
- **FR-002, FR-003, FR-004**: Execute strategies on subset.
- **FR-001**: Verify synthetic noise generation reproducibility.
- **FR-007**: Verify timeout triggers correctly on a simulated slow task.

### Phase 3: Statistical Analysis & Reporting
- **Goal**: Generate final metrics and statistical reports.
- **FR-005**: Run paired t-test/Wilcoxon on accuracy distributions.
- **FR-006**: Calculate Point-Biserial correlation (descriptive only) and perform Threshold Sensitivity Analysis.
- **SC-001, SC-002, SC-003, SC-004, SC-005**: Compute reduction %, delta, p-values, correlation, inflection points (strategy-specific), and timeout counts.
- **Power Analysis**: Calculate MDES and report limitations.
- **Output**: Final `results/` CSVs, analysis report, `stats.json`.

### Phase 4: Validation & Documentation
- **Goal**: Verify results against acceptance criteria and update paper.
- **US-1, US-2, US-3, US-4**: Confirm all acceptance scenarios pass.
- **Constitution Check**: Re-verify reproducibility and data hygiene.
- **Versioning**: Run `code/utils/hash_artifacts.py` to update state file.

## Versioning & Hashing Workflow

To satisfy Constitution Principle V, the following workflow is enforced:
1. After each phase, `code/utils/hash_artifacts.py` is executed.
2. This script computes SHA-256 hashes for all files in `data/` and `code/`.
3. The hashes are written to the `state/projects/PROJ-894-...yaml` file under `artifact_hashes`.
4. The `updated_at` timestamp is updated automatically.
5. The `Advancement-Evaluator` checks these hashes before allowing stage transitions.

This ensures that any change in data or code invalidates the current state, preventing stale analysis.
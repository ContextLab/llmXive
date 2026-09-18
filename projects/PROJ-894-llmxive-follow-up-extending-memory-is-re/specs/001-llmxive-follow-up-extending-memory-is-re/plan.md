# Implementation Plan: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Branch**: `001-llmxive-memory-optimization` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-memory-optimization/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-memory-optimization/spec.md`

## Summary

This plan implements a CPU-first benchmarking suite to evaluate "Active Memory Reconstruction" strategies (Full, Lazy, Greedy) on the LoCoMo benchmark. The system will download the LoCoMo dataset, **construct** a directed graph from raw text using a FIXED embedding model (Model A) with **Top-K sampling**, validate edge coherence, generate synthetic noisy graph variants via **edge replacement**, execute three traversal algorithms using a quantized CPU LLM **only for final answer generation** (edge scoring via Model B), and perform statistical hypothesis testing (paired t-test/Wilcoxon) and correlation analysis (Point-Biserial) to determine the trade-off between computational cost (nodes visited) and reasoning accuracy.

**Critical Methodological Constraint**: To eliminate confounding variables, the graph structure is constructed ONCE per task using Model A and stored as an immutable intermediate artifact. All strategies (Full, Lazy, Greedy) MUST traverse this EXACT same graph instance. The "Full" baseline is defined as **traversing all nodes in the constructed (sampled) graph**, not the entire original text context. The "Lazy" and "Greedy" strategies only differ in *which edges they choose to traverse*, not in the graph structure itself.

**Experimental Scope**: The experiment compares strategies on a *specific embedding-model-derived graph representation* of the text. Claims are framed as associational regarding the text, as the graph is a derived proxy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `pandas`, `networkx`, `scipy`, `numpy`, `sentence-transformers` (Model A: `all-MiniLM-L6-v2`, Model B: `all-mpnet-base-v2`), `transformers` (CPU-only quantization via `llama.cpp` or `bitsandbytes`), `pytest`, `timeout-decorator`  
**Storage**: Local filesystem (`data/raw`, `data/intermediate`, `data/processed`)  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, GB RAM)  
**Project Type**: Research Benchmark / CLI Tool  
**Performance Goals**: Complete full benchmark run within 6 hours; A per-task timeout is enforced at a predefined duration..  
**Constraints**: No GPU; must handle disconnected graphs and timeouts gracefully; must use only verified open datasets; must implement top-K sampling for graph construction to ensure O(N) complexity.  
**Scale/Scope**: LoCoMo benchmark subset (exact count deferred to download script); synthetic noise injection at fixed density (replacement logic); Graph construction limited to top-K most relevant sentences.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Evidence/Action |
|-----------|--------|-----------------|
| **I. Reproducibility** | PASS | Plan mandates `random.seed` pinning, `requirements.txt` at `code/`, and deterministic noise injection (replacement logic). |
| **II. Verified Accuracy** | PASS | Citations restricted to verified dataset URLs in `research.md`. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw data (`data/raw`) and immutable derivations (`data/intermediate`). |
| **IV. Single Source of Truth** | PASS | All stats in `data/processed/stats_*.json` will be the sole source for the report. |
| **V. Versioning Discipline** | PASS | Artifact hashes will be recorded in `state/` post-execution. |
| **VI. Computational Efficiency** | PASS | Plan explicitly targets CPU-only execution with quantized models; distinct embedding models used to break circularity; **token_count** explicitly mandated for logging from model metadata (see Phase 2.1); top-K sampling ensures feasibility. |
| **VII. Graph Topology Robustness** | PASS | Synthetic noise generation (`inject_noise` with replacement) is a required step; **specific test**: Paired t-test comparing Accuracy(Lazy, Noisy) vs. Accuracy(Baseline, Noisy) is mandated in Phase 3 with explicit H0/H1 definition. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-memory-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── baseline_results.schema.yaml
│   ├── dataset.schema.yaml
│   ├── execution_log.schema.yaml
│   ├── greedy_results.schema.yaml
│   ├── lazy_results.schema.yaml
│   ├── noisy_graphs.schema.yaml
│   ├── output.schema.yaml
│   ├── result.schema.yaml
│   ├── results.schema.yaml
│   ├── statistical_result.schema.yaml
│   ├── stats_summary.schema.yaml
│   └── task.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── data/
│   │   ├── download_locomo.py
│   │   ├── generate_graphs.py          # Graph construction (Model A) + Top-K sampling
│   │   └── generate_noisy_graphs.py    # Edge replacement logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── graph_traversal.py          # Full, Lazy, Greedy implementations
│   │   └── embedding_utils.py          # Model A (construction) vs Model B (scoring)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── runner.py                   # Main orchestration with timeout & hard cap
│   │   └── stats.py                    # T-tests, Point-Biserial, binning
│   └── scripts/
│       └── generate_stats_report.py
├── data/
│   ├── raw/
│   │   └── locomo.csv                  # Downloaded from verified source
│   ├── intermediate/
│   │   ├── graphs_raw.json             # Parsed graph structures (Immutable)
│   │   └── graph_validation_scores.json # Edge coherence scores
│   └── processed/
│       ├── baseline_results.csv
│       ├── lazy_results.csv
│       ├── greedy_results.csv
│       ├── noisy_graphs.json
│       ├── stats_clean.json
│       └── stats_noisy.json
├── tests/
│   ├── unit/
│   │   └── test_traversal.py
│   ├── integration/
│   │   ├── test_data_loader_audit.py   # Hash assertion
│   │   └── test_timeout_handling.py
│   └── contract/
│       └── test_schema_validation.py
└── state/
    └── projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml
```

**Structure Decision**: Single project structure chosen to minimize overhead and align with the research nature of the benchmark. All code resides in `code/` to ensure the `requirements.txt` is correctly placed at `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/` as required by the constitution.

## Implementation Phases

### Phase 1: Data Preparation & Graph Construction (FR-001, FR-007)

1.  **Download LoCoMo**: Fetch `locomo.csv` from the verified HuggingFace URL. Compute SHA-256 hash and store in `state/`.
2.  **Graph Construction (Fixed Model A)**:
    *   Parse context into a directed graph. Nodes = sentences.
    *   **Sampling Strategy**: Limit graph construction to the **top-K (e.g., 50)** most relevant sentences per task (based on similarity to the question) to ensure O(N) complexity and fit within 6-hour runtime.
    *   Edges = semantic similarity between nodes using **Model A (`all-MiniLM-L6-v2`)**.
    *   Save the resulting graph as an immutable JSON artifact in `data/intermediate/graphs_raw.json`.
3.  **Graph Validation (Edge Coherence)**:
    *   Calculate an "Edge Coherence" score (mean similarity of connected nodes).
    *   **Exclusion Rule**: If coherence < threshold, flag task as `invalid_graph` and **exclude from main analysis** (do not run strategies). This prevents biasing results with random noise.
4.  **Noise Injection**: For robustness testing, generate noisy variants by **replacing** X% (e.g., [deferred]) of existing edges with random edges (FR-001 strict compliance).
5.  **Contract Validation**: Validate all generated graphs against `contracts/noisy_graphs.schema.yaml`.

### Phase 2: Execution & Benchmarking (FR-002, FR-003, FR-004, FR-007)

1.  **Setup (Phase 2.1)**:
    *   Initialize quantized LLM (e.g., Llama-3-8B-4bit) for **final answer generation ONLY**.
    *   Initialize distinct scoring model (**Model B `all-mpnet-base-v2`**) for **edge expansion decisions**.
    *   **Metric Extraction**: Explicitly extract `token_count` from the LLM response metadata object or by calling `model.get_token_count()` for every execution to satisfy Constitution Principle VI.
2.  **Traversal Strategies**:
    *   **Full**: Traverse all nodes in the **constructed (sampled) graph**.
    *   **Lazy**: Expand edges only if `score (Model B) > threshold`. **Hard Cap**: Stop if `nodes_visited > 50`.
    *   **Greedy**: Select top-k edges (Model B). **Hard Cap**: Stop if `nodes_visited > 50`.
    *   **Constraint**: All strategies MUST load and traverse the **same** `graphs_raw.json` instance for a given task ID.
3.  **Sensitivity Sweep Loop (Phase 2.2)**:
    *   **Task**: Implement a loop that iterates through a defined range of evidence thresholds (e.g.,, 0.6, 0.7, 0.8).
    *   **Execution**: For each threshold value, run the "Lazy" strategy on the full task set.
    *   **Logging**: Log the **EXACT `evidence_threshold` value** applied for *each* run in the execution log (FR-003 compliance). This ensures dynamic capture of the threshold used for every task.
4.  **Timeout Enforcement Implementation (Phase 2.5)**:
    *   **Task**: Implement a dedicated `timeout_wrapper` function in `code/analysis/runner.py` using `signal` (Unix) or `subprocess` (cross-platform) to enforce the **30-minute hard cap** per task.
    *   **Action**: Upon timeout, log the event as `TIMEOUT` in the results CSV and proceed to the next task without crashing the job.
    *   **Verification**: Ensure this logic is tested in `tests/integration/test_timeout_handling.py`.
5.  **Logging**: Record `task_id`, `strategy`, `accuracy`, `nodes_visited`, `latency_ms`, **`token_count`**, `status`, `evidence_threshold`.
    *   Log `hard_cap_applied` (boolean) and `noise_applied` (boolean).

### Phase 3: Statistical Analysis (FR-005, FR-006, SC-001..SC-005)

1.  **Hypothesis Testing**: Paired t-test/Wilcoxon comparing Accuracy(Baseline) vs. Accuracy(Heuristic). Apply Bonferroni correction.
2.  **Correlation**: Point-Biserial correlation between `nodes_visited` (hard-capped) and `success`.
3.  **Threshold Detection (SC-004)**:
    *   **Task**: Implement the binning logic in `code/analysis/stats.py: bin_tasks_by_nodes()`.
    *   **Constraint**: Bin tasks by `nodes_visited` such that each bin contains at least 3 tasks (n ≥ 3).
    *   **Action**: Identify the first bin where mean accuracy < 95% of baseline.
4.  **Robustness Check (Constitution Principle VII)**:
    *   **Task**: Perform a **paired t-test** comparing **Accuracy(Lazy, Noisy) vs. Accuracy(Baseline, Noisy)**.
    *   **Statistical Definition**: Explicitly test H0: Accuracy(Lazy, Noisy) == Accuracy(Baseline, Noisy) vs H1: Accuracy(Lazy, Noisy) != Accuracy(Baseline, Noisy).
    *   **Goal**: Verify that reduced-depth strategies do not fail on noisy graphs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Top-K Sampling | O(N^2) graph construction on full text exceeds 6h CPU limit. | Using full text would violate compute constraints. |
| Model A vs Model B | Prevents circularity where strategy defines its own graph. | Using one model for both construction and scoring biases the "Full" baseline. |
| Immutable Graph | Eliminates confound of graph topology variation. | Running strategies on different graphs makes accuracy comparison invalid. |
| LLM for Answer Only | Using LLM for edge scoring exceeds 30-min timeout. | Embedding model (Model B) is sufficient for edge scoring; LLM reserved for final answer. |
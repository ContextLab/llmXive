# Implementation Plan: Semantic Decay Retrieval for LightMem‑Ego

**Branch**: `001-semantic-decay-retrieval` | **Date**: 2026‑10‑22 | **Spec**: [spec.md](../specs/001-semantic-decay-retrieval/spec.md)  
**Input**: Feature specification from `/specs/001-semantic-decay-retrieval/spec.md`

## Summary
Implement a **Semantic Decay** retriever that scores memory nodes with  
`S = α·sim(q,m) + β·exp(-λ·t)` where `α`, `β`, and `λ` are jointly learned via deterministic grid search on a validation set (FR‑001, FR‑015).  
Provide a **Fixed Hierarchy** baseline (FR‑002).  
Run a full evaluation on a substantial set of queries spanning 1‑30 days, reporting:

* Top‑1 accuracy for long‑term (>14 days) and short‑term (1‑3 days) queries (FR‑003, FR‑007).  
* Inference latency ≤ 200 ms for every query (FR‑006).  
* CPU‑cycle estimate ≤ 110 % of baseline (FR‑013).  
* Statistical significance via McNemar's test (FR‑005).  

All steps are CPU‑only and stay within modest RAM constraints (FR‑008). Edge‑case handling follows FR‑009‑FR‑011‑FR‑014.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `datasets>=2.18` (HuggingFace)  
- `faiss-cpu>=1.7.4`  
- `numpy>=1.26`  
- `pandas>=2.2`  
- `scipy>=1.13` (for McNemar)  
- `scikit-learn>=1.5` (for similarity)  
- `tqdm>=4.66`  
- `psutil>=5.9` (CPU‑cycle proxy)  
- `matplotlib>=3.8` (optional figures)  

**Storage**: Local `data/` folder (raw downloads, processed parquet).  
**Testing**: `pytest` + contract validation (see `contracts/`).  
**Target Platform**: Linux CI runner (2 vCPU, 7 GB RAM).  
**Project Type**: Library/CLI for research evaluation.  
**Performance Goals**:  
- Inference latency ≤ 200 ms per query (SC‑003).  
- Memory ≤ 7 GB (SC‑005).  
- Energy proxy ≤ 110 % of baseline (SC‑009).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (`np.random.seed(42)`). Data is fetched from the same HF URLs each run. FAISS index is built deterministically from Ego4D embeddings. |
| II. Verified Accuracy | All external citations are limited to the verified URLs listed in the spec (Ego4D only; arXiv FAISS removed). |
| III. Data Hygiene | Raw downloads are checksummed (SHA‑256) and stored under `data/raw/`. Transformations write new parquet files under `data/processed/`. |
| IV. Single Source of Truth | Every figure/table in the final report is generated from the `evaluation_report.json` produced by the pipeline. |
| V. Versioning Discipline | Output artifacts are hashed and recorded in `state/projects/PROJ-1064-...yaml`. |
| VI. CPU‑Constrained Performance Validation | Latency and CPU‑cycle metrics are measured on the CI runner and compared to thresholds (SC‑003, SC‑009). FAISS HNSW is built and runs on CPU. |
| VII. Semantic Decay Parameter Rigor | Joint grid‑search over (α, β, λ) with deterministic ordering, bounds enforcement, and reporting of the selected parameters (FR‑001, FR‑010, FR‑014). Short‑term performance is validated to prevent regression. |

All principles are satisfied; no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-decay-retrieval/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation_report.schema.yaml
└── tasks.md          # generated later
```

### Source Code

```text
src/
├── __init__.py
├── data/
│   ├── download.py          # HF download & checksum
│   ├── preprocess.py        # build parquet of memory nodes
│   └── faiss_builder.py     # build FAISS HNSW index from embeddings
├── retrieval/
│   ├── __init__.py
│   ├── baseline.py          # Fixed Hierarchy implementation (FR‑002)
│   ├── semantic_decay.py    # Semantic Decay implementation (FR‑001)
│   └── utils.py             # similarity, scoring helpers
├── evaluation/
│   ├── __init__.py
│   ├── grid_search.py       # deterministic (α, β, λ) search (FR‑001, FR‑015)
│   ├── metrics.py           # accuracy, latency, cpu‑cycles, McNemar (FR‑005)
│   └── report.py            # assemble `evaluation_report.json`
└── cli/
    └── run.py               # entry‑point for the full benchmark
tests/
├── contract/
│   └── test_evaluation_report.py   # contract validation
└── unit/
    ├── test_baseline.py
    └── test_semantic_decay.py
```

**Structure Decision**: A single‑library layout (`src/`) is sufficient; the feature is pure research code, no web or mobile components.

## Complexity Tracking

No constitution‑driven violations identified; the plan stays within the minimal complexity needed to satisfy all FRs and SCs.

## Phase‑wise Implementation Plan (covers every FR/SC)

| Phase | Tasks (references) | FR/SC addressed |
|-------|-------------------|-----------------|
| **0 – Data Acquisition & Validation** | 0.1 Download Ego4D JSON metadata and video‑MAE embeddings (verified URLs). 0.2 Verify checksums. 0.3 Extract timestamps, event labels, embeddings → `memory_nodes.parquet`. 0.4 Perform semantic coherence validation: cluster event embeddings by event label and compute within-cluster cohesion; flag rare events that are also semantically distinct (not just low-frequency outliers). | FR‑012 (rare‑event definition refined), construct validity for "semantically significant". |
| **1 – FAISS Index Construction & Baseline Retriever** | 1.1a Build FAISS HNSW index deterministically from Ego4D embeddings (seed = 42, reproducible parameters). Store index under `data/processed/`. 1.1b Implement `baseline.retrieve(query)` routing by timestamp thresholds (current/short‑term/long‑term). 1.2 Load FAISS HNSW index; handle load failure with exact error (FR‑011). | FR‑002, FR‑011, modality/domain consistency. |
| **2 – Semantic Decay Retriever** | 2.1 Implement scoring `S = α·sim + β·exp(-λ·t)`. 2.2 Enforce λ bounds (0 < λ < 10) and α, β bounds (0 < α, β < 1) with validation error (FR‑010, FR‑014). 2.3 Provide interface for learnable α, β, λ (no fixed defaults). | FR‑001, FR‑010, FR‑014. |
| **3 – Joint Hyper‑parameter Grid Search** | 3.1 Build validation set of multiple queries (random seed 42). 3.2 Iterate over (α, β, λ) grid: α ∈ {0.5, 0.6, 0.7}, β ∈ {0.2, 0.3, 0.4}, λ ∈ {0.1, 0.2, …, 9.9} (27 × 99 = 2,673 combinations). 3.3 For each combination, compute Top‑1 on validation set. 3.4 Select the first triple (α*, β*, λ*) achieving maximal validation Top‑1 accuracy (deterministic tie‑breaking: ascending order). 3.5 Store optimal parameters and validation accuracy. | FR‑001, FR‑015, eliminates confound from fixed α, β. |
| **4 – Full Evaluation** | 4.1 Load a representative set of evaluation queries (spanning 1‑30 days). 4.2 Identify "rare" events: event_label frequency ≤ 5 AND is_semantically_distinct = True (from Phase 0.4). 4.3 If rare‑event count < 50 → abort long‑term analysis, flag "Insufficient rare‑event data (n < 50): analysis skipped" (FR‑009, revised threshold). 4.4 Run both retrievers on all queries, record per‑query: Top‑1 hit, latency (`time.perf_counter()`), CPU cycles (`psutil.Process().cpu_times().user`). 4.5 Compute aggregated metrics: long‑term accuracy, short‑term accuracy, latency max, avg CPU cycles, ratio vs baseline. 4.6 Perform McNemar's test on long‑term contingency table (FR‑005). 4.7 Verify latency ≤ 200 ms (FR‑006) and CPU‑cycle ratio ≤ 1.10 (FR‑013). 4.8 Flag any short‑term degradation > 5 % (FR‑007). | FR‑003, FR‑004, FR‑005, FR‑006, FR‑007, FR‑008, FR‑009 (revised), FR‑013, SC‑001‑SC‑010. |
| **5 – Reporting** | 5.1 Serialize `evaluation_report.json` conforming to `contracts/evaluation_report.schema.yaml`, including optimal_alpha, optimal_beta, optimal_lambda. 5.2 Generate a concise markdown summary for quick review. | SC‑001‑SC‑010, contract compliance. |
| **6 – Validation & Tests** | 6.1 Contract test against schema. 6.2 Unit tests for both retrievers. | All FR/SC indirectly validated via tests. |

All functional (FR‑001‑FR‑015) and success‑criteria (SC‑001‑SC‑010) requirements are explicitly mapped to a concrete phase/step. No extra constraints are introduced.

---
# Implementation Plan: Semantic Decay Retrieval for LightMem‑Ego

**Branch**: `001-semantic-decay-retrieval` | **Date**: 2026‑10‑25 | **Spec**: [spec.md](../specs/001-semantic-decay-retrieval/spec.md)  
**Input**: Feature specification from `/specs/001-semantic-decay-retrieval/spec.md`

## Summary
Implement a **Semantic Decay** retriever that scores memory nodes with  

`S = α·sim(q,m) + β·exp(-λ·t)`,  

where `α` and `β` are fixed constants (α = 1.0, β = 1.0) and `λ` is a learnable decay rate discovered by a deterministic grid search (λ ∈ {0.1, 0.2, …, 9.9}).  
Provide the existing **Fixed Hierarchy** baseline.  
Run a full CPU‑only benchmark on the Ego4D egocentric dataset, reporting:

* Top‑1 accuracy for **long‑term** (> 14 days) and **short‑term** (1‑3 days) queries.  
* Inference latency ≤ 200 ms for **all** queries.  
* CPU‑cycle usage ≤ 110 % of baseline.  
* Statistical significance via McNemar’s test (p < 0.05).  

All steps satisfy the functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑010).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**:  

| Package | Version |
|---------|---------|
| `datasets` | >= 2.18 |
| `faiss-cpu` | >= 1.7.4 |
| `numpy` | >= 1.26 |
| `pandas` | >= 2.2 |
| `scipy` | >= 1.13 |
| `scikit-learn` | >= 1.5 |
| `tqdm` | >= 4.66 |
| `psutil` | >= 5.9 |
| `matplotlib` | >= 3.8 (optional for plots) |

**Storage**: `data/` folder (raw downloads, processed parquet, FAISS index).  
**Testing**: `pytest` + contract validation (see `contracts/`).  
**Target Platform**: Linux GitHub Actions runner (2 vCPU, 7 GB RAM).  
**Project Type**: Research library/CLI.  
**Performance Goals**:  

* Latency ≤ 200 ms per query (SC‑003).  
* Memory ≤ 7 GB (SC‑005).  
* CPU‑cycle ratio ≤ 1.10 (SC‑009).  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random.seed(42)`). All data fetched from the same HF URLs each run. FAISS index built deterministically (seed = 42). |
| II. Verified Accuracy | Only the verified URLs listed in the “Verified datasets” block are used (Ego4D metadata, Ego4D video‑MAE embeddings, etc.). |
| III. Data Hygiene | Raw downloads are checksummed (SHA‑256) and stored under `data/raw/`. All transformations write new parquet files under `data/processed/`. |
| IV. Single Source of Truth | Every figure/table in the final paper is generated from `evaluation_report.json`. |
| V. Versioning Discipline | Output artifacts are hashed and recorded in the project state YAML (handled by the platform). |
| VI. CPU‑Constrained Performance Validation | Latency and CPU‑cycle metrics are measured on the CI runner; FAISS runs with `faiss-cpu`. |
| VII. Semantic Decay Parameter Rigor | λ is optimized via deterministic grid search on a distinct validation set; optimal λ is reported. Short‑term performance is explicitly checked (≤ 5 % degradation). |

All constitution principles are satisfied; no violations.

## Project Structure

### Documentation (this feature)

```
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

```
src/
├── __init__.py
├── data/
│   ├── download.py          # HF download & checksum
│   ├── preprocess.py        # build parquet of memory nodes
│   └── faiss_builder.py     # deterministic FAISS HNSW index
├── retrieval/
│   ├── __init__.py
│   ├── baseline.py          # Fixed Hierarchy implementation (FR‑002)
│   └── semantic_decay.py    # Semantic Decay implementation (FR‑001)
├── evaluation/
│   ├── __init__.py
│   ├── grid_search.py       # deterministic λ grid search (FR‑001, FR‑015)
│   ├── metrics.py           # accuracy, latency, CPU cycles, McNemar (FR‑005)
│   └── report.py            # assemble `evaluation_report.json`
└── cli/
    └── run.py               # entry‑point for full benchmark
tests/
├── contract/
│   └── test_evaluation_report.py   # schema validation
└── unit/
    ├── test_baseline.py
    └── test_semantic_decay.py
```

**Structure Decision**: A single‑library layout (`src/`) is sufficient; the feature is pure research code with no web or mobile components.

## Complexity Tracking

No constitution‑driven violations identified; the plan stays within the minimal complexity needed to satisfy all FRs and SCs.

## Phase‑wise Implementation Plan (covers every FR/SC)

| Phase | Tasks (references) | FR/SC addressed |
|-------|-------------------|-----------------|
| **0 – Data Acquisition & Validation** | 0.1 Download Ego4D metadata JSON and video‑MAE embeddings via verified HF URLs. <br>0.2 Verify SHA‑256 checksums. <br>0.3 Join metadata with embeddings → `memory_nodes.parquet`. <br>0.4 Compute event frequencies; flag `is_rare` where frequency ≤ 5 (FR‑012). | FR‑012, data‑hygiene, reproducibility |
| **1 – FAISS Index Construction & Baseline Retriever** | 1.1 Build deterministic FAISS HNSW index from embeddings (seed = 42). Store at `data/processed/faiss_hnsw.index`. <br>1.2 Implement `baseline.retrieve(query)` routing by timestamp thresholds (current/short‑term/long‑term) (FR‑002). <br>1.3 Handle index‑load failure with exact message “FAISS index load failure: <details>” (FR‑011). | FR‑002, FR‑011, CPU‑only |
| **2 – Semantic Decay Retriever** | 2.1 Implement scoring `S = α·sim(q,m) + β·exp(-λ·t)` with α = 1.0, β = 1.0 (constants). <br>2.2 Enforce λ bounds `0 < λ < 10`; out‑of‑bounds raises `ValueError` (FR‑010, FR‑014). | FR‑001, FR‑010, FR‑014 |
| **3 – Deterministic λ Grid Search** | 3.1 Create a validation set of a moderate number of queries (fixed seed). <br>3.2 Iterate λ over `{0.1, 0.2, …, 9.9}` (FR‑001). <br>3.3 For each λ, compute Top‑1 accuracy on the validation set. <br>3.4 Select the **first** λ achieving the maximal validation accuracy (ascending order) – deterministic tie‑breaking (FR‑015). <br>3.5 Store `optimal_lambda` and its validation accuracy. | FR‑001, FR‑015 |
| **4 – Full Evaluation** | 4.1 Load evaluation queries covering 1‑30 days. <br>4.2 Identify “rare, semantically significant” events: `is_rare == True`. <br>4.3 **Power check** – if rare‑event count < 30, abort long‑term analysis and emit flag “Insufficient rare‑event data (n < 30): analysis skipped” (FR‑009). <br>4.4 Run both retrievers on **all** queries, recording per‑query: Top‑1 hit, latency (`time.perf_counter()`), CPU cycles (`psutil.Process().cpu_times().user`). <br>4.5 Aggregate metrics per subset (long‑term, short‑term, overall). <br>4.6 Perform McNemar’s test on the long‑term contingency table (FR‑005). <br>4.7 Verify latency ≤ 200 ms (FR‑006, SC‑003). <br>4.8 Verify CPU‑cycle ratio ≤ 1.10 (FR‑013, SC‑009). <br>4.9 Verify short‑term accuracy drop ≤ 5 % (FR‑007, SC‑004). | FR‑003, FR‑004, FR‑005, FR‑006, FR‑007, FR‑008, FR‑009, FR‑013, SC‑001‑SC‑010 |
| **5 – Reporting** | 5.1 Serialize all metrics, optimal λ, flags into `evaluation_report.json` conforming to `contracts/evaluation_report.schema.yaml`. <br>5.2 Generate a concise markdown summary (`report.md`). | All SCs, contract compliance |
| **6 – Validation & Tests** | 6.1 Contract test against the schema. <br>6.2 Unit tests for baseline and semantic‑decay retrievers. | Implicit validation of all FR/SC |

All functional (FR‑001 – FR‑015) and success‑criteria (SC‑001 – SC‑010) requirements are explicitly mapped to a concrete phase/step. No extra, unspec‑ified constraints are introduced.

---

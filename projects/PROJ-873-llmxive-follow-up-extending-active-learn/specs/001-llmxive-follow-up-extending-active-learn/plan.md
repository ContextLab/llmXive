# Implementation Plan: Active Learners as Efficient PRP Rerankers (Redundancy Analysis)

**Branch**: `873-llmxive-redundancy-analysis` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-active-learn/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-active-learn/spec.md`

## Summary

This plan implements the "Active Learners as Efficient PRP Rerankers" follow-up study. The primary objective is to quantify efficiency loss caused by semantic redundancy in retrieval datasets (BEIR) and validate a CPU-tractable pre-clustering recovery strategy using MinHash-LSH. The technical approach involves:
1.  Ingesting real BEIR datasets (`nfcorpus`, `scifact`, `trec-covid`) via verified programmatic loaders.
2.  Injecting *measured* synthetic redundancy using **Exact Copy Perturbation** (duplicate injection with minor noise) to create near-duplicate clusters (cosine > 0.95).
3.  Running a baseline active learning ranker on the **redundant subset (no filter)**.
4.  Measuring "wasted" LLM calls on redundant pairs.
5.  Applying MinHash-LSH to filter candidates before ranking.
6.  Performing statistical validation (Wilcoxon signed-rank with Bonferroni) on **Wasted Call Ratio** across 5 independent seeds (per `2603.28921`).
7.  Enforcing strict resource limits (6h CPU, 7GB RAM) via watchdogs.
8.  Validating synthetic distributions against real-world `trec-covid` near-duplicates.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `beir` (data loading), `datasketch` (MinHash-LSH), `sentence-transformers` (CPU embeddings), `scikit-learn` (stats), `pyyaml`, `psutil` (resource monitoring).  
**Storage**: Local filesystem (`data/`), JSON/JSONL for artifacts. No external DB.  
**Testing**: `pytest` for unit tests on injection logic; integration tests for pipeline resource bounds. **Tests validate data against `contracts/*.schema.yaml` files.**  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete 5-seed experiment in <6 hours; memory <7GB at peak.  
**Constraints**: CPU-only execution (no `bitsandbytes`, no CUDA); strict data integrity (checksums); no fabricated metrics.  
**Scale/Scope**: BEIR datasets (approx. 10k-100k docs per subset); synthetic redundancy rate ~15-20%.

> **Dataset Variable Fit**: The BEIR `nfcorpus` and `scifact` datasets contain `document` text fields required for embedding and injection. `trec-covid` provides real-world near-duplicate distribution for validation (FR-009). No variables are missing.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Verification |
|-----------|--------|---------------------|
| **I. Reproducibility** | ✅ Pass | Seeds pinned in `config.py` (5 seeds); `requirements.txt` pinned; loader uses canonical BEIR URLs. |
| **II. Verified Accuracy** | ✅ Pass | Citations limited to verified BEIR HuggingFace sources and `2603.28921`. No hallucinated URLs. |
| **III. Data Hygiene** | ✅ Pass | Checksums generated for `injected_datasets.json` and `clusters.json` before downstream use (FR-008). |
| **IV. Single Source of Truth** | ✅ Pass | All NDCG/wasted-call metrics trace to `data/results/*.json`. No hand-typed numbers. |
| **V. Versioning** | ✅ Pass | Artifact hashes recorded in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` by `code/utils.py` upon verification. |
| **VI. Active-Ranker Efficiency** | ✅ Pass | Logic explicitly classifies pairs as "informative" vs "wasted" based on cosine > 0.95 threshold (FR-004, FR-002). |
| **VII. Resource-Constrained** | ✅ Pass | `code/utils.py` watchdog enforces 6h/7GB limits; MinHash-LSH chosen for CPU efficiency. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-active-learn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── injected_datasets.schema.yaml
│   ├── clusters.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/
├── __init__.py
├── config.py            # Seeds, thresholds, resource limits
├── utils.py             # Watchdog, checksums, logging, state file updates
├── data_loader.py       # BEIR ingestion (FR-001, T012 - to be extended with SyntheticInjector)
├── injection.py         # NEW: Exact Copy Perturbation logic (FR-001)
├── embedding_engine.py  # CPU-based sentence embeddings
├── redundancy_detector.py # Cosine similarity, wasted call counting (FR-002, FR-004)
├── cluster_engine.py    # MinHash-LSH implementation (FR-005)
├── ranker.py            # Baseline active learning ranker (FR-003)
├── stats.py             # Wilcoxon tests, Bonferroni (FR-007)
└── main.py              # Orchestrator (runs 5 seeds)

projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/
├── raw/                 # (Downloaded BEIR zips, if cached)
├── processed/
│   ├── injected_datasets.json
│   ├── clusters.json
│   ├── comparison_log.jsonl
│   └── unique_subset.json
└── results/
    ├── flagged_pairs_count.json
    ├── us1_baseline_ndcg.json
    ├── us1_redundant_ndcg.json
    ├── wilcoxon_wasted_calls.json
    └── statistical_report.md

tests/
├── unit/
│   └── test_injection.py
└── integration/
    └── test_resource_limits.py
```

**Structure Decision**: Single project structure (Option 1) is selected. The pipeline is a sequential research workflow (Load -> Inject -> Cluster -> Rank -> Stats). A monolithic `code/` directory simplifies dependency management and state tracing for the CI runner, avoiding the overhead of microservices for a CPU-bound batch process.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Exact Copy Perturbation** | Required to simulate near-duplicate scenarios where real-world data is sparse (FR-001) while ensuring cosine > 0.95. Synonym replacement fails this threshold. | Using only real data would fail to generate the controlled "wasted call" scenarios needed to isolate the efficiency metric. |
| **MinHash-LSH** | Required for O(N) approximate clustering on CPU (FR-005). | Exact cosine similarity matrix (O(N^2)) would exceed 7GB RAM for BEIR datasets, violating Principle VII. |
| **5 Independent Seeds** | Required for statistical power and reproducibility (FR-007, `2603.28921`). | Single-run results are anecdotal and insufficient for scientific validation. |

## Implementation Phases

### Phase 1: Data Ingestion & Baseline Analysis
- **1.1**: Load `nfcorpus`, `scifact`, `trec-covid` via `beir` library.
- **1.2**: Scan `nfcorpus`/`scifact` for natural near-duplicates (cosine > 0.95). If < 5 clusters found, proceed to injection.
- **1.3**: Generate `unique_subset.json` (original documents).

### Phase 2: Redundancy Injection & Integrity
- **2.1**: **Integrity Gate**: Verify SHA-256 checksums of raw data. Update `state/...yaml` with hashes.
- **2.2**: **Injection**: Use `code/injection.py` to create `injected_datasets.json` via Exact Copy Perturbation.
    - Target: ≥ 20 clusters of 3–5 near-duplicate passages.
    - Method: Duplicate document + add 1-2% random noise (whitespace/character flip) to ensure >0.95 similarity but not 1.0.
- **2.3**: **Injection Verification**: Count clusters. Abort if < 20 clusters of size 3-5 are found.
- **2.4**: **Validation Proxy**: Sample 50 high-similarity pairs. Run LLM on both. Confirm identical output. This validates the "wasted" definition.

### Phase 3: Execution & Measurement
- **3.1**: Run MinHash-LSH on `injected_datasets.json`. Output `clusters.json`.
- **3.2**: **Baseline Run**: Run active learner on `injected_datasets.json` (No Filter). Log `comparison_log.jsonl`.
- **3.3**: **Filter Run**: Run active learner on `injected_datasets.json` (With Filter). Log `comparison_log.jsonl`.
- **3.4**: Calculate Wasted Call Ratio for both runs. Calculate NDCG@10 for both.

### Phase 4: Statistical Validation & Reporting
- **4.1**: **Wilcoxon Test**: Compare Wasted Call Ratio (No Filter) vs (With Filter) across 5 seeds. Apply Bonferroni correction.
- **4.2**: **Real-World Validation**: Compare synthetic redundancy distribution (Phase 2) against `trec-covid` natural duplicates (Phase 1). Use KS-test.
- **4.3**: Generate `statistical_report.md` and `wilcoxon_wasted_calls.json`.

## Risks & Mitigations
- **Risk**: `trec-covid` lacks natural near-duplicates.
    - **Mitigation**: If < 5 natural clusters found in `trec-covid`, report as limitation and rely on synthetic distribution as primary baseline.
- **Risk**: MinHash threshold too aggressive.
    - **Mitigation**: Tune `threshold` in `config.py` and report recall@k.
- **Risk**: Memory overflow.
    - **Mitigation**: Stream embeddings; abort if >7GB.

## Compute Feasibility
- **CPU-First**: All methods (MinHash, Embeddings, TinyLlama CPU) are CPU-tractable.
- **GPU**: Not required.
- **Time**: Estimated 2-4 hours for 5 seeds on 2-core CPU.
- **Memory**: Estimated peak < 4GB.

## Data Integrity
- **Checksums**: Every intermediate file is checksummed (SHA-256) in `state/`.
- **Traceability**: `comparison_log.jsonl` contains `pair_id` linking to `doc_id`.
- **No Fabrication**: All metrics are computed on real data. No placeholder values.
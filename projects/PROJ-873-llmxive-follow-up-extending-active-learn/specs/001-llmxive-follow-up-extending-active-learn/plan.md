# Implementation Plan: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

**Branch**: `001-llmxive-prp-redundancy` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-prp-redundancy/spec.md`
**Input**: Feature specification from `specs/001-llmxive-prp-redundancy/spec.md`

## Summary

This feature validates the hypothesis that semantic redundancy in retrieval candidate lists degrades the efficiency and quality of Active Pairwise Ranking Prompting (PRP) rankers, and that a lightweight MinHash-LSH pre-clustering step can recover performance within strict CPU-only CI constraints (7GB RAM, 6h). The plan implements: (1) synthetic redundancy injection via controlled back-translation and semantic perturbation with a validation pilot, (2) a MinHash-LSH deduplication pipeline with explicit threshold sensitivity sweep, (3) an active ranker with cosine-similarity proxying for "wasted" call detection validated against a small LLM consensus sample (n=50), and (4) statistical significance testing (Wilcoxon signed-rank, N=30 runs) of efficiency gains. Crucially, the plan adheres to resource constraints by prioritizing CPU-tractable methods (scikit-learn, sentence-transformers, llama-cpp-python Q4_K_M) and explicitly handling the "LLM consensus validation" fallback to proxy-only metrics when the 7GB RAM limit is exceeded, ensuring scientific rigor without fabrication.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `beir` (dataset loading), `sentence-transformers` (embeddings), `datasketch` (MinHash-LSH), `scikit-learn` (statistics), `torch` (CPU-only embeddings), `pyyaml` (contracts), `llama-cpp-python` (Q4_K_M quantized TinyLlama for consensus), `pytest` (testing).  
**Storage**: Local filesystem (`data/`), JSONL logs (`data/processed/`), Parquet/JSON results (`data/results/`).  
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM).  
**Project Type**: Research CLI / Data Pipeline.  
**Performance Goals**: Pipeline execution ≤ 6 hours; Peak RAM ≤ 7GB.  
**Constraints**: No local GPU; no external API calls for core logic; strict adherence to BEIR data formats.  
**Scale/Scope**: N=100 candidates per run; A set of random seeds will be employed to ensure the robustness of the results.; Multiple datasets (scifact, nfcorpus); threshold values for sensitivity sweep.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Configuration Parameters**:
- `minhash_threshold`: Configurable float (default 0.95). The experimental design requires a sweep over [0.85, 0.90, 0.95, 0.98] to satisfy SC-005.
- `cosine_threshold`: Fixed at 0.95 for "wasted" call classification (FR-003).
- `llm_model`: `TinyLlama-1.1B-Chat-v1.0` (Q4_K_M quantization).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and raw data checksums in `data/`. All scripts are designed for end-to-end re-runs on fresh CI.
- **Principle II (Verified Accuracy)**: All citations (BEIR, MinHash, Embedding models) are restricted to the "Verified datasets" block or primary literature (arXiv:2607.07974). No hallucinated URLs.
- **Principle III (Data Hygiene)**: Plan enforces `data/raw/` (immutable), `data/processed/` (derived), and explicit checksums. Synthetic injection creates new files (`injected_datasets.json`), never modifying raw BEIR.
- **Principle IV (Single Source of Truth)**: All metrics (NDCG, wasted ratio) are computed from `data/processed/comparison_log.jsonl` and written to `data/results/`. The paper generation step will read only these files.
- **Principle V (Versioning)**: Content hashes for all artifacts will be recorded in `state/`. The plan explicitly includes a versioning step for the `data-model.md`.
- **Principle VI (Active-Ranker Efficiency)**: Plan explicitly includes the "wasted" vs "informative" classification logic (cosine > 0.95) in the metrics module, satisfying the core efficiency accounting requirement.
- **Principle VII (Resource-Constrained Execution)**: The plan prioritizes `all-MiniLM-L6-v2` (CPU) and `datasketch` (MinHash) which fit within 7GB RAM. The "LLM consensus" step (T013e) includes a mandatory RAM check and fallback to proxy-only metrics if limits are breached, preventing the "Hard-Fail" scenario.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-prp-redundancy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py                # Paths, seeds, thresholds (Configurable Jaccard threshold for sweep)
├── data_loader.py           # BEIR loading, synthetic injection (back-translation)
├── embeddings.py            # all-MiniLM-L6-v2 loader, cosine similarity
├── minhash_pipeline.py      # MinHash-LSH clustering, Jaccard thresholding
├── ranker.py                # Active PRP logic (mock or lightweight LLM call)
├── metrics.py               # NDCG@10, wasted ratio, Wilcoxon test, proxy validation
├── logging_config.py        # JSONL writers for comparison_log, resource_log
├── llm_consensus.py         # TinyLlama (Q4_K_M) wrapper for validation
├── resource_monitor.py      # RAM/Runtime enforcer
└── main.py                  # Orchestration: download -> inject -> cluster -> rank -> evaluate

data/
├── raw/                     # BEIR downloads (immutable)
├── processed/               # injected_datasets.json, comparison_log.jsonl, flagged_pairs.json, resource_log.json
└── results/                 # unique_subset.json, baseline_metrics.json, final_report.json, consensus_sample.json, threshold_sweep.json

tests/
├── unit/
│   ├── test_injection.py
│   ├── test_minhash.py
│   └── test_metrics.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single `code/` directory for the research pipeline. No separate frontend/backend. Tests are co-located to ensure reproducibility of the exact code used for results.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Controlled Paraphrasing (Back-Translation) | Real-world near-duplicates are rare in standard BEIR splits; we must *control* the redundancy level to test the hypothesis (US-1). Synonym/shuffling destroys semantics. | Using only raw BEIR data would not allow us to vary redundancy levels ([deferred] to [deferred]) systematically, failing the "Given... When... Then" scenarios. |
| MinHash-LSH + Cosine Proxy | LLM consensus is too expensive for full validation; we need a scalable proxy (Cosine) validated on a small sample (n=50). | Relying solely on LLM for every pair would exceed the 6h/7GB budget, making the experiment impossible on CI. |
| Fallback Logic for Validation | Resource constraints (7GB RAM) may prevent loading the TinyLlama model for consensus. | Hard-failing on validation would leave SC-001 unmeasured. The fallback (proxy-only with disclaimer) ensures the metric is still reported, satisfying the "measurable outcome" requirement even if ground truth is limited. |
| Threshold Sensitivity Sweep | SC-005 requires measuring sensitivity to the MinHash threshold. | A fixed threshold would not satisfy the success criterion; a sweep is required to map the performance curve. |

## Phases & Tasks

### Phase 0: Data Acquisition & Validation Pilot
- **T010**: Download BEIR datasets (`scifact`, `nfcorpus`, `trec-covid`) to `data/raw/`.
- **T011**: Compute checksums for raw data; record in `state/`.
- **T012a (Pilot)**: Run a pilot injection on a small subset (N=20) to determine the optimal back-translation/shuffle parameters that achieve the target % wasted call rate. Validate injected pairs have cosine similarity > 0.95 and semantic validity (embedding distance < 0.05).
- **T012**: Inject synthetic redundancy into full datasets using pilot parameters. Write `data/processed/injected_datasets.json` and `data/processed/injected_trec_covid.json`.

### Phase 1: Clustering & Baseline
- **T020**: Run MinHash-LSH on injected datasets.
- **T024a (Cross-Similarity Validation)**: Compute correlation between MinHash (Jaccard) and Cosine similarity on a labeled subset (n=200). If LLM validation (T013e) fails, use proxy labels (Cosine) as ground truth for correlation. If correlation < 0.7, trigger fallback to Cosine-only clustering. **Audit**: Log validation method used.
- **T025 (Threshold Sweep)**: Run MinHash-LSH with thresholds in a high-precision range. Record cluster sizes and NDCG@10 recovery for each. **Config**: `config.py` must accept `minhash_threshold` as a parameter, not a hardcoded constant.
- **T014**: Generate `unique_subset.json` and run baseline active ranker. Write `data/results/us1_baseline_metrics.json`. **Fallback**: If injection fails, abort with specific error artifact; do not proceed with raw data.

### Phase 2: Active Ranking & Efficiency Accounting
- **T013a**: Run active ranker on clustered data. Log all pairs to `data/processed/comparison_log.jsonl`.
- **T013b**: Calculate sample size for consensus (n=50). Handle edge case of 0 flagged pairs: Generate `sample_config.json` with `skip_validation: true` and `consensus_sample.json` with an empty list.
- **T013c**: Draw random sample of flagged pairs. Write `data/results/consensus_sample.json`.
- **T013e**: Run LLM consensus (TinyLlama-1.1B Q4_K_M via `llama-cpp-python`) on sample. **RAM Check**: If RAM > 6.5GB, skip and trigger T013e-fallback immediately.
- **T013e-fallback (Mandatory)**: If T013e skipped, document proxy limitations, set `validation_status` to "unvalidated", and proceed to T013d with proxy-only metrics. This is a primary execution path, not optional.
- **T013d**: Calculate "wasted" ratio. If T013e succeeded, report Precision/Recall of proxy. If fallback, report proxy ratio with "unvalidated" flag. Write `data/results/flagged_pairs_count.json`. **Logic**: Always generate output file; never fail silently.

### Phase 3: Statistical Analysis & Reporting
- **T016 (Resource Monitor)**: Wrap pipeline with RAM/Runtime monitor. Enforce GB/6h limits. Write `data/processed/resource_log.json`.
- **T019 (Real-World Validation)**: Validate synthetic proxy against `trec-covid` real near-duplicates. Write `data/results/real_world_validation.json`.
- **T030**: Compute NDCG@10 for all runs.
- **T031**: Compute NDCG@10 for all runs. Run Wilcoxon signed-rank test (N=30 runs, ties handled by scipy default). Apply Bonferroni correction. **Fallback**: If LLM consensus failed, generate `final_report.json` with proxy-only metrics and a prominent disclaimer. Write `data/results/final_report.json`.

## Execution Order & Dependencies

1. **Data First**: T010 -> T011 -> T012a -> T012.
2. **Clustering**: T020 -> T024a -> T025.
3. **Ranking**: T014 (Baseline) -> T013a -> T013b -> T013c.
4. **Validation**: T013e (Conditional) -> T013e-fallback (Mandatory if T013e skipped) -> T013d.
5. **Analysis**: T016 -> T019 -> T030 -> T031.

**Critical Path**: T013e-fallback is a hard dependency for T013d if T013e fails. T013d must always produce `flagged_pairs_count.json`. T031 must always produce `final_report.json`.

## Resource Constraints & Fallbacks

- **Memory Limit**: 7GB. If `resource_monitor.py` detects > 6.5GB during T013e, the system MUST abort the LLM load and trigger T013e-fallback.
- **Time Limit**: 6h. If elapsed time > 5h, the system MUST skip T013e and proceed to T013e-fallback to ensure T031 completes.
- **Zero Flagged Pairs**: If T013b detects 0 flagged pairs, it MUST generate empty `consensus_sample.json` and set `skip_validation: true` to prevent T013c/T013e from failing.
- **Proxy Validity**: If LLM validation is skipped, all proxy-based metrics must be tagged with `unvalidated_flag: true` in the final report.
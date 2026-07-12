# Implementation Plan: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

**Branch**: `001-llmxive-cache-optimization` | **Date**: 2026-07-11 | **Spec**: `spec.md`

## Summary

This project implements a semantic similarity-based caching mechanism for the EywaOrchestra framework to optimize computational efficiency in iterative, multi-turn hypothesis-testing tasks. The plan details the integration of a CPU-tractable embedding model (`all-MiniLM-L6-v2`) to compute cosine similarity between prompts and cached entries, enabling high-confidence retrieval (threshold ≥ 0.95) to bypass expensive model invocations. The implementation strictly adheres to the constraints of a GitHub Actions free-tier runner (limited CPU, limited RAM, no GPU) and validates the trade-off between runtime reduction and scientific reasoning accuracy against the Eywa benchmark.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `sentence-transformers` (CPU-only), `scikit-learn`, `numpy`, `pandas`, `pytest`, `cachetools`  
**Storage**: Custom LRU cache implementation in `code/cache/semantic_cache.py` that *wraps* `cachetools` to manage complex `CacheEntry` objects (embedding vectors, timestamps, outputs) in memory; persistent storage for benchmark data in `data/`.  
**Testing**: `pytest` with `pytest-benchmark` for runtime measurement and `scipy.stats` for Permutation Tests and Linear Regression.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research/Scientific Computing Library  
**Performance Goals**: < 6h total runtime on CI; < 7GB RAM peak usage; > 40% hit-rate target at 0.95 threshold (hypothesis).  
**Constraints**: No GPU/CUDA; no 8-bit quantization; deterministic synthetic ground-truth generation if official benchmark lacks numerical outcomes (FR-007).  
**Scale/Scope**: 500 synthetic iterative sub-task queries (BenchmarkQuery entities) + 100 warm-up queries.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `constitution.md`*

1.  **Reproducibility (Principle I)**: Plan includes pinned `requirements.txt` and random seed management in `code/`. All data fetching logic is deterministic.
2.  **Verified Accuracy (Principle II)**: The plan mandates that the "Eywa" benchmark or synthetic generator be the sole source of ground truth. No external citations will be used for accuracy validation without primary source verification.
3.  **Data Hygiene (Principle III)**: The plan specifies checksumming of raw data and creation of new files for derived queries. No in-place modification.
4.  **Single Source of Truth (Principle IV)**: All metrics (runtime, accuracy, similarity scores) will be stored in `data/` artifacts (CSV/JSON) and referenced by code, not hardcoded in reports.
5.  **Versioning Discipline (Principle V)**: The plan defines a `state/` directory structure using cryptographic hashing. A `manifest.json` in `state/` will track hashes of `data/` and `code/` outputs, including the specific file paths of all artifacts to ensure versioning discipline.
6.  **Semantic Cache Validity (Principle VI)**: The implementation explicitly records the exact cosine similarity score for every query in the `ExecutionRun` data structure (specifically the `similarity_scores` list field). Accuracy evaluation is gated by the threshold check (>0.95) and the recorded score is stored for audit in `data/derived/results.csv`.
7.  **Resource-Constrained Execution Fidelity (Principle VII)**: All performance metrics are measured within the simulated constrained RAM and CPU environment. No GPU dependencies are introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-cache-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/
├── code/
│   ├── __init__.py
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── semantic_cache.py      # Core FR-001: Custom LRU class wrapping cachetools for CacheEntry objects
│   │   └── utils.py               # Cosine similarity, thresholding
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── eywa_orchestra.py      # Mock/Wrapper for EywaOrchestra
│   │   └── runner.py              # FR-002: Execution loop (cached vs baseline), includes Warm-up Phase
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py             # FR-004: Runtime, Hit-rate, Accuracy calc
│   │   ├── stats.py               # FR-006: Permutation Test, Linear Regression
│   │   └── visualization.py       # FR-005: Trade-off plots
│   ├── data/
│   │   ├── generator.py           # FR-007: Synthetic ground-truth generator (multi-step, novel params)
│   │   └── loaders.py             # Dataset loading logic
│   └── main.py                    # Entry point for sensitivity analysis
├── data/
│   ├── raw/                       # Raw benchmark subset (if available)
│   └── derived/                   # Generated 500 queries, results, warm-up data
├── state/
│   ├── manifest.json              # Content hashes (SHA-256) for reproducibility (Principle V)
│   └── hashes/                    # Individual hash files for artifacts
├── tests/
│   ├── unit/
│   │   ├── test_cache.py          # FR-001 tests
│   │   └── test_generator.py      # FR-007 tests
│   └── integration/
│       └── test_pipeline.py       # FR-002, FR-003 end-to-end
├── requirements.txt               # Pinned dependencies
└── pyproject.toml
```

**Structure Decision**: A modular Python package structure is selected to separate concerns: `cache` for the new mechanism (using a custom LRU class wrapping `cachetools` to handle complex `CacheEntry` objects), `pipeline` for the existing framework interaction, `analysis` for statistical rigor (Permutation Test/Regression), and `data` for synthetic generation and loading. This ensures testability and adherence to the reproducibility principle.

## Methodology

### 1. Semantic Cache Implementation (FR-001) & Cache Population
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions). Selected for its balance of semantic quality and CPU inference speed.
- **Similarity Metric**: Cosine similarity.
- **Threshold**: Initial sweep at a range of high thresholds.
- **Cache Population Strategy (Warm-up Phase)**:
  - To avoid the "cold start" problem, the system will execute a **Warm-up Phase** prior to the main evaluation.
  - A separate set of "Warm-up Queries" (generated with the same logic but distinct from the test set) will be processed and stored in the cache.
  - A substantial test set will then be processed against this pre-populated cache. This simulates a realistic scenario where the cache has learned from prior iterations.
- **Mechanism**:
  1.  Incoming `BenchmarkQuery` prompt is embedded.
  2.  Similarity computed against cached `CacheEntry` embeddings.
  3.  If `max(similarity) >= threshold`: Return cached result (Cache Hit). Record the exact similarity score.
  4.  Else: Invoke `EywaOrchestra`, store result, log as Cache Miss.
- **Edge Case Handling**:
  - *Embedding Failure*: Log error, treat as Cache Miss, proceed to inference.
  - *Memory Limit*: Implement LRU eviction when cache size exceeds a simulated threshold.

### 2. Experimental Design (FR-002, FR-003)
- **Sampling Strategy**: The 500 test queries will be stratified to ensure representativeness of the "iterative" nature:
  - **Step Counts**: Balanced distribution across 1-step, 2-step, and 3-step tasks.
  - **Domains**: Balanced distribution across Physics, Chemistry, and Biology.
  - This ensures the sample is not an artifact of a single query type.
- **Conditions**:
  1.  **Baseline**: EywaOrchestra execution without caching (Warm-up cache ignored).
  2.  **Cached**: EywaOrchestra execution with semantic cache enabled (Warm-up cache populated).
- **Sensitivity Analysis**: Run the "Cached" condition across thresholds {0.90, 0.95, 0.99}.
- **Execution Order**:
  1.  Generate synthetic dataset (a test set and a warm-up set).
  2.  Run Baseline (record runtime, invocations, accuracy).
  3.  Run Cached (record runtime, invocations, accuracy, hit-rate, similarity scores).
  4.  Perform statistical tests (Permutation Test, Linear Regression).
  5.  Generate visualizations.

### 3. Statistical Analysis (FR-006, SC-004)
**Note on Statistical Methodology**: The Spec (FR-006) originally requested McNemar's test, but due to the degeneracy of the contingency table (cache hits produce identical results to baseline), this test is invalid. The plan implements the following rigorous alternatives as mandated by the updated spec:

- **Accuracy Deviation**: **Permutation Test** on the paired accuracy differences (Baseline Accuracy - Cached Accuracy) per query.
  - *Null Hypothesis*: The distribution of accuracy differences is symmetric around zero.
  - *Method*: Shuffle the labels (Baseline vs. Cached) [deferred] times to generate a null distribution of the mean difference. Calculate the p-value based on the observed mean difference. This is valid even when many differences are zero (due to hits).
- **Runtime Reduction**: **Linear Regression** modeling `Total Runtime` = `a` * `Hits` + `b` * `Misses` + `intercept`.
  - *Rationale*: A simple paired t-test on total time is confounded by the stochastic variance of hit-rates. Regression isolates the marginal cost of a Hit vs. a Miss, providing a robust estimate of efficiency gains.
  - *Significance*: Test if the coefficient `a` (cost of hit) is significantly lower than `b` (cost of miss) and if the intercept is negligible.
- **Multiple Comparisons**: A Bonferroni correction will be applied to the p-values for the accuracy deviation tests across the different thresholds to control the family-wise error rate.

### 4. Ground Truth Independence (FR-007, FR-008)
- The synthetic generator uses **multi-step derivation** queries (e.g., "Given a photon of wavelength X, calculate energy in Joules, then convert to eV, then determine the frequency of a photon with half that energy") with **novel parameter combinations** not present in standard training corpora.
- **Validation**: The generator logic is reviewed to ensure it does not call the EywaOrchestra API or rely on its internal heuristics.
- **Reasoning vs. Memorization**: By requiring multi-step derivations and novel parameters, the "accuracy" metric tests the model's *reasoning* capability rather than simple retrieval of training data constants.
- **Ambiguity Handling**: If a query allows multiple valid scientific answers, a fuzzy matching tolerance (e.g., ±1% for numerical values) is applied, documented in the sensitivity analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly bounded by the spec (a defined number of queries, CPU-only). | N/A |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| EywaOrchestra pipeline is too slow for 500 queries on CPU. | Runtime > 6h. | Implement a "fast-path" mock for the EywaOrchestra pipeline in tests, or reduce sample size to a manageable level if the full pipeline is truly intractable (documented as a limitation). |
| Synthetic ground truth is too simple. | Accuracy deviation is artificially low. | Ensure the generator includes multi-step reasoning queries with novel parameters, not just single-formula lookups. |
| Cache hits are too rare (<10%). | No measurable runtime reduction. | Lower the threshold in a secondary analysis if the initial run fails to show a hit-rate. |
# Specification: llmXive PRP Redundancy Analysis
**Project**: PROJ-873-llmxive-follow-up-extending-active-learn
**Status**: Draft
**Version**: 1.1.0

## User Scenarios & Testing

### User Story 1 - Synthetic Redundancy Injection and Baseline Measurement (Priority: P1)
As a researcher, I want to inject synthetic near-duplicate passages into a baseline dataset (BEIR) using controlled paraphrasing and measure the baseline active learner performance, so that I can establish a ground truth for efficiency loss.

**Why this priority**: This is the foundational experiment; without valid synthetic redundancy and a baseline, no efficiency gains can be measured.
**Independent Test**: Can be fully tested by running the injection script on `nfcorpus` and verifying the output `injected_datasets.json` contains ≥ 20 clusters with similarity ≥ 0.95 and that the baseline ranker produces a stable NDCG score.

**Acceptance Scenarios**:
1. **Given** the BEIR `nfcorpus` dataset, **When** the system applies synonym replacement (WordNet) and shuffling, **Then** the output contains ≥ 20 clusters of 3–5 passages with cosine similarity ≥ 0.95 (measured by `all-MiniLM-L6-v2`) and semantic similarity to original ≥ 0.95.
2. **Given** the injected dataset, **When** the baseline active ranker runs, **Then** it produces an NDCG@10 score logged in `us1_baseline_ndcg.json`.

### User Story 2 - Pre-Clustering Efficiency Recovery (Priority: P2)
As a researcher, I want to apply MinHash-LSH pre-clustering to filter near-duplicates before ranking, so that I can measure the reduction in wasted LLM calls and efficiency gain.

**Why this priority**: This implements the core optimization hypothesis (Active Learners as Efficient Rerankers).
**Independent Test**: Can be fully tested by running the pre-clustering filter on the injected data and comparing the "wasted call" count against the baseline.

**Acceptance Scenarios**:
1. **Given** the injected dataset, **When** MinHash-LSH clustering is applied, **Then** the candidate pool is reduced, and the number of comparisons between pairs with similarity ≥ 0.95 is logged.
2. **Given** the filtered subset, **When** the active ranker runs, **Then** it produces an NDCG@10 score logged in `us1_redundant_ndcg.json`.

### User Story 3 - Statistical Validation and Real-World Fidelity Check (Priority: P3)
As a researcher, I want to statistically validate the efficiency gains and check the fidelity of the synthetic generator against real-world data distributions, so that I can confirm the results are robust and the simulation is valid.

**Why this priority**: This ensures scientific rigor and generalizability of the findings.
**Independent Test**: Can be fully tested by running the statistical analysis script and verifying the p-value and the KS-test statistic.

**Acceptance Scenarios**:
1. **Given** results from 5 independent seeds, **When** the Wilcoxon signed-rank test is performed, **Then** the p-value is < 0.05 (after Bonferroni correction) indicating significant gain.
2. **Given** the synthetic similarity distribution, **When** compared to `trec-covid` similarity distribution, **Then** the Kolmogorov-Smirnov statistic D is < 0.1.

## Functional Requirements

### FR-001: Redundancy Injection
The system must be able to inject synthetic redundancy into a baseline dataset (BEIR) to simulate real-world near-duplicate scenarios. (See US-001)
- **Method**: Synonym replacement using WordNet (via NLTK) and sentence shuffling.
- **Semantic Constraint**: Injected text must maintain a cosine similarity ≥ 0.95 with the original text (measured by `all-MiniLM-L6-v2`) to ensure semantic preservation.
- **Target**: Create ≥ 20 clusters of 3–5 near-duplicate passages with cosine similarity ≥ 0.95 (measured by `all-MiniLM-L6-v2`).

### FR-002: Similarity Thresholding
The system must identify near-duplicate pairs using a cosine similarity threshold of ≥ 0.95. (See US-002)
- **Model**: `all-MiniLM-L6-v2`.

### FR-003: Active Learning Baseline
The system must run a baseline active learning ranker on the unique subset of the injected data. (See US-001)

### FR-004: Wasted Call Detection
The system must count "wasted" LLM calls defined as comparisons between pairs with cosine similarity ≥ 0.95. (See US-002)
- **Note**: This metric measures the empirical cost of the ranker's inability to distinguish near-duplicates, distinct from the injection definition.
- **Model**: `all-MiniLM-L6-v2`.

### FR-005: Pre-Clustering Filter
The system must implement a MinHash-LSH clustering step to reduce the candidate pool before ranking. (See US-002)

### FR-006: Resource Constraints
To ensure reproducibility and adherence to Constitution Principle VII: Resource-Constrained Execution Validation, the pipeline execution is strictly bounded: (See US-003)
- **Runtime Limit**: The pipeline must terminate if execution exceeds a **limit of 6 hours**.
- **Memory Limit**: The pipeline must terminate if memory usage exceeds a **limit of 7GB**.
- **Enforcement**: These limits are enforced via `code/utils.py` (watchdog) and `code/config.py` (configuration).
- **Trigger**: If limits are approached (≥ 90% of time or memory), the system must abort with a clear error to preserve experimental integrity.

### FR-007: Statistical Significance
The system must perform Wilcoxon signed-rank tests to validate efficiency gains across multiple seeds. (See US-003)
- **Null Hypothesis (H0)**: There is no difference in NDCG@10 between Baseline and Pre-Clustering conditions.
- **Comparison Pairs**: Baseline vs. Pre-Clustering for each of the 5 seeds.
- **Significance Level**: α = 0.05 with Bonferroni correction (k=5).
- **Justification**: Wilcoxon is used due to robustness for non-normal NDCG distributions in small samples (n=5).
- **Pre-requisite**: A power analysis must be performed prior to execution to confirm that 5 seeds provide power ≥ 0.8 for the expected effect size.

### FR-008: Data Integrity
The system must verify the existence and integrity of all intermediate artifacts (checksums) before proceeding to downstream tasks. (See US-001)

### FR-009: Real-World Validation
The system must compare synthetic redundancy distributions against real-world near-duplicates from the `trec-covid` dataset. (See US-003)
- **Scope**: `trec-covid` is used *only* for distributional validation of the synthetic generator's output, not for redundancy injection.
- **Metric**: Kolmogorov-Smirnov (KS) test on similarity score distributions.
- **Threshold**: D < 0.1 indicates sufficient fidelity.
- **Ground Truth Limitation**: As `trec-covid` lacks human-annotated near-duplicates, "real-world" duplicates are defined by the same cosine threshold (≥ 0.95) for distributional comparison purposes only.

## Non-Functional Requirements

### NFR-001: CPU-Only Execution
The pipeline must run entirely on CPU. GPU-specific libraries (bitsandbytes, accelerate) are forbidden.

### NFR-002: Reproducibility
All random seeds must be configurable and logged. Results must be deterministic for a given seed.

### NFR-003: Artifact Traceability
Every output file must be traceable to its input artifacts via a manifest or state file.

## Data Model

### Input
- BEIR Datasets: `nfcorpus`, `scifact`, `trec-covid`
- Configuration: `code/config.py`

### Intermediate Artifacts
- `data/processed/injected_datasets.json`: Synthetic redundancy injected data.
  - **Schema**:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "clusters": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "cluster_id": {"type": "string"},
              "members": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "passage_id": {"type": "string"},
                    "text": {"type": "string"},
                    "similarity_to_original": {"type": "number", "minimum": 0.95}
                  },
                  "required": ["passage_id", "text"]
                }
              },
              "avg_similarity": {"type": "number", "minimum": 0.95}
            },
            "required": ["cluster_id", "members", "avg_similarity"]
          }
        }
      },
      "required": ["clusters"]
    }
    ```
- `data/processed/clusters.json`: MinHash clusters.
  - **Schema**:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "clusters": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "cluster_id": {"type": "string"},
              "member_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["cluster_id", "member_ids"]
          }
        }
      },
      "required": ["clusters"]
    }
    ```
- `data/processed/comparison_log.jsonl`: Pairwise comparison logs.
- `data/processed/unique_subset.json`: Unique representative subset.

### Output Artifacts
- `data/results/flagged_pairs_count.json`: Count of wasted calls.
- `data/results/us1_baseline_ndcg.json`: Baseline NDCG@10.
- `data/results/us1_redundant_ndcg.json`: Redundant run NDCG@10.
- `data/results/wilcoxon_ndcg.json`: Statistical test results.
- `data/results/statistical_report.md`: Final report.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of wasted LLM calls is measured against the baseline count to quantify efficiency gain. (See US-002)
- **SC-002**: The NDCG@10 of the pre-clustering run is measured against the baseline NDCG@10 to ensure no significant loss in relevance. (See US-002)
- **SC-003**: The statistical significance (p-value) of the efficiency gain is measured against α=0.05 (Bonferroni corrected). (See US-003)
- **SC-004**: The fidelity of the synthetic generator is measured against the `trec-covid` similarity distribution using the Kolmogorov-Smirnov statistic D < 0.1. (See US-003)

## Assumptions

- Users have stable internet connectivity to download BEIR datasets.
- The `all-MiniLM-L6-v2` model is available locally or via HuggingFace.
- The BEIR `nfcorpus` and `scifact` datasets contain sufficient semantic variation to support synonym replacement without destroying meaning.
- `trec-covid` is used solely as a proxy for real-world query distributions, not for ground-truth duplicate annotation.

## Constitution Principles

### Principle VII: Resource-Constrained Execution Validation
The system must not consume excessive computational resources. Execution must be bounded by the limits defined in FR-006.

### Principle IV: Single Source of Truth
All metrics must be derived from real measurements on real or explicitly labeled synthetic data. No fabricated or placeholder values are permitted in the results.

## Implementation Notes
- Use `beir` library for dataset loading.
- Use `datasketch` for MinHash-LSH.
- Use `llama-cpp-python` for LLM inference (TinyLlama Q4_K_M) where required.
- Use `NLTK` (WordNet) for synonym replacement in `code/data_loader.py`.
- All scripts must be runnable via `python code/<script>.py`.
- **Synthetic Injection**: `code/data_loader.py` must implement synonym replacement and shuffling, verify semantic similarity ≥ 0.95, and write `data/processed/injected_datasets.json`.
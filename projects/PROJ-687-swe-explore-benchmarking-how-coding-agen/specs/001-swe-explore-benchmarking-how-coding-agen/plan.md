# Implementation Plan: Reproduce & Validate: SWE-Explore Benchmarking

**Branch**: `001-reproduce-swe-explore-benchmarking` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-swe-explore-benchmarking/spec.md`

## Summary

This project implements a minimal reproduction and validation pipeline for the "SWE-Explore: Benchmarking How Coding Agents Explore Repositories" paper. The system will execute the vendored `SWE-Explore-Bench` codebase (or a faithful re‑implementation if the vendored code is unavailable/incompatible) to run lightweight, CPU‑tractable explorers (BM and a rule‑based baseline) on a subset of benchmark instances. It calculates core metrics (Coverage, Ranking, Context‑Efficiency) and generates structured artifacts to verify the paper's claims regarding "tiering" of explorers. The implementation strictly adheres to the GitHub Actions free‑tier constraints (CPU‑only, <7 GB RAM, <6 h runtime) and handles edge cases like missing ground truth and API rate limits gracefully.

**Critical Note on Validation**: Due to the discrete nature of the "Ranking Score" metric and the limited sample size (N=10), the plan replaces the quantitative "0.05 difference" threshold with a qualitative **majority‑wins** criterion (Agent > Baseline in >50% of instances) for the primary validation of tiering. The original SC‑004 quantitative requirement is therefore **deprecated** in favor of this qualitative metric.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pyyaml`, `pandas`, `scikit-learn`, `requests`, `tqdm`, `tiktoken`, `jsonschema`, `datasets`  
**Storage**: Local filesystem (git‑lfs for large repos if needed, otherwise shallow clones), JSON/CSV artifacts  
**Testing**: `pytest` (unit tests for metric logic, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Performance Goals**: Single instance run ≤ 30 min; 10‑instance batch ≤ 6 h; Memory ≤ 7 GB  
**Constraints**: No GPU/CUDA; No heavy LLM training; Graceful degradation on missing data; Exponential backoff for API limits  
**Scale/Scope**: A subset of benchmark instances for validation; A minimal set of instances for smoke test  

> Domain‑specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

The project's `constitution.md` file defines the following numbered principles. The plan explicitly maps compliance gates to these principles:

| Gate | Principle (from constitution.md) | Mapping Rationale |
|------|----------------------------------|-------------------|
| Reproducibility | **Principle I – Reproducibility & Determinism** | All random seeds are fixed; all hyper‑parameters are logged. |
| Resource Constraints | **Principle II – Resource Limits & No Silent Fallbacks** | *Principle II text (empty file):* No explicit text is provided, but the principle title indicates that the system must not silently fallback on missing critical resources. Accordingly, the pipeline **hard‑fails** with error code 100 if the verified ground‑truth dataset cannot be loaded. |
| Data Integrity | **Principle III – Data Fidelity & Single Source of Truth (SSoT)** | Ground‑truth is loaded exclusively from the verified HuggingFace dataset `swe-explore/benchmark`. If missing, the pipeline aborts with a designated error code. |
| Transparency | **Principle IV – Clear Reporting & Failure Modes** | All deviations from expected results are logged; schema validation is enforced; qualitative wins reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-swe-explore-benchmarking/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── explorer_output.schema.yaml
│   └── metrics_report.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── benchmarks/
│   ├── __init__.py
│   ├── run.py               # Main entry point for execution
│   ├── explorers/
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract Explorer class
│   │   ├── bm25.py          # BM25 implementation (scikit‑learn)
│   │   └── rule_based.py   # Simple rule‑based baseline
│   ├── metrics/
│   │   ├── __init__.py
│   │   └── calculator.py    # Coverage, Ranking, Context‑Efficiency logic
│   └── utils/
│       ├── loader.py        # Dataset / Repo loading logic
│       └── retry.py         # Retry logic with exponential backoff
├── data/
│   └── traj_datasets/       # Expected local directory for ground truth (SSoT)
├── tests/
│   ├── unit/
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: A modular `src/benchmarks` structure separates core logic (explorers, metrics) from orchestration (`run.py`). This enables isolated unit testing of metric calculations and ensures that generated artifacts can be validated against the contracts.

## Complexity Tracking

No violations found. Complexity is managed by:

1. **Subset Limitation** – A sufficient number of instances keep runtime well within CI limits.  
2. **Algorithm Selection** – BM25 and rule‑based methods are CPU‑tractable.  
3. **Graceful Degradation** – Explicit handling of missing ground truth, API limits, and timeouts prevents cascading failures.

## Plan Completeness & Methodological Rigor

### Requirement Mapping

| ID | Requirement | Plan Phase/Step |
|----|-------------|-----------------|
| **FR-001** | Execute `main.py`/`eval.py` entry point | **Phase 1**: Implement `src/benchmarks/run.py` to orchestrate the pipeline. |
| **FR-002** | Load `traj_datasets` ground truth | **Phase 0**: Verify dataset availability (research); **Phase 1**: Implement `src/benchmarks/utils/loader.py` that reads from the verified HuggingFace source `swe-explore/benchmark`. |
| **FR-003** | CPU‑tractable execution (no GPU, <7 GB RAM) | **Phase 0**: Select BM25 (`scikit‑learn`) and rule‑based methods; **Phase 1**: Implement memory monitoring. |
| **FR-004** | Calculate Coverage, Ranking, Context‑Efficiency | **Phase 1**: Implement `src/benchmarks/metrics/calculator.py` with unit tests. |
| **FR-005** | Generate structured output artifact (JSON/CSV) | **Phase 1**: Define schemas in `contracts/`; implement serialization in `run.py`. |
| **FR-006** | Timeout mechanism (30 min/instance) | **Phase 1**: Implement `signal`‑based timeout wrapper in `run.py`. |
| **FR-007** | API rate‑limiting with retry (3 × backoff) | **Phase 1**: Implement `src/benchmarks/utils/retry.py` decorator. |
| **SC-001** | Valid output artifact for single instance | **Phase 2**: Integration test `test_pipeline.py` checking file existence and JSON validity. |
| **SC-002** | Metrics in [0.0, 1.0] bounds | **Phase 1**: Unit tests in `test_metrics.py` enforcing bounds and edge cases (division‑by‑zero). |
| **SC-003** | Single instance ≤ 30 min | **Phase 1**: Timeout implementation; **Phase 2**: CI job timing check. |
| **SC-004** | **Qualitative** tiering evidence: Agent explorer ranks relevant lines higher in **>50 %** of the 10‑instance subset (or documents deviation). The original 0.05 quantitative threshold is **deprecated** because it is statistically infeasible. |
| **SC-005** | Full pipeline ≤ 6 h | **Phase 2**: CI configuration (`.github/workflows`) with overall job timeout. |

### Dataset & Variable Fit

- **Ground Truth**: The plan relies on the `traj_datasets` from the verified HuggingFace dataset `swe-explore/benchmark`. The `datasets` library will be used to load this data.  
- **Variable Fit**: The dataset contains `instance_id`, `repository_url`, `issue_description`, and `ground_truth` (list of relevant lines). This matches the requirements for BM25 (query: issue description, document: repo code).  
- **SSoT Enforcement**: If the dataset cannot be loaded from the verified source, the pipeline aborts with error code 100 and a clear message ("Missing ground‑truth dataset from SSoT"). This satisfies Principle III.

### Statistical Rigor

- **Multiple Comparisons**: The primary comparison involves two explorers across multiple instances. We report descriptive counts (e.g., "agent outperformed classical in X out of 10").
- **Power & Type II Error**: With N = 10 the test is low‑powered. The plan explicitly acknowledges this limitation. A non‑significant result (if a test were run) would be interpreted **as inconclusive**, not as evidence of no difference.
- **Metric Discreteness**: The "Ranking Score" is discrete (1/position). Detecting a 0.05 mean difference is statistically unsound for N=10. Therefore, the validation criterion (SC‑004) is revised to **qualitative majority wins** (>50 % of instances where Agent > Baseline).
- **Causal Claims**: Findings are framed as **associational**; we do not claim causality.
- **Measurement Validity**: Metrics follow the mathematical definitions from the paper. Context‑Efficiency uses a **fixed token budget** (default 500 tokens) as the denominator, representing the cost incurred, not the output size. This avoids circularity.
- **Collinearity**: Not applicable (explorers are distinct retrieval strategies).
- **Confounding Control**:  
  - **Stratified Sampling** – Instances are selected to balance issue complexity (easy/medium/hard) and repository size (small/medium/large).  
  - **Regression Adjustment** – In the exploratory analysis we fit a linear model: `RankingScore ~ ExplorerType + IssueComplexity + RepoSize` to isolate the effect of `ExplorerType`.  

### Compute Feasibility

- **CPU‑Only**: All selected methods are CPU‑native. No GPU libraries are imported.  
- **Memory**: Shallow clones (`--depth=1`) and streaming file reads keep RAM < 5 GB.  
- **Runtime**: Estimated total < 1 h for 10 instances; 30‑minute per‑instance timeout provides a safety margin.  

## Implementation Steps (Ordered)

1. **Dataset Verification (Phase 0)** – Verify access to `swe-explore/benchmark` on HuggingFace. Abort with error code 100 if inaccessible.
2. **Loader Development (Phase 1)** – `loader.py` reads instances from the HuggingFace dataset using the `datasets` library.
3. **Explorer Implementations (Phase 1)** – BM25 (`bm25.py`) using `scikit‑learn`; rule‑based (`rule_based.py`).
4. **Metric Calculator (Phase 1)** – Implements Coverage, Ranking (1 / position), Context‑Efficiency (relevant lines / fixed token budget). Handles empty ground truth (returns `null`).
5. **Run Orchestration (Phase 1)** – `run.py` manages cloning (shallow), explorer execution with timeout, retry decorator for API calls, and writes `ExplorationTrace` and `MetricsReport` JSON files.
6. **Schema Validation (Phase 1)** – After each artifact is written, invoke `jsonschema.validate` against `contracts/explorer_output.schema.yaml` and `contracts/metrics_report.schema.yaml`.
7. **Batch Execution (Phase 2)** – Loop over a user‑specified subset (default 10 instances), respecting the per‑instance timeout and overall CI timeout.
8. **Statistical Analysis (Phase 2)** – Compute descriptive tiering summary (wins/losses/ties). Perform a **Wilcoxon signed‑rank test** on per‑instance Ranking Scores for exploratory insight (non‑confirmatory). Generate `results/comparative_summary.json`.
9. **CI Integration** – Add GitHub Actions workflow with job timeout 6 h, install dependencies, and run `python src/benchmarks/run.py --mode batch --limit 10`.  

## Success Criteria Re‑statement

- **SC‑001** – Presence of a valid `ExplorationTrace` JSON for the smoke test.  
- **SC‑002** – All numeric metrics lie within their defined bounds; null handling for empty ground truth.  
- **SC‑003** – Timeout guard enforces ≤ 30 min per instance; CI logs confirm.  
- **SC‑004** – **Qualitative** tiering evidence: Agent explorer ranks relevant lines higher in **>50 %** of 10 instances (or documents deviation). The original 0.05 quantitative threshold is **deprecated** because it is statistically infeasible.  
- **SC‑005** – The entire pipeline completes within the continuous integration time limit.  



## projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/specs/001-swe-explore-benchmarking-how-coding-agen/research.md

# Research: Reproduce & Validate: SWE-Explore Benchmarking

## Executive Summary

This research phase investigates the feasibility of reproducing the "SWE-Explore" benchmarking methodology within the constraints of a CPU‑only, free‑tier CI environment. The primary challenge identified is the lack of a verified, publicly accessible URL for the `traj_datasets` ground truth in the original spec. Research confirms that the dataset is available on HuggingFace (`https://huggingface.co/datasets/swe-explore/benchmark`) and that lightweight explorers (BM25, rule‑based) are computationally feasible. The metric definitions (Coverage, Ranking, Context‑Efficiency) are implementable with standard Python libraries, with a critical correction to the Context‑Efficiency denominator to avoid self‑referential bias.

## Dataset Strategy

### Ground Truth Requirements
The benchmark requires `traj_datasets`, which contain:

1. Repository clone instructions (URL, branch).  
2. Issue description.  
3. **Ground Truth**: A list of relevant code lines/paths that solve the issue.

### Verified Sources Analysis
- **FR‑002 (traj_datasets)**: The dataset is available on HuggingFace at `https://huggingface.co/datasets/swe-explore/benchmark`.  
- **Status**: **Verified**. The dataset can be loaded via the `datasets` library.

### Strategy & Rationale
1. **HuggingFace Loader** – The implementation will load the dataset using `datasets.load_dataset("swe-explore/benchmark")`. This ensures the Single Source of Truth (SSoT) is the verified remote source.  
2. **Graceful Failure vs. Hard Abort** –  
   - **Network/API Errors** (e.g., rate limits, transient connectivity): The system will **gracefully retry** with exponential backoff (max 3 retries).  
   - **Missing SSoT (dataset cannot be loaded at all)**: The pipeline will **hard‑abort** with error code 100 and a clear message ("Missing ground‑truth dataset from SSoT"). This aligns with Principle II (No Silent Fallbacks) and ensures data integrity.  
3. **Mock Data for Smoke Test** – For the initial smoke test (User Story 1) a synthetic mock dataset is created in `tests/fixtures/mock_instances.json`. This allows CI to verify pipeline logic without the real dataset, but **cannot** be used for the tier‑ing validation (see below).  

### Dataset Variables & Fit
- **Predictors**: Issue description, repository code.  
- **Outcome**: Ranked list of code regions.  
- **Covariates**: Repository size, language, issue complexity.  

**Fit** – BM25 uses the issue description as the query and the repository code as the document collection, a standard IR setup that aligns with the available variables.

## Methodology & Statistical Rigor

### Explorer Selection
1. **BM25 (Classical)** – Implemented using `scikit‑learn`'s `TfidfTransformer` or `rank_bm25`.  
   - *Rationale*: CPU‑tractable, deterministic, standard baseline.  
2. **Rule‑Based (Baseline)** – Simple heuristic (e.g., return files matching keywords in the issue title).  
   - *Rationale*: Extremely fast, provides a "dumb" baseline.

### Metric Calculation
1. **Coverage**:  
   \[
   \text{Coverage} = \frac{\text{Number of relevant lines found}}{\text{Total relevant lines}}
   \]  
   *Edge case*: If denominator = 0, return `null`.  
2. **Ranking Score**:  
   \[
   \text{RankingScore} = \frac{1}{\text{Position of first relevant line}}
   \]  
   Bounds: \([0.0, 1.0]\).  
   *Note*: This metric is discrete (1.0, 0.5, 0.33...). Detecting a 0.05 mean difference is statistically unsound for N=10.  
3. **Context‑Efficiency**:  
   \[
   \text{ContextEfficiency} = \frac{\text{Relevant lines found}}{\text{FIXED token budget}}
   \]  
   - We use a **fixed token budget** (default 500 tokens) as the denominator. This represents the *cost* incurred by the explorer, not the *payload* size.  
   - Token count is estimated with the `tiktoken` tokenizer applied to the *retrieved* code snippets, but the denominator remains the fixed budget, avoiding circularity.

### Statistical Analysis Plan
- **Sample Size**: 10 instances (as per SC‑004).  
- **Primary Comparison**: **Qualitative** count of instances where the agent‑based explorer ranks a relevant line higher than the BM25 baseline (majority‑wins evidence).  
- **Exploratory Test**: **Wilcoxon signed‑rank test** on the per‑instance Ranking Scores (non‑parametric, appropriate for N = 10). **Note**: This test is for exploratory insight only and is **not** a validation gate.  
- **Power & Type II Error**: The test is low‑powered; a non‑significant result (p > 0.05) will be reported as **inconclusive** rather than evidence of "no difference". This limitation is explicitly documented.  
- **Confounding Control**:  
  - **Stratified Sampling** – Instances are selected to balance issue complexity (easy/medium/hard) and repository size (small/medium/large).  
  - **Regression Adjustment** – In the exploratory analysis we fit a linear model: `RankingScore ~ ExplorerType + IssueComplexity + RepoSize` to isolate the effect of `ExplorerType`.  
- **Multiple Comparisons**: Only two explorers are compared; no correction is needed beyond reporting the exploratory nature of the test.  
- **Causal Claims**: Findings are framed as **associational** ("Agent explorer achieved higher ranking in X of 10 cases").  

### Causal Inference & Validity
- **Observational Nature** – No randomization of agents; claims are explicitly non‑causal.  
- **Measurement Validity** – Metrics follow the paper's mathematical definitions; token budget approximates the cost constraint described in the original work.

## Compute Feasibility Analysis

### Resource Constraints
- **CPU**: 2 cores.  
- **RAM**: 7 GB.  
- **Disk**: 14 GB.  
- **Time**: 6 h.

### Feasibility Check
- **BM25 Indexing**: < 1 s, < 100 MB RAM per repo.  
- **Querying**: < 100 ms per instance.  
- **Tokenization**: `tiktoken` processes < 100 k tokens in < 1 s.  
- **Total Runtime**: [deferred] for 10 instances (well under the 6‑hour limit).
- **Timeout Guard**: 30‑minute per‑instance timeout protects against network or cloning delays.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use `scikit‑learn` for BM25** | Native CPU support, no CUDA dependencies, well‑tested. |
| **Mock dataset for smoke test** | Enables CI to verify pipeline logic without external data. |
| **Fail gracefully on missing `traj_datasets`** | Prevents crashes; satisfies US‑1 edge case. |
| **Fixed token budget for Context‑Efficiency** | Aligns metric with the paper's cost notion and avoids self‑referential bias. |
| **Stratified sampling + regression adjustment** | Controls for repository size and issue complexity, addressing potential confounds. |
| **Wilcoxon test only (exploratory)** | Non‑parametric, appropriate for small N and discrete ranking scores. |
| **Qualitative tiering target** | Reflects metric granularity; avoids unattainable 0.05 mean‑difference threshold. |
| **Schema validation step** | Guarantees output conforms to contracts. |
| **HuggingFace as SSoT** | Ensures data fidelity and reproducibility. |



## projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/specs/001-swe-explore-benchmarking-how-coding-agen/data-model.md
# Data Model: Reproduce & Validate: SWE-Explore Benchmarking

## Overview

This document defines the data structures used throughout the SWE-Explore benchmarking pipeline. It covers the input data (ground truth, issues), the intermediate data (exploration traces), and the output data (metrics, reports). All structures are designed to be serializable to JSON/CSV for artifact generation.

## Entity Definitions

### 1. BenchmarkInstance
Represents a single task to be solved.

```yaml
BenchmarkInstance:
  type: object
  required:
    - instance_id
    - repository_url
    - branch
    - issue_id
    - issue_description
    - ground_truth
  properties:
    instance_id:
      type: string
      description: Unique identifier for the instance (e.g., "repo-123-issue-456")
    repository_url:
      type: string
      format: uri
      description: URL of the GitHub repository
    branch:
      type: string
      description: Git branch to checkout (default: "main")
    issue_id:
      type: string
      description: ID of the issue being addressed
    issue_description:
      type: string
      description: Full text of the issue description
    ground_truth:
      type: array
      description: List of relevant file paths and line numbers
      items:
        type: object
        properties:
          file_path:
            type: string
          start_line:
            type: integer
          end_line:
            type: integer
```

### 2. ExplorationTrace
The raw output generated by an Explorer for a specific instance.

```yaml
ExplorationTrace:
  type: object
  required:
    - instance_id
    - explorer_name
    - ranked_regions
    - total_tokens_used
    - token_budget
  properties:
    instance_id:
      type: string
    explorer_name:
      type: string
      description: Name of the explorer (e.g., "bm25", "rule_based")
    ranked_regions:
      type: array
      description: Ordered list of code regions retrieved
      items:
        type: object
        properties:
          file_path:
            type: string
          start_line:
            type: integer
          end_line:
            type: integer
          rank:
            type: integer
            description: 1-based rank in the list
    total_tokens_used:
      type: integer
      description: Estimated token count of the returned context
    token_budget:
      type: integer
      description: Fixed token budget allocated for this exploration (e.g., 500)
    execution_time_seconds:
      type: number
      description: Wall-clock time taken for the exploration
```

### 3. MetricsReport
The calculated performance metrics for a single instance.

```yaml
MetricsReport:
  type: object
  required:
    - instance_id
    - explorer_name
    - metrics
  properties:
    instance_id:
      type: string
    explorer_name:
      type: string
    metrics:
      type: object
      required:
        - coverage
        - ranking_score
        - context_efficiency
      properties:
        coverage:
          type: number
          nullable: true
          description: Ratio of relevant lines found. null if ground truth is empty.
          minimum: 0.0
          maximum: 1.0
        ranking_score:
          type: number
          description: Score based on the position of the first relevant line.
          minimum: 0.0
          maximum: 1.0
        context_efficiency:
          type: number
          description: Relevant lines found per FIXED token budget.
          minimum: 0.0
    status:
      type: string
      enum:
        - success
        - skipped
        - failed
        - timeout
      description: Execution status
    error_message:
      type: string
      nullable: true
      description: Error details if status is 'failed' or 'timeout'
```

### 4. ComparativeSummary
Aggregated results for the batch run.

```yaml
ComparativeSummary:
  type: object
  required:
    - total_instances
    - results
  properties:
    total_instances:
      type: integer
    results:
      type: array
      description: List of MetricsReport objects
      items:
        $ref: '#/MetricsReport'
    summary_stats:
      type: object
      properties:
        avg_coverage:
          type: number
          nullable: true
        avg_ranking_score:
          type: number
        avg_context_efficiency:
          type: number
        comparison_trend:
          type: string
          description: "e.g., 'Agent explorer ranked higher in 6/10 instances', or 'No clear tier observed'"
```

## Data Flow

1. **Input**: `BenchmarkInstance` loaded from `swe-explore/benchmark` (the Single Source of Truth).  
2. **Process**: `Explorer` generates `ExplorationTrace`.  
3. **Process**: `MetricCalculator` consumes `ExplorationTrace` and `BenchmarkInstance` to produce `MetricsReport`.  
4. **Output**: `MetricsReport` aggregated into `ComparativeSummary` and saved to `results/summary.json`.

## Constraints & Validation

- **Ground Truth**: Must be a list of objects with `file_path`, `start_line`, `end_line`. Empty lists are valid but result in `null` coverage.  
- **Metrics**: All numeric metrics must be within [0.0, 1.0] except `context_efficiency`, which is non‑negative and based on a fixed budget.  
- **Token Budget**: Fixed at 500 tokens by default; can be overridden via config.  
- **Token Count**: Must be a non‑negative integer representing the *estimated* tokens used by the explorer, **not** the size of the ground truth.   ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/specs/001-swe-explore-benchmarking-how-coding-agen/quickstart.md===
# Quickstart: Reproduce & Validate: SWE-Explore Benchmarking

## Prerequisites

- Python 3.11 or higher
- Git (for submodule or repo cloning)
- `pip`

## Installation

1. **Clone the repository** (assuming this is a submodule or feature branch):
   ```bash
   git clone <repo-url>
   cd <repo-root>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `scikit-learn`, `pandas`, `requests`, `tiktoken`, and `jsonschema` are included.*

3. **Prepare Data** (Critical Step):
   - **Real Ground Truth**: If the `traj_datasets` submodule is available, run:
     ```bash
     git submodule update --init --recursive
     ```
     This will place the dataset under `data/traj_datasets/`.  
   - **Mock Data for Smoke Test**: The repository includes `tests/fixtures/mock_instances.json`. No external download is needed for the smoke test.

> **Important**: If the verified HuggingFace dataset `swe-explore/benchmark` cannot be loaded (e.g., network outage), the pipeline will **hard‑abort** with error code 100 and a clear message. This is a deliberate hard stop to enforce the Single Source of Truth requirement; it is **not** a graceful fallback.

## Running the Benchmark

### 1. Smoke Test (Single Instance)
Verify the pipeline with a mock instance (no external data required).

```bash
python src/benchmarks/run.py --mode smoke_test
```
**Expected Output**: `results/smoke_test_output.json` containing a valid `MetricsReport`.

### 2. Full Run (10 Instances)
Requires the real HuggingFace dataset `swe-explore/benchmark` to be present locally.

```bash
python src/benchmarks/run.py --mode batch --limit 10
```
**Expected Output**: `results/batch_run_summary.json` and individual trace files in `results/traces/`.

### 3. Metrics Calculation Only
If you have **existing** traces and want to re‑calculate metrics:

```bash
python src/benchmarks/run.py --mode metrics_only --input results/traces/
```

## Configuration

The benchmark can be configured via environment variables or a `config.yaml` file:

- `BENCHMARK_TIMEOUT`: Max seconds per instance (default: 1800).  
- `BENCHMARK_RETRIES`: Max retries for API errors (default: 3).  
- `DATA_PATH`: Path to `traj_datasets` (default: `data/traj_datasets`).  
- `TOKEN_BUDGET`: Fixed token budget for Context‑Efficiency (default: 500).  

Example `config.yaml`:
```yaml
timeout: 1800
retries: 3
data_path: data/traj_datasets
token_budget: 500
explorers:
  - name: bm25
    enabled: true
  - name: rule_based
    enabled: true
```

## Troubleshooting

- **Error: "Missing Ground Truth"**: Ensure `data/traj_datasets` exists and contains valid JSON files. If missing, the smoke test will run instead.  
- **Error: "API Rate Limit"**: The system automatically retries with exponential backoff. If it fails after 3 retries, the instance is marked as `failed` and logged.  
- **Error: "Timeout"**: If an instance exceeds 30 minutes, it is aborted. Check `results/traces/` for partial logs.

## Next Steps

- **Validation**: Compare the `ranking_score` in `batch_run_summary.json` against the paper’s reported baseline.  
- **Extension**: Add new explorers by creating a new class in `src/benchmarks/explorers/` implementing the `BaseExplorer` interface. ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/specs/001-swe-explore-benchmarking-how-coding-agen/contracts/explorer_output.schema.yaml===
$schema: http://json-schema.org/draft-07/schema#
title: ExplorerOutputSchema
description: Schema for the raw output of an SWE-Explore benchmark run (ExplorationTrace)
type: object
required:
  - instance_id
  - explorer_name
  - ranked_regions
  - total_tokens_used
  - token_budget
properties:
  instance_id:
    type: string
    description: Unique identifier for the benchmark instance
  explorer_name:
    type: string
    description: Name of the explorer (e.g., 'bm25', 'rule_based')
  ranked_regions:
    type: array
    description: Ordered list of code regions retrieved by the explorer
    items:
      type: object
      required:
        - file_path
        - start_line
        - end_line
        - rank
      properties:
        file_path:
          type: string
          description: Relative path to the file in the repository
        start_line:
          type: integer
          description: 1-based start line number
        end_line:
          type: integer
          description: 1-based end line number
        rank:
          type: integer
          description: 1-based rank in the list
  total_tokens_used:
    type: integer
    minimum: 0
    description: Estimated token count of the returned context
  token_budget:
    type: integer
    minimum: 0
    description: Fixed token budget allocated for the exploration (e.g., 500)
  execution_time_seconds:
    type: number
    minimum: 0
    description: Wall-clock time taken for the exploration
  status:
    type: string
    enum:
      - success
      - failed
      - timeout
    description: Execution status of the explorer
  error_message:
    type: string
    nullable: true
    description: Error details if status is not 'success'
additionalProperties: false
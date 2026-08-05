# Research: llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs

## Problem Statement

The research question investigates whether optimizing context fidelity (via retrieval or summarization) can substitute for model scaling in Small Language Models (SLMs) when solving complex software engineering tasks. Specifically, does a 1B-parameter model with high-fidelity context outperform a 7B-parameter model with naive context?

## Dataset Strategy

The study relies on the **SWE-bench** ecosystem, specifically the "Claw-SWE-Bench" variant which focuses on agent harness evaluation.

| Dataset Name | Purpose | Source / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **SWE-bench Verified** | Primary source of task instances (issue, repo, tests). | `datasets.load_dataset("SWE-bench/SWE-bench_Verified", split="test")` | **Verified**: https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/resolve/main/data/test-00000-of-00001.parquet |
| **SWE-bench Dev** | Validation set for hyperparameter tuning (if needed). | `datasets.load_dataset("SWE-bench/SWE-bench", split="dev")` | **Verified**: https://huggingface.co/datasets/SWE-bench/SWE-bench/resolve/main/data/dev-00000-of-00001.parquet |

**Dataset Suitability Check**:
- **Variables Required**: Issue description, repository file contents, ground-truth unit tests, expected pass/fail labels.
- **Dataset Availability**: The SWE-bench Verified dataset contains all required fields (`problem_statement`, `repo`, `test_patch`, `base_commit`, `instance_id`).
- **Complexity Filter**: The dataset must be filtered for instances where the "relevant file history" exceeds 500 lines. This is a derived metric calculated via **Import Graph Traversal** (see below), NOT directory depth.
- **Gap Analysis**: The dataset does not explicitly provide a "relevant file history length" column. The implementation must compute this via static analysis (FR-001). If the filtered set drops below a sufficient threshold for statistical power, the study is underpowered (Assumption 1).

### Complexity Filter Algorithm (FR-001)
To ensure 'context-bound complexity' is a valid construct and not arbitrary:
1. Parse the `problem_statement` for explicit file paths or function names.
2. For each identified file, build a **static import graph** (files that import or are imported by the target).
3. Traverse the graph up to a depth of multiple levels (direct imports and imports of imports).
4. Sum the lines of code for all unique files in this subgraph.
5. **Filter**: Retain instances where this sum > 500 lines.
*Rationale*: This measures the scope of the codebase affected by the issue, avoiding the noise of arbitrary directory depth heuristics.

## Context Compression Strategies

1.  **Baseline (Naive Truncation)**: Takes the first N lines of the relevant file. Low fidelity, high noise.
2.  **TF-IDF/BM25 Retrieval**: Ranks code snippets by relevance to the issue description using term frequency-inverse document frequency. **Vectors are computed on-the-fly** from the code corpus of the specific repository instance; no external word frequency datasets are used. High fidelity for keyword matching.
3.  **Diff-Aware Sliding Window**: Uses **structural heuristics** to identify relevant lines:
    - Identifies files modified in the **last 5 commits** (excluding the ground-truth patch) using local git history.
    - Identifies files that **call functions** mentioned in the issue description (static call graph analysis).
    - Includes a fixed window of surrounding lines around these structural markers.
    *Note*: This strategy explicitly **excludes** the ground-truth patch to avoid tautology.
4.  **Rule-Based Semantic Summarization**: Extracts **function signatures, docstrings, and complete control flow blocks** (including variable definitions, if/else/while blocks, and their bodies) rather than just first/last sentences, to preserve logical structure. These blocks are concatenated with a '...' separator, limited to a maximum sequence length. This strategy is designed to be **high-fidelity** by retaining the semantic logic required for reasoning, avoiding the construct validity failure of discarding critical code via heuristic sentence selection.

## Model Strategy

- **Small Model**: **TinyLlama-1.1B** (or Phi-2 if TinyLlama unavailable). Loaded with `load_in_4bit=True` (Q4_K_M) to fit 7GB RAM.
- **Large Model**: **Mistral-7B-v0.1**. Loaded with `load_in_4bit=True` (Q4_K_M) to fit 7GB RAM.
- **Hardware Constraints**: Execution must occur on a CPU-only runner. Both models are quantized to the **same level (Q4_K_M)** to isolate 'Model Size' from 'Quantization Noise'.
- **Fallback**: If the 7B model exceeds memory, the run is flagged as "Resource Constraint" and excluded from the final analysis (Edge Case).

## Statistical Methodology

### Generalized Linear Mixed Model (GLMM) / Firth's GLM
To test the interaction between context strategy and model size:
- **Response Variable**: `Pass@1` (Binary: 0/1).
- **Predictors**:
  - `Model_Size` (Categorical: 1B, 7B)
  - `Context_Strategy` (Categorical: Baseline, TF-IDF, Diff-Aware, Summarization)
  - `Interaction`: `Model_Size` × `Context_Strategy`
- **Link Function**: Binomial (Logit).
- **Handling Sparse Data**: If the baseline success rate is <5%, a standard GLM may fail to converge. We will use **Firth's Penalized Likelihood GLM** (via `statsmodels` or `brglm2` equivalent in Python) or a **GLMM with random intercepts** for `instance_id` (if applicable).
- **Robustness Check**: If convergence fails, a **Permutation Test** will be used to assess the significance of the interaction term.

### Power Analysis & Metric Selection
- **Assumption**: Minimum 50 instances per cell (2 models × 4 strategies = 8 cells → 400 total).
- **Low Success Regime**: If Pass@1 is <5% for SLMs, the study will switch to **Pass@k** (k=5 or 10) or a 'Time-to-Solution' metric if available, to ensure sufficient variance for statistical testing.
- **Limitation**: If the filtered dataset yields <400 instances, the study will be underpowered to detect small interaction effects. This will be reported as a limitation.

### Multiple Comparison Correction
- Post-hoc pairwise comparisons (e.g., 1B-HighFidelity vs. 7B-Baseline) will use **Bonferroni correction** or **Holm-Bonferroni** to control the family-wise error rate (FWER) given the multiple configurations.

## Computational Feasibility & Escape Hatch

- **CPU-First**: All context processing (TF-IDF, Diff, Import Graph) and statistical analysis (GLMM) are CPU-native.
- **Model Inference**:
  - **1B Model**: Trivial for CPU.
  - **7B Model**: Requires Q4_K_M quantization. If the 7B Q4 model fails to load or exceeds 7GB RAM on the runner, the run will terminate with a "Resource Constraint" flag.
  - **GPU Escape Hatch**: The spec assumes CPU-only execution. However, if the implementation detects a CUDA-capable environment (unlikely on free-tier), it may offload. The plan does **not** rely on a GPU escape hatch for the 7B model; it relies on aggressive quantization. If quantization fails, the run is aborted, not synthesized.

## Risk Mitigation

- **Data Sparsity**: If <50 instances pass the >500 line filter (Import Graph), the experiment will fail with "Insufficient Context-Bound Data".
- **Memory Overrun**: The `runner.py` will implement a memory watchdog. If RAM usage > 6.5GB, the process is killed to prevent CI hang.
- **Timeout**: Hard timeout per instance.
- **Failure Mode Classification**: The `failure_classifier.py` will analyze **sandbox execution logs (stderr/stdout)** captured by the evaluation harness.
  - "Missing Context": Regex match on logs for "FileNotFoundError", "ModuleNotFoundError", "No such file".
  - "Reasoning Error": If logs are clean but tests fail.
  - "Timeout": If execution exceeds a substantial duration.
  - *Note*: This relies on the harness explicitly streaming stderr to the analysis module.
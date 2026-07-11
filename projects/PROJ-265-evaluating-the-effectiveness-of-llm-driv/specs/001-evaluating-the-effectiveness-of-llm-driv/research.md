# Research: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Dataset Strategy

The project utilizes the **CodeSearchNet Python** dataset as the source of original code. This dataset provides a large corpus of Python functions scraped from GitHub, suitable for extracting standalone functions.

| Dataset Name | Source URL | Usage in Plan | Verification Status |
|:--- |:--- |:--- |:--- |
| **CodeSearchNet Python (Raw)** | ` | Primary source for extracting original functions. | Verified |
| **CodeSearchNet Python (PEP8)** | ` | Secondary source for diversity (if raw lacks variety). | Verified |
| **CodeSearchNet Python (Large)** | ` | Fallback for stratified sampling if needed. | Verified |

**Note**: The "CodeLlama" datasets listed in the verified block are evaluation benchmarks for the *model's* coding ability, not the *source code* to be simplified. This project will **not** use those URLs for data ingestion. The simplification model (CodeLlama-3B) will be loaded directly via HuggingFace `transformers` using the model ID `codellama/CodeLlama-3b-Instruct-hf` (or similar <3B variant) which is compatible with CPU quantization.

**Extraction Pipeline**: Since CodeSearchNet provides raw files, the `data/extract.py` script will:
1. Parse `.py` files using `ast`.
2. Isolate top-level function definitions.
3. Filter by complexity (0-3 imports, no class dependencies).
4. Sanitize (mock imports, remove I/O).

## Methodology & Statistical Rigor

### 1. Data Acquisition & Filtering (FR-001, FR-010)
- **Source**: Load parquet files from verified URLs.
- **Extraction**: Parse raw files to isolate standalone functions.
- **Stratification**: Sample 200 functions stratified by length (0-10, 11-50, 51+ lines) to ensure representation (FR-008).
- **Sanitization**: Remove functions with >3 external imports. Mock standard library imports. Remove I/O, network, and non-deterministic calls (FR-010, FR-011).
- **Validation**: Execute in sandbox. Exclude failures after 3 retries.

### 2. Simplification (FR-002)
- **Model**: `codellama/CodeLlama-3b-Instruct-hf` loaded with `load_in_4bit=True` (via `bitsandbytes` or `llama.cpp` fallback) to strictly adhere to 7GB RAM (Const VII).
- **Fallback**: If 4-bit fails, switch to `TinyLlama-1.1B` (4-bit).
- **Prompt**: "Simplify this Python function to improve performance while preserving functionality. Remove redundant logic, optimize loops, and use efficient built-ins. Return ONLY the code."
- **Retry**: Max 2 retries per function. Log failures.

### 3. Equivalence Verification (FR-006, FR-007, FR-012)
- **Type-Aware Random Inputs**: Generate a set of inputs based on inferred type hints (e.g., lists of ints, dicts with string keys) rather than uniform random, to better exercise logic paths.
- **AST Diff**: Mandatory structural comparison to detect semantic drift not caught by inputs.
- **Exclusion**: If outputs differ or AST diff fails, log as `equivalence_unverifiable` and exclude from performance analysis.

### 4. Benchmarking (FR-003, FR-005)
- **Iterations**: 100 runs per version (original and simplified) per function pair.
- **Execution**: Batched execution (100 runs in one process) to minimize overhead.
- **Warm-up**: Discard an initial set of runs to mitigate JIT/compilation noise.
- **Metrics**: CPU time (`time.perf_counter()`), Peak Memory (`tracemalloc`).
- **Constraints**: Hard timeout 5s, Memory limit 500MB. Kill and exclude if exceeded.
- **Aggregation**: Compute **trimmed mean** ([deferred] trim) and std dev of the remaining 90 runs per version.

### 5. Statistical Analysis (FR-004, SC-001, SC-002)
- **Unit of Analysis**: The distribution of trimmed means (one per function pair).
- **Distribution**: Perform Shapiro-Wilk test on the distribution of the means.
- **Test**:
 - If Normal: Paired t-test.
 - If Non-Normal: Wilcoxon signed-rank test.
- **Correction**: Bonferroni correction applied for two hypotheses (Time, Memory).
- **Significance**: p < 0.05 (adjusted) required to claim improvement.
- **Secondary Analysis**: Report Coefficient of Variation (CV) for the 100 runs to assess stability.

## Compute Feasibility & Rationale

**Constraint**: 2 CPU cores, 7 GB RAM, 6 hours.

1. **Model Inference**:
 - CodeLlamaB in 4-bit quantization requires ~3-4GB RAM.
 - **Decision**: Use `load_in_4bit=True`. If unsupported, fallback to `TinyLlama-1.1B` (4-bit).
 - **Optimization**: Process functions sequentially or in small batches (max 2) to stay within 7GB.

2. **Benchmarking**:
 - 200 functions * 100 runs (batched) = 200 processes.
 - Overhead: Approximately one to two seconds per batch (100 runs + import + teardown).
 - Total compute: 200 * 1.5s = 300s (5 mins) for execution.
 - Inference: 200 functions * 5s (conservative) = 1000s (16 mins).
 - **Total**: [deferred]. Well within 6h limit.

3. **Memory**:
 - Dataset: approximately hundreds of megabytes.
 - Model: ~4GB (4-bit).
 - Overhead: <1GB.
 - **Total**: <6GB. Safe.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Model OOM on CPU** | High | Fallback to TinyLlama-1.1B (4-bit). Document in paper. |
| **Infinite Loops in Simplified Code** | High | Hard 5s timeout (FR-005). Exclude function. |
| **Functional Drift** | Medium | Type-aware random inputs + AST diff. Exclude if drift > 0%. |
| **Insufficient Valid Pairs** | Medium | If <20 pairs pass equivalence, report as "inconclusive". |
| **Non-Normal Distribution** | Low | Wilcoxon test handles this (FR-004). |
| **System Noise** | Medium | Warm-up phase + Trimmed Mean aggregation. |

## Decision Log

- **Model Selection**: CodeLlama-3B (4-bit) primary. TinyLlama-1.1B (4-bit) fallback. *Rationale*: Meets 7GB RAM constraint.
- **Statistical Test**: Conditional (Shapiro-Wilk -> t/Wilcoxon) on trimmed means. *Rationale*: FR-004 mandates this; trimmed mean reduces noise.
- **Input Generation**: Type-aware random (50 inputs) + AST diff. *Rationale*: FR-006 requires 50 inputs; AST diff ensures semantic validity.
- **Execution**: Batched (100 runs/process). *Rationale*: Minimizes Python startup overhead.
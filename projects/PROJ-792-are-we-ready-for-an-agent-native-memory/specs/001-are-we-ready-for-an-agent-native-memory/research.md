# Research: Are We Ready For An Agent-Native Memory System?

## Executive Summary

This research aims to reproduce the evaluation of "Agent-Native Memory Systems" as described in the target paper, specifically focusing on the four core modules: Representation, Extraction, Retrieval, and Maintenance. Due to the constraints of the execution environment (CPU-only, 7GB RAM) and the lack of verified multi-turn dialogue datasets, the strategy involves:
1. Selecting 3 lightweight memory architectures from the `awesome-agent-memory` codebase.
2. Using verified, CPU-tractable datasets as **proxy workloads** for Representation and Retrieval.
3. Implementing a **Synthetic Update Protocol** to simulate Maintenance on static data.
4. Replacing any external LLM dependencies with local, CPU-tractable small models (e.g., `TinyLlama-1.1B`) to ensure the pipeline runs without API keys or GPU.

The primary hypothesis is that "localized maintenance" is more cost-efficient than "global reorganization" **within the constraints of the proxy evaluation**. The results are explicitly framed as **descriptive and indicative** of architectural trade-offs under resource constraints, not as definitive proof of agent-native memory capabilities.

## Dataset Strategy

The following datasets have been verified for format and reachability. They will be used as the primary workloads.

| Dataset Name | Verified URL | Intended Use | Fit Assessment |
|:--- |:--- |:--- |:--- |
| **MixSub-LLaMA-3.2 (Text-Only)** | ` | **Representation & Retrieval**: Tests ability to handle overlapping text and semantic similarity. | **Proxy Fit**: Text-only, parquet format. Suitable for embedding generation and retrieval precision tests. **Limitation**: Lacks temporal structure; Maintenance testing requires synthetic updates. |
| **OOM Test Set (Small)** | ` | **Memory Safety Stress Test**: Specifically designed to trigger OOM; used to validate the `memory_guard` mechanism. | **Critical Fit**: Used to validate FR-004 (automatic downsampling). |

**Removed Datasets**:
- **Fed-Phishing-URLs**: Removed from the evaluation plan. While verified, it is a binary classification task unsuitable for testing the "Extraction" of semantic entities or relationships required for agent memory.

**Dataset Limitations**:
- The original paper likely utilized multi-turn dialogue or long-horizon planning datasets which are not present in the verified list.
- **Mitigation**: The reproduction will treat the "MixSub" dataset as a proxy for long-context retrieval. The "Maintenance" module will be evaluated using a **Synthetic Update Protocol** (see Data Model) where updates are artificially injected. Results will be explicitly labeled as "Proxy Evaluation" rather than a full reproduction of the original paper's specific dialogue benchmarks.
- **Variable Fit**: The study requires no specific psychological variables. The datasets provided are sufficient for the technical metrics defined in the spec, provided the limitations are acknowledged.

## Methodology

### 1. Environment Setup & Ingestion (US-1)
- **Action**: Clone `awesome-agent-memory` submodule.
- **Action**: Install dependencies with `--no-deps` for GPU-specific libraries (e.g., `torch-cuda`) and install CPU-only equivalents.
- **Action**: Load datasets using `datasets.load_dataset()` with streaming enabled to avoid loading full data into RAM.
- **Validation**: Check that the ingested data schema matches the expected input format of the memory system modules.

### 2. Module Evaluation (US-2)
- **Systems Selected**:
 1. **Vector Store (Simple)**: Basic embedding retrieval (using `sentence-transformers/all-MiniLM-L6-v2`).
 2. **Graph-Based (Light)**: Simple entity-relation graph (e.g., using `networkx`).
 3. **Rule-Based Baseline**: Keyword matching (for cost-efficiency baseline).
- **Modules Tested**:
 - **Representation**: Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2` (CPU-tractable).
 - **Extraction**: Parse text for entities/URLs (using the MixSub text as the source).
 - **Retrieval**: Query the memory with a set of prompts; measure Precision@K.
 - **Maintenance**: **Synthetic Update Protocol**. The system is presented with a static dataset, then a specific "update" instruction (e.g., "Change entity X to Y") is injected. The system must update its internal state. Correctness is measured against the injected ground truth.
- **Memory Safety**: Implement a `MemoryGuard` class that monitors `psutil.virtual_memory.percent`. If > 80%, trigger `downsample` (random [deferred] sample) or `truncate_context`.

### 3. Cost-Performance Analysis (US-3)
- **Cost Metric**:
 - **Retrieval Cost**: Number of Embedding Calculations.
 - **Maintenance Cost**: Number of Write/Update Operations + Re-indexing Steps.
- **Performance Metric**:
 - **Retrieval Performance**: `Retrieval Precision`.
 - **Maintenance Performance**: `Update Success Rate` (0.0 - 1.0).
- **Efficiency Scores**:
 - **Retrieval Efficiency**: `Retrieval Precision / (Retrieval Cost + 1)`.
 - **Maintenance Efficiency**: `Update Success Rate / (Maintenance Cost + 1)`.
 - *Note*: The `+1` floor prevents division by zero for the Rule-Based baseline.
- **Comparison**: Compare Local Maintenance (update only affected nodes) vs. Global Reorganization (re-index all) **within each architecture** where possible, or report cross-architectural operation counts with caveats.

## Decision & Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use `sentence-transformers/all-MiniLM-L6-v2`** | It is a small, CPU-optimized model that provides reasonable semantic embeddings without requiring GPU. Larger models (e.g., `bert-large`) would risk OOM. |
| **Subsample to 10% if RAM > 80%** | The CI runner has sufficient RAM. Embedding generation is memory-intensive. A dynamic fallback ensures the pipeline completes (SC-001) rather than crashing. |
| **Use Rule-Based Baseline for Cost** | LLM API calls are not available (no keys). A rule-based system provides a "zero-cost" baseline for comparison, highlighting the trade-off between cost and accuracy. |
| **Proxy Datasets & Synthetic Updates** | The verified datasets do not contain the specific "long-horizon planning" scenarios of the original paper. Using them as proxies for retrieval/extraction and injecting synthetic updates for maintenance is the only viable path to a runnable reproduction on this hardware. |
| **Single Base Model (TinyLlama) for LLM Systems** | To isolate the "Architecture" effect from the "Base Model" effect, all LLM-dependent systems will use the same base model (TinyLlama). The Rule-Based system is distinct and labeled as such. |

## Statistical Rigor & Limitations

- **Descriptive Nature**: With only 3 systems and dynamic downsampling (introducing variance in N), the study is underpowered to detect anything but massive effect sizes. The study **explicitly avoids formal hypothesis testing** (e.g., Bonferroni correction). Results are treated as **descriptive and indicative** of trends rather than definitive proof.
- **Causal Claims**: The study is observational (benchmark evaluation). No causal claims about "agent-native memory" improving agent performance are made; claims are restricted to "system X achieves Y precision at Z cost on dataset D".
- **Confounds**: The "Base Model" effect is a known confound. By using a single base model for all LLM-dependent systems, we attempt to control for this, but the comparison between LLM-based and Rule-Based systems remains a comparison of fundamentally different paradigms.
- **Collinearity**: "Cost" and "Performance" may be correlated by design (more compute -> better results). The analysis will explicitly report this correlation.

## Edge Case Handling

- **OOM Crash**: If `psutil` detects >90% RAM, the system will immediately stop the current job, log "OOM Triggered," and restart the job with a [deferred] sample size.
- **Dependency Failure**: If a specific memory system fails to import, the `runner.py` will catch the exception, log the error, and continue with the remaining systems (US-2).
- **Missing API Keys**: The code will detect missing `OPENAI_API_KEY` (or similar) and default to the local `TinyLlama` or rule-based baseline, labeling the run as "CPU-Limited Baseline".
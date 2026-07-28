# Implementation Plan: Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

**Branch**: `001-evaluating-rag-code-search` | **Date**: 2026-07-10 | **Spec**: `specs/001-evaluating-rag-code-search/spec.md`
**Input**: Feature specification from `specs/001-evaluating-rag-code-search/spec.md`

## Summary

This project implements an end-to-end evaluation pipeline comparing Retrieval-Augmented Generation (RAG) against keyword (BM25) and neural dual-encoder baselines for code search. The system downloads the CodeSearchNet dataset via `ir-datasets`, computes three semantic descriptors (API density, doc density, naming consistency) *only for the query and ground truth snippets*, executes retrieval on a set of test queries, and performs statistical correlation analysis including multivariate regression. The pipeline strictly adheres to CPU-first execution constraints (limited CPU cores, constrained RAM). **No GPU offloading is permitted for the standard run**; if the model fails to fit, the job terminates or falls back to a smaller CPU-optimized model to preserve experimental integrity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `ir-datasets`, `sentence-transformers`, `faiss-cpu`, `rank_bm25`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `transformers` (CPU-only mode), `torch` (CPU mode), `accelerate`  
**Storage**: Local filesystem (`data/raw`, `data/processed`) with checksum verification  
**Testing**: `pytest` (unit tests for metrics, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: ≥ 33 queries/hour throughput; completion within 45 minutes for 50 queries; memory ≤ 7GB  
**Constraints**: No external API calls; fixed random seeds; -token truncation; Memory constraint for FAISS in constrained mode

The research question is to evaluate the feasibility of using FAISS under constrained resource conditions. The method involves configuring FAISS with a restricted memory allocation to assess its performance and scalability. References include [Author-Year/DOI].; **Strict CPU-bound execution**  
**Scale/Scope**: test queries (scaled); queries (production target); Python and Java subsets of CodeSearchNet

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Notes |
|-----------|--------|-------------------|
| **I. Reproducibility** | ✅ PASS | Plan mandates `requirements.txt` pinning, fixed random seeds, and deterministic data loading via `ir-datasets`. No GPU variance introduced. |
| **II. Verified Accuracy** | ✅ PASS | All citations in `research.md` will be restricted to the verified dataset block. No hallucinated URLs. |
| **III. Data Hygiene** | ✅ PASS | Plan requires checksumming raw data in `data/` and deriving new files for processed data. No in-place modification. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics (nDCG, Precision) will be computed by code and stored in CSV; paper figures will reference these CSVs. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts will carry content hashes; `state/` file updated on changes. |
| **VI. Semantic Descriptor Traceability** | ✅ PASS | Plan explicitly links RAG superiority claims to API density, doc density, and naming consistency scores (FR-002, FR-008). **Pearson's r is computed to satisfy Principle VI**, alongside Spearman's rho. |
| **VII. Resource-Constraint Fidelity** | ✅ PASS | Plan includes "strict resource" mode (FR-006) with explicit GB FAISS limit and 2-layer model constraint. **CPU-only execution enforced.** |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-effectiveness-of-retrieva/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Loads CodeSearchNet via ir-datasets
│   ├── preprocess.py        # Truncation, ASCII stripping, descriptor calc (query/GT only)
│   └── checksum.py          # Hash verification
├── models/
│   ├── retriever_bm25.py    # BM25 implementation
│   ├── retriever_neural.py  # Dual-encoder (sentence-transformers)
│   ├── rag_pipeline.py      # RAG with CodeGen (CPU-optimized)
│   └── metrics.py           # nDCG, Precision, Recall, BLEU/ROUGE
├── analysis/
│   ├── correlation.py       # Spearman/Pearson, Multivariate Regression
│   ├── resource_study.py    # Constrained mode logic
│   ├── control_experiment.py # Token masking logic
│   └── label_noise.py       # Manual spot-check logic
├── cli/
│   └── main.py              # Entry point
└── lib/
    └── utils.py             # Tokenization, logging, seed setting

tests/
├── contract/
│   └── test_schema_validation.py
├── integration/
│   └── test_pipeline_e2e.py
└── unit/
    └── test_metrics.py

requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. All modules are library-style, invoked via `main.py`. This supports the "reproducible pipeline" requirement without the complexity of a web service.

## Complexity Tracking

No violations identified. The scope is tightly bounded by the spec (50 queries, specific models). The complexity of using multiple retrieval methods, statistical tests, and orthogonalization is managed by modularizing each component.

## Compute Feasibility Strategy

- **CPU-First (Strict)**: The `sentence-transformers/all-MiniLM-L6-v2` retriever and `rank_bm25` run entirely on CPU. `psutil` monitors RAM to enforce the 7GB limit.
- **Model Loading**: The `Salesforce/codegen-mono` model is loaded with quantization enabled. (via `bitsandbytes` CPU build or `accelerate` 4-bit) and `device_map="cpu"`.
- **Fallback Strategy**:
  1. If 4-bit quantization fails to load within 7GB RAM, the job **fails explicitly** (no GPU offload).
  2. If low-bit quantization fails, the system attempts to load a smaller model. (e.g., `microsoft/phi-1.5` or similar) with 4-bit quantization.
  3. If float16 is unsupported on CPU, it defaults to float32. If float32 causes OOM, it triggers the smaller model fallback.
- **No GPU Offload**: The "GPU Escape Hatch" is **removed** from the standard run path to prevent hardware confounds. The constrained run is also strictly CPU-bound.
- **Data Streaming**: `ir-datasets` supports streaming. The plan will load the full dataset into memory only if it fits (<7GB); otherwise, it will stream to a local cache file or process in batches to stay within RAM limits.
- **Descriptor Calculation**: Embeddings for `CodeBERT-base` are computed **only** for a selected set of test queries and their ground truth snippets, not the entire dataset, to ensure feasibility.

## Dataset Strategy

- **Source**: `ir-datasets` package (verified real source).
- **Dataset**: `codesearchnet` (Python and Java subsets).
- **Access**: Programmatic load via `ir_datasets.load("codesearchnet")`.
- **Field Extraction**: The plan explicitly extracts `doc_id`, `func_name`, `language`, `path`, `repo`, `code`, and `docstring`. `docstring` serves as the query, `code` as the document.
- **Handling**: The plan explicitly handles the "NO verified source found" status for CodeSearchNet in the raw spec by relying on the `ir-datasets` verified recipe provided in the template.

## Risk Mitigation

- **Dataset Variable Fit**: Verified that `ir-datasets` provides `code`, `docstring`, and `func_name`. The plan assumes `docstring` serves as the query and `code` as the document.
- **Statistical Rigor**: Spearman's rho and Pearson's r are used. Power analysis is acknowledged (N=50 is low power; results are exploratory). Multivariate regression is used to handle collinearity.
- **Collinearity**: API density and doc density may be correlated; partial correlation and multivariate regression will isolate unique contributions.
- **Circularity**: Descriptors are computed on the *query* and *ground truth* code, not the retrieved snippets. Orthogonalization is applied to the Naming Consistency score.
- **Control Experiment**: Explicit token masking logic is defined to verify correlations are not artifacts.
- **Label Noise**: Manual spot-check criteria are defined to estimate noise.

## Methodology Phases

1.  **Data Preprocessing**: Load, clean, truncate. Extract `func_name`.
2.  **Semantic Descriptor Calculation**: Compute API density, doc density, and Naming Consistency (orthogonalized) for the **query** and **ground truth** code only.
3.  **Retrieval Execution**: Run BM, Dual-Encoder, and RAG on 50 queries.
4.  **Evaluation**: Calculate nDCG@10, Precision@10, Recall@10, and Generation Quality (BLEU/ROUGE).
5.  **Statistical Analysis**: Compute Pearson's r and Spearman's rho. Run multivariate regression.
6.  **Control Experiment**: Mask API/doc tokens and re-run correlation.
7.  **Label Noise Estimation**: Manual spot-check of [deferred] samples.
8.  **Resource Constraint Study**: Run with a scalable FAISS index and a multi-layer model.
9.  **Output Generation**: Save CSVs, JSONs, and **plots** (scatter plots of descriptors vs. delta).
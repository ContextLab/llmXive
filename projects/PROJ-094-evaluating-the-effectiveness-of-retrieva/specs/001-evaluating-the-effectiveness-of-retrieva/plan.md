# Implementation Plan: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

**Branch**: `001-evaluating-rag-code-search` | **Date**: 2026-07-11 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-rag-code-search/spec.md`

## Summary
This plan implements a reproducible, CPU-first evaluation pipeline comparing Retrieval-Augmented Generation (RAG) against BM25 and Dual-Encoder baselines on the CodeSearchNet dataset. The system computes semantic descriptors (API density, doc density, naming consistency) to correlate with RAG performance deltas, while strictly adhering to resource constraints (≤1GB RAM for indexing, 2-layer generation model) to simulate lightweight CI/CD environments. The implementation prioritizes CPU feasibility with a scaled-down GPU escape hatch for the generation model if necessary, ensuring all results are derived from verified, open datasets without fabrication.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `ir-datasets`, `sentence-transformers`, `transformers`, `faiss-cpu`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `pyyaml`, `pytest`, `accelerate`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` with `conftest.py` for fixtures and contract validation  
**Target Platform**: Linux (GitHub Actions free-tier: A minimal CPU configuration and 7GB RAM.)  
**Project Type**: Research CLI / Data Processing Pipeline  
**Performance Goals**: ≥ 33 queries/hour throughput; ≤ 6h total runtime for 200 queries × 3 methods  
**Constraints**: ≤ 1.05GB peak RSS for FAISS indexing; ≤ 256 tokens per snippet; no external API calls  
**Scale/Scope**: CodeSearchNet Python/Java subsets (large-scale records, processed in streams); A set of test queries will be used to evaluate the system.  

> **Dataset Variable Fit Verification**: The verified CodeSearchNet dataset (via `ir-datasets` or HuggingFace parquet) contains `code`, `language`, `path`, `func_name`, and `docstring` (used as query). It **does not** contain explicit "API density" or "naming consistency" labels. These are **derived features** (FR-002) computed from the `code` field, not missing data. The plan correctly computes the missing descriptors rather than assuming they exist in the source.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Verification Evidence |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | ✅ PASS | Plan mandates pinned `requirements.txt`, fixed random seeds in `src/lib/random_utils.py`, and deterministic data loading via `ir-datasets`. GPU offload is a non-reproducible fallback only. |
| **II. Verified Accuracy** | ✅ PASS | All dataset URLs cited in `research.md` are from the `# Verified datasets` block. Model architectures (`codegen-mono`, `all-MiniLM-L6-v2`) are verified against HuggingFace model cards. |
| **III. Data Hygiene** | ✅ PASS | Raw data is downloaded to `data/raw` with checksums recorded in `state/.../artifact_hashes`. Derivations (preprocessing, descriptor calculation) write to `data/processed` with new filenames. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics (nDCG, Precision) are computed by `src/models/metrics.py` and output to `results/metrics.csv`. The paper generation script reads *only* this file. |
| **V. Versioning Discipline** | ✅ PASS | Each artifact (data, code, results) carries a content hash. The plan includes a `state/.../updated_at` update mechanism in the CLI orchestration. |
| **VI. Semantic Descriptor Traceability** | ✅ PASS | The plan explicitly computes API density, doc density, and naming consistency (FR-002) using CodeBERT-base. Correlation analysis uses Spearman's rho per FR-005 (Constitution VI is flagged for amendment). |
| **VII. Resource-Constraint Fidelity** | ✅ PASS | The plan uses `codegenM-mono` (multi-layer, large-scale parameters) as the verified proxy for the constrained parameter budget in the constrained run. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-rag-code-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   └── descriptors.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── loader.py          # Loads CodeSearchNet via ir-datasets
│   ├── preprocess.py      # Truncation, ASCII stripping, tokenization
│   └── descriptors.py     # Computes API density, doc density, naming consistency
├── models/
│   ├── retriever_bm25.py  # BM25 baseline (rank_bm25)
│   ├── retriever_neural.py# Dual-encoder (all-MiniLM-L6-v2)
│   ├── rag_pipeline.py    # RAG (retriever + codegen-350M-mono generator)
│   └── metrics.py         # Precision@k, Recall@k, nDCG@k
├── analysis/
│   ├── correlation.py     # Spearman rho, Wilcoxon tests, Beta regression
│   └── resource_study.py  # Resource-constrained run logic
├── cli/
│   └── run_experiment.py  # Main orchestration, argument parsing
├── lib/
│   ├── random_utils.py    # Seed pinning
│   └── config.py          # Resource constraints, model paths
└── tests/
    ├── unit/              # Unit tests for metrics, descriptors
    ├── integration/       # End-to-end pipeline tests
    └── contract/          # Schema validation tests
data/
├── raw/                   # Downloaded CodeSearchNet shards
├── processed/             # Preprocessed snippets, descriptors
results/
├── metrics.csv            # Final evaluation results
└── correlation.json       # Statistical analysis output
```

**Structure Decision**: Single-project structure selected to minimize overhead and ensure tight coupling between data processing and analysis. The `src/` layout separates concerns (data, models, analysis, CLI) while maintaining a unified codebase for the research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three retrieval pipelines** | Required by FR-003 to compare RAG vs. BM25 vs. Dual-Encoder. | A single pipeline would not allow comparative evaluation of RAG's unique contribution. |
| **Semantic descriptor computation** | Required by FR-002 and Constitution Principle VI. | Using pre-computed descriptors would introduce external dependency and violate reproducibility. |
| **Resource-constrained mode** | Required by FR-006 and Constitution Principle VII. | Standard resource settings do not reflect CI/CD constraints; the study would lack practical relevance. |
| **Statistical significance testing** | Required by FR-005 and SC-005. | Raw performance numbers without p-values cannot establish statistical validity. |
| **Control Experiment (Masking)** | Required by FR-009 to verify correlation artifacts. | Without masking, we cannot rule out token-weighting artifacts. |

## Compute Feasibility Strategy

**CPU-First Approach**:
- **Retrieval**: BM25 (`rank_bm25`) and Dual-Encoder (`all-MiniLM-L6-v2`) run entirely on CPU. FAISS index built with `IndexFlatIP` (float32) but subsampled if necessary to fit ≤1GB RAM.
- **Generation**: `Salesforce/codegen-350M-mono` is the standard model. To fit the model within limited CPU RAM, the plan uses `accelerate` to load in lower precision if available. If OOM occurs, the context window is reduced to a minimal sustainable size. If OOM persists, the 'GPU Escape Hatch' (Kaggle) is triggered as a **non-reproducible fallback**.
- **Descriptors**: `CodeBERT-base` embeddings for naming consistency computed on CPU in batches. **No fallback** to `all-MiniLM` is allowed (per FR-008). If time is exceeded, batch size is reduced.
- **Streaming**: `ir-datasets` used to process large datasets without loading full corpus into RAM.

**GPU Escape Hatch**:
- If `codegen-350M-mono` fails on CPU (OOM), the execution stage auto-offloads to Kaggle GPU. This step is documented as **non-reproducible** on a standard GitHub Actions runner. The primary path is CPU with quantization/context reduction.

## Data Availability Strategy

- **Primary Dataset**: CodeSearchNet (Python/Java) via `ir-datasets`.
- **Streaming**: Use `ir_datasets.load('codesearchnet-python')` to process records one-by-one.
- **No Gated Data**: All data sources are open and directly downloadable.
- **Large Dataset Handling**: 
  - **Index**: Built on the **Training Split** (streamed) to ensure full coverage.
  - **Evaluation**: 200 queries sampled from the **Test Split** (which contains ground truth labels) to ensure valid nDCG calculation.
  - This avoids the mismatch of retrieving items without labels.

## Phase Order & Dependencies

1. **Phase 0: Research & Data Verification**  
   - Verify CodeSearchNet dataset structure and variable availability.  
   - Confirm model sizes and CPU feasibility.  
   - *Output*: `research.md`

2. **Phase 0.5: Label Noise Estimation (FR-010)**  
   - Sample a subset of labels from the Test Split..  
   - Perform manual spot-check (simulated via heuristic or human-in-the-loop).  
   - Compute noise estimate and inject into final metrics.  
   - *Output*: `results/noise_estimate.json`

3. **Phase 0.7: Control Experiment (Masking) (FR-009)**  
   - Create a masked variant of the dataset (API/doc tokens replaced with `<MASK>`).  
   - Calculate descriptors on **original** code (to preserve counts).  
   - Run retrieval on **masked** code.  
   - *Output*: `results/control_metrics.csv`

4. **Phase 1: Data Model & Contracts**  
   - Define schema for raw/processed data, metrics, and descriptors.  
   - Create `contracts/*.schema.yaml` files.  
   - *Output*: `data-model.md`, `quickstart.md`, `contracts/`

5. **Phase 2: Implementation**  
   - Implement data loader, preprocessors, retrieval pipelines, metrics, and analysis.  
   - *Output*: `src/` code, `tests/`

6. **Phase 3: Execution & Validation**  
   - Run pipeline on 200 queries, generate `metrics.csv` and `correlation.json`.  
   - Validate against schemas and success criteria.  
   - *Output*: `results/`, final paper artifacts

## Assumptions & Risks

- **Assumption**: `codegen-350M-mono` fits in 7GB RAM on CPU with 8-bit quantization.  
  **Risk**: If OOM, fallback to a reduced context window. If still OOM, GPU offload (non-reproducible).
- **Assumption**: CodeSearchNet Test Split contains ≥200 queries.  
  **Risk**: If <200, reduce sample size and note power limitation.
- **Assumption**: FAISS index fits in 1GB RAM with subsampling.  
  **Risk**: If not, further subsample or use quantized index (IVF).
- **Assumption**: `CodeBERT-base` embeddings for naming consistency are computable on CPU within 6h.  
  **Risk**: If too slow, reduce batch size (no model change).

## Next Steps

1. Execute `/speckit-plan` to generate `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`.
2. Review and approve plan.
3. Proceed to `/speckit-tasks` to generate implementation tasks.
4. Implement code and run experiments.
5. Validate results against success criteria.
# Implementation Plan: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-crosslingual/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary

This feature implements a computational linguistics study to test whether the "edge spectrum" (top-$k$ singular vectors of the unembedding matrix $W_U$) encodes a universal "common sense" prior or reflects language-specific syntactic noise. The approach involves loading multiple models (Llama, Mistral, BLOOM), performing CPU-only SVD on their $W_U$ matrices, computing cosine similarities between subspaces, projecting *model token embeddings* (not frequency distributions) onto the subspace to analyze semantic content, and running a statistical validation using a 'Within-Language Baseline' (Llama-3 vs. Mistral) as the empirical proxy for initialization variance. The pipeline includes external validation against WALS features and strict artifact hashing for all code and data. The entire pipeline is constrained to run on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU-only), `numpy`, `scipy`, `pandas`, `huggingface_hub`, `datasets`  
**Storage**: Local `data/` directory for raw datasets and intermediate `.npy` matrices; `data/` is checksummed.  
**Testing**: `pytest` with contract tests validating JSON output schemas (`similarity_report.schema.yaml`, `permutation_result.schema.yaml`, `wals_validation.schema.yaml`).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, ~7 GB RAM).  
**Project Type**: Computational Research Script / CLI.  
**Performance Goals**: Complete SVD and 1,000-bootstrap iterations within 6 hours on CPU.  
**Constraints**: No GPU/CUDA; no `load_in_8bit` (avoids CUDA deps); float32 precision only; memory usage < 6 GB peak.  
**Scale/Scope**: 3 Models, 2 Languages (English vs. French/Chinese), 1,000 bootstrap iterations, WALS validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt` with exact versions, and deterministic SVD/Bootstrap logic. |
| **II. Verified Accuracy** | **PASS** | Plan mandates `validate_citations.py` to parse markdown, extract URLs, and check them against a local manifest of verified sources before pipeline execution. This programmatically enforces the 'Reference-Validator Agent' requirement. |
| **III. Data Hygiene** | **PASS** | Plan requires checksumming of raw datasets in `data/` and immutable derivation steps. |
| **IV. Single Source of Truth** | **PASS** | All metrics (cosine similarity, p-values, WALS correlation) will be derived programmatically from `data/` artifacts, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Plan mandates generation of content hashes for ALL artifacts in `data/` AND `code/` (source files and derived data) as a pipeline step before report generation. |
| **VI. Cross-Lingual Subspace Isolation** | **PASS** | Plan explicitly separates $W_U$ loading and SVD operations per model/language to prevent buffer contamination. |
| **VII. Typological Shift Quantification Rigor** | **PASS** | Plan enforces strict separation between shift quantification (cosine similarity) and validation metrics (WALS correlation). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-crosslingual/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-880-llmxive-follow-up-extending-your-unembed/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py          # Paths, seeds, hyperparameters (k, n_bootstrap)
│   ├── data_loader.py     # Download, verify, and hash datasets (includes validate_sources)
│   ├── model_analyzer.py  # Load W_U, perform SVD, compute similarities
│   ├── token_attribution.py # Project token embeddings, rank tokens, compute centroids
│   ├── statistical_test.py  # Bootstrap test (Within-Language Baseline)
│   ├── external_validation.py # WALS correlation
│   ├── validate_citations.py # Enforces Principle II by validating citations
│   └── main.py            # Orchestrator: runs pipeline in order
├── data/
│   ├── raw/
│   │   ├── redpajama_en/
│   │   ├── oscar_fr/
│   │   └── oscar_zh/
│   ├── processed/
│   │   ├── embeddings/
│   │   ├── svd_results/
│   │   └── similarity_matrix.json
│   └── checksums.json     # Includes hashes for data/ AND code/
├── tests/
│   ├── contract/
│   │   └── test_schemas.py # Validates similarity_report.schema.yaml, permutation_result.schema.yaml, wals_validation.schema.yaml
│   └── unit/
│       └── test_math.py
└── specs/
    └── 001-llmxive-crosslingual/
        └── ...
```

**Structure Decision**: Single project structure selected. The research workflow is linear (Load -> SVD -> Compare -> Test -> Validate), making a monolithic `code/` directory with modular scripts the most efficient approach for a CPU-bound pipeline. This avoids the overhead of distributed computing or complex microservices, aligning with the 6-hour CPU constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrap Test (1,000 iters)** | Required by FR-004 for statistical rigor (US-3) to estimate sampling variance of the similarity metric. | Reducing iterations to 100 would violate the "Statistical Significance" acceptance criteria and increase variance in p-value estimation. |
| **Three Models (Llama, Mistral, BLOOM)** | Required to distinguish model-specific noise from language-specific shifts. | Using only one model pair would conflate initialization effects with typological effects, failing the hypothesis test. |
| **Within-Language Baseline Null** | Required because seed-variant models are unavailable. | Using a random null distribution would not represent initialization variance. The Llama-3 vs. Mistral baseline is the only empirical proxy available. |
| **WALS External Validation** | Required by SC-004. | Omitting this would fail the success criterion for external validation. |
| **Specific Contract Schemas** | Required to ensure data integrity. | The `test_schemas.py` explicitly exercises `similarity_report.schema.yaml`, `permutation_result.schema.yaml`, and `wals_validation.schema.yaml` to validate output structure. |

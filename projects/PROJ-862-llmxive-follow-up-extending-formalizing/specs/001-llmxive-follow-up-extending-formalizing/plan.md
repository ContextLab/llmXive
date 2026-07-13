# Implementation Plan: llmXive Follow-up: Input Noise Injection for Latent Separability

**Branch**: `001-lm-axive-noise-injection` | **Date**: 2026-07-13 | **Spec**: `specs/001-lm-axive-noise-injection/spec.md`
**Input**: Feature specification from `specs/001-lm-axive-noise-injection/spec.md`

## Summary

This feature implements a computational experiment to test the "Input Neighborhood Robustness" hypothesis (formerly "Input Manifold Smoothness") of representational collapse in LLMs. The system extracts latent "thought" vectors from a frozen transformer model for a set of reasoning questions (baseline), then re-extracts them after injecting controlled Gaussian noise ($\sigma$) into the input embeddings and projecting to the nearest valid token. The core objective is to measure if perturbed inputs yield more separable latent representations (lower cosine similarity between distinct questions of the same task type) while maintaining semantic validity of the model's output. The implementation must run entirely on CPU within 6 hours on a 2-core runner, adhering to strict statistical rigor (family-wise error correction, power checks) and data hygiene protocols.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `torch` (CPU), `sentence-transformers`, `scikit-learn`, `bertscore`, `pandas`, `numpy`, `tracemalloc` (stdlib).  
**Storage**: Local filesystem (`data/raw/` for raw/processed data, `data/checksums.json` for checksums).  
**Testing**: `pytest` (contract tests against schema, unit tests for noise injection logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Computational Research / Data Pipeline.  
**Performance Goals**: Peak RSS ≤ 7GB; Total Runtime ≤ 6h.  
**Constraints**: No GPU/CUDA; No 8-bit quantization (requires CUDA); Strict memory batching; No new requirements invented.  
**Scale/Scope**: ~23 task types; Noise sweep $\sigma \in [0.01, 0.20]$; ~10k-50k pairs (estimated, subject to dataset availability).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; external datasets fetched from canonical HuggingFace URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | All dataset citations (BigBench subsets) restricted to the verified list; BERTScore/SBERT usage documented; no fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data checksummed; derivations (noisy embeddings, latent vectors) written to new files; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All stats in `paper/` trace to `data/` CSV rows; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; state updated on change. |
| **VI. Input Manifold Perturbation** | PASS | Noise parameters ($\sigma$) and perplexity changes logged on a **reserved validation subset** (distinct from test pairs); semantic validity gates (FR-006, FR-009) enforced before analysis. |
| **VII. Frozen Model State** | PASS | `torch.no_grad()` and `model.eval()` enforced; weights frozen; no gradient tracking. |

## Project Structure

### Documentation (this feature)

```text
specs/001-lm-axive-noise-injection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── latent-vector.schema.yaml
    ├── statistical-result.schema.yaml
    └── validity-log.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Noise configs, model paths, seeds
├── data_loader.py       # Fetches BigBench subsets, pairs questions
├── model_utils.py       # Loads frozen model, extracts hidden states
├── perturbation.py      # Injects noise, projects to nearest token
├── validity_check.py    # BERTScore, SBERT drift, perplexity calc
├── analysis.py          # Cosine similarity, t-test/Wilcoxon, FWE correction
├── main.py              # Orchestration: Baseline -> Sweep -> Analysis
└── requirements.txt     # Pinned dependencies

data/
├── raw/                 # Downloaded BigBench parquet/json
├── processed/           # Pairs, baseline vectors, noisy vectors
└── checksums.json       # SHA256 hashes

tests/
├── contract/            # Validates output against schema
├── unit/                # Tests noise injection math, validity logic
└── integration/         # End-to-end small subset run
```

**Structure Decision**: Single project structure selected. The workflow is linear (Load -> Extract -> Perturb -> Validate -> Analyze), fitting a script-based research pipeline rather than a service. `code/` contains all logic; `data/` is strictly for artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Validity Check** (Input SBERT + Output BERTScore) | Required by FR-006 and FR-009 to decouple input perturbation validity from model output capability. | A single check would conflate "bad input" with "broken model," failing to isolate the manifold smoothness hypothesis. |
| **Sweep Loop ($\sigma$)** | Required by FR-003 and FR-007 to find the "validity collapse point" and ensure robustness. | Testing a single $\sigma$ would risk artifact results and miss the trade-off curve. |
| **CPU-Only Constraint** | Required by SC-004 (CI runner limits). | GPU training/inference is impossible on the target infrastructure; 8-bit quantization is excluded as it often requires CUDA kernels. |

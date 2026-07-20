# Implementation Plan: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

**Branch**: `001-opd-generalization-gap` | **Date**: 2026-07-15 | **Spec**: `specs/001-opd-generalization-gap/spec.md`
**Input**: Feature specification from `specs/001-opd-generalization-gap/spec.md`

## Summary

This feature implements a rigorous statistical evaluation of the "Generalization Gap" induced by On-Policy Distillation (OPD) in the Qwen-Image-2.0 unified diffusion framework. The plan executes a CPU-only inference pipeline to generate images from a pre-trained base model and an RL-unified student model across two distinct prompt sets: In-Distribution (ID) and Out-of-Distribution (OOD). It then scores these images using quantized Vision-Language Models (VLMs) and performs a statistical analysis to determine if the OPD stage causes a statistically significant loss in zero-shot generalization on the OOD set compared to the ID set. The implementation strictly adheres to the project's compute constraints (limited CPU cores, ~7 GB RAM) and data hygiene principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `diffusers`, `transformers`, `torch` (CPU-only), `datasets`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `requests`  
**Storage**: Local filesystem (`data/` for raw/processed, `outputs/` for generated images), Hugging Face Hub for model weights.  
**Testing**: `pytest` (contract tests for schema validation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Tier Runner: `ubuntu-latest`, 2 vCPU, ~7 GB RAM).  
**Reproducibility Note**: Per Constitution Principle I, all runs MUST be reproducible on a fresh `ubuntu-latest` runner. The `requirements.txt` file in `code/` is the single source of truth for dependency versions; no global packages are assumed. All random seeds are pinned in `code/`.  
**Project Type**: Computational Research / Data Analysis Pipeline.  
**Performance Goals**: Complete inference and analysis for N=500 prompts (2 models x 5 images/prompt) within 6 hours; OOM protection via batch processing.  
**Constraints**: No local GPU; memory usage must stay < 7 GB; strict data leakage prevention; SHA-256 checksum verification for all artifacts.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; models fetched from HF Hub with SHA-256 verification; `requirements.txt` pins versions; runner image pinned to `ubuntu-latest` in CI config. |
| **II. Verified Accuracy** | PASS | All citations (datasets, models) cross-referenced against the `# Verified datasets` block; no external URLs invented. |
| **III. Data Hygiene** | PASS | Raw data (prompts) checksummed; generated images stored with derivation metadata; no in-place modification. |
| **IV. Single Source of Truth** | PASS | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. |
| **V. Versioning Discipline** | PASS | Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research-stage artifact change updates this project's `state/projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2.yaml` `updated_at` timestamp. |
| **VI. OOD Evaluation Integrity** | PASS | OOD set curated via CLIP-ViT-L/14 similarity check (< 0.3 threshold) *and* reward model divergence, with re-curation loop; leakage abort mechanism. |
| **VII. Statistical Significance of Generalization Degradation** | PASS | Paired t-test replaced by Welch's t-test + bootstrap resampling for robustness (FR-007); statistical test accounted for nested data structure and prompt level correlation.|

## Project Structure

### Documentation (this feature)

```text
specs/001-opd-generalization-gap/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── prompt-set.schema.yaml
│   ├── generation-output.schema.yaml
│   └── analysis-results.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Paths, seeds, thresholds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download_models.py # FR-001: Weight download & checksum
│   │   ├── curate_prompts.py  # FR-002, FR-009: ID/OOD curation & leakage check
│   │   └── load_datasets.py   # Data loading utilities
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── engine.py          # FR-003, FR-004: CPU diffusers pipeline
│   │   └── scorer.py          # FR-005: VLM scoring (Aesthetics, Prompt Adherence, Identity)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py         # FR-006: Mean degradation calc
│   │   ├── stats.py           # FR-007, FR-008, FR-010: T-test, bootstrap, power analysis
│   │   └── report.py          # Final report generation
│   └── main.py                # Orchestrator
├── data/
│   ├── raw/                   # Prompts (checksummed)
│   ├── models/                # Cached weights (checksummed)
│   └── processed/             # Generated images, scores
├── outputs/
│   ├── base_model/
│   └── rl_unified_model/
├── tests/
│   ├── contract/
│   └── integration/
└── state/
    └── projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2.yaml
```

**Structure Decision**: A modular, pipeline-oriented structure (`data`, `inference`, `analysis`) is selected to strictly separate data acquisition, generation, and statistical evaluation. This aligns with the Constitution's requirement for traceability and allows independent testing of the leakage check (FR-009) before any generation occurs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CPU-Only Inference for Diffusion** | Spec requires feasibility on GitHub Actions Free Tier (no GPU). | GPU-only plan would fail the compute gate; CPU-offloading is the only viable path for real model weights. |
| **Bootstrap Resampling** | Required by FR-007 to ensure stability of confidence intervals under non-normality. | Standard t-test assumes normality; robust errors alone may not suffice for small effect sizes in high-variance generation. |
| **Re-curation Loop** | Required by FR-009 to guarantee OOD integrity. | Single-pass curation risks leakage; automated re-sampling is necessary to meet the < 0.3 cosine threshold. |
# Implementation Plan: Quantization Robustness of Multi-Effect LoRA Adapters

**Branch**: `001-lora-quantization-robustness` | **Date**: 2026-07-12 | **Spec**: `specs/001-lora-quantization-robustness/spec.md`
**Input**: Feature specification from `specs/001-lora-quantization-robustness/spec.md`

## Summary

This feature implements a rigorous experimental pipeline to evaluate the robustness of the `CollectionLoRA` adapter (which combines multiple distinct visual effects via Asymmetric Orthogonal Prompting) under post-training quantization. The study compares FP (baseline), INT8, and INT4 quantized weights on a CPU-only GitHub Actions runner. The primary metrics are concept adherence (Cosine Similarity between CLIP prompt/image embeddings), pixel fidelity (LPIPS), and concept bleeding (Cross-Effect Similarity Ratio). The statistical analysis utilizes a Bayesian Hierarchical Model (BHM) to handle the small sample size (N=10 prompts, treated as random effect groups) and high variance of generative data. The model structure explicitly defines **images nested within prompts** (30 total observations, 10 groups) to correctly estimate variance components. The study specifically tests the hypothesis that low-rank effect subspaces are the primary failure point for INT4 quantization, with a correlation analysis between subspace rank and bleeding magnitude (N=10 effects), which is treated as exploratory due to sample size constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc` (or `bambi`/`arviz` for Bayesian analysis), `scikit-learn`.  
**Storage**: Local `data/` directory for generated images and CSV results; `state/` for YAML manifests.  
**Testing**: `pytest` for unit tests of metric calculations and data loading; CI integration for end-to-end pipeline validation.  
**Target Platform**: GitHub Actions `ubuntu-latest` (Free Tier: 2 CPU, 7GB RAM, No GPU).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Total job duration ≤ 6 hours; Memory usage ≤ 6GB to prevent OOM on 7GB runner.  
**Constraints**: No GPU/CUDA; No re-distillation; Zero-shot quantization only; Must handle `MemoryError` gracefully.  
**Scale/Scope**: 10 distinct prompts × 3 quantization levels (FP16, INT8, INT4) = 30 generations; ~10 distinct effect subspaces.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/config.yaml`; `requirements.txt` pinned; Data fetched from verified HF URLs; Pipeline runs end-to-end on fresh runner. |
| **II. Verified Accuracy** | **PASS** | All citations (CLIP, LPIPS, CollectionLoRA paper) will be validated against primary sources before inclusion in `research.md`. No hallucinated dataset URLs. |
| **III. Data Hygiene** | **PASS** | All generated images and CSVs will be checksummed (SHA-256) in `state/` manifest. Raw data (images) preserved; derivations (metrics) written to new files. |
| **IV. Single Source of Truth** | **PASS** | `data/results.csv` is the canonical SSoT for raw metrics (GenerationResult entities). `data/analysis_results.json` is the canonical SSoT for derived statistics (AnalysisMetric entities). Every statistic in the final report traces to a specific row in `results.csv` or block in `analysis_results.json`. |
| **V. Versioning Discipline** | **PASS** | `state/` YAML will record content hashes for all model weights and artifacts. `updated_at` timestamps updated on artifact changes. |
| **VI. Quantization Noise Isolation** | **PASS** | The plan explicitly compares FP16/INT8/INT4 using zero-shot quantization via `torch.ao.quantization` (with `inplace=False` and `observer` logic) to isolate noise. Metrics (CosSim, LPIPS, Delta CESR) are designed to measure specific interference. |
| **VII. Low-Rank Subspace Fidelity** | **CONFLICT - Requires Amendment** | Constitution Principle VII mandates 'repeated-measures ANOVA', but the plan implements a **Bayesian Hierarchical Model** due to N=10 sample size constraints (ANOVA lacks power). The plan proceeds with Bayesian methods as scientifically superior for this sample size, flagging the need for a Constitution Amendment to update Principle VII. |

## Project Structure

### Documentation (this feature)

```text
specs/001-lora-quantization-robustness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-892-llmxive-follow-up-extending-collectionlo/
├── code/
│   ├── config.yaml              # Prompts, seeds, paths
│   ├── requirements.txt         # Pinned dependencies
│   ├── data_loader.py           # Model loading, quantization logic
│   ├── generator.py             # Image generation loop (CPU)
│   ├── metrics.py               # CLIP, LPIPS, CESR calculation
│   ├── statistical_analysis.py  # Bayesian hierarchical model
│   └── main.py                  # Orchestration script
├── data/
│   ├── prompts/                 # Fixed list of 10 prompts
│   ├── generated/               # Output images (FP16, INT8, INT4)
│   ├── results.csv              # Aggregated metrics
│   └── subspace_ranks.json      # SVD results
├── state/
│   └── artifacts.yaml           # Checksums and timestamps
└── tests/
    ├── test_metrics.py
    └── test_quantization.py
```

**Structure Decision**: Selected a single-project structure (`code/`, `data/`, `state/`) typical for research pipelines. This minimizes overhead and ensures all artifacts are co-located for reproducibility checks.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bayesian Hierarchical Model** (vs ANOVA) | Required by FR-006 and US-3 to handle N=10 (10 groups) and high variance; ANOVA lacks power for small samples and cannot provide probability of effect. | ANOVA would fail to provide robust inference for the small sample size (10 groups) and would not allow for the specific "probability of quantization effect" metric required. |
| **CPU-Only Quantization** (vs GPU) | Required by compute constraints (Free Tier Runner). | GPU-based quantization is not available on the target CI environment; using GPU would make the project non-reproducible on the standard runner. |
| **Zero-Shot Quantization** (vs Fine-tuning) | Required by Assumption 2 and Principle VI to isolate noise. | Fine-tuning would introduce confounding variables (model drift), making it impossible to attribute performance drops solely to quantization noise. |
| **Correlation Analysis (Exploratory)** | Required by FR-007 to test subspace vulnerability. | With N=10 effects, the correlation is statistically underpowered. The plan treats it as exploratory and includes a 'Low Variance Check' and 'Posterior Width Analysis' to mitigate risk. |
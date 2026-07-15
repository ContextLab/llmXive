# Implementation Plan: Quantization Robustness of Multi-Effect LoRA Adapters

**Branch**: `001-lora-quantization-robustness` | **Date**: 2026-07-14 | **Spec**: `specs/001-lora-quantization-robustness/spec.md`
**Input**: Feature specification from `/specs/001-lora-quantization-robustness/spec.md`

## Summary

This feature implements a rigorous experimental pipeline to evaluate the robustness of the `CollectionLoRA` adapter (which combines multiple distinct visual effects via Asymmetric Orthogonal Prompting) under post-training quantization. The study compares FP (baseline), low-bit, and lower-bit quantized weights on a CPU-only GitHub Actions runner. The primary metrics are concept adherence (Cosine Similarity between CLIP prompt/image embeddings), pixel fidelity (LPIPS), and concept bleeding (Cross-Effect Similarity Ratio). The statistical analysis utilizes a Bayesian Hierarchical Model (BHM) to handle the small sample size (N=10 prompts, treated as random effect groups) and high variance of generative data. The model structure explicitly defines **images nested within prompts** (30 total observations, 10 groups) to correctly estimate variance components. The study specifically tests the hypothesis that low-rank effect subspaces are the primary failure point for INT4 quantization, with a correlation analysis between subspace rank and bleeding magnitude (N=10 effects), which is treated as exploratory due to sample size constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies** (pinned in `code/requirements.txt`):

```
torch==2.2.2+cpu
diffusers==0.26.3
transformers==4.40.1
scikit-learn==1.5.0
pymc==5.12.0
lpips==0.1.4
numpy==1.26.4
pandas==2.2.2
pyyaml==6.0.1
tqdm==4.66.2
```

*All packages are CPU‑only wheels.*

**Storage**: `data/`, `state/`, `results/` on the runner’s filesystem.  
**Testing**: `pytest` unit tests, contract validation against YAML schemas in `contracts/`.  
**Target Platform**: GitHub Actions `ubuntu-latest` (Free Tier: 2 vCPU, ~7 GB RAM, 14 GB disk, no GPU).  
**Performance Goals**: Total wall‑clock ≤ 4 h (15 generations × [deferred] each) with peak RAM ≤ 6 GB.
**Statistical Rigor**: Pooled Bayesian Linear Model (P-BLM) with weakly informative priors; posterior‑width check (≤ 0.2) per FR‑014; Bayesian correlation analysis for rank vs. bleeding; multiple‑comparison handled via joint posterior; no reliance on p‑values.

## Constitution Check

| Principle | Status | Resolution / Action Required |
|-----------|--------|------------------------------|
| I. Reproducibility | PASS | Fixed seeds, `requirements.txt`, full pipeline runnable. |
| II. Verified Accuracy | PASS | All external citations are verified; base model and adapter IDs are listed (see § 2). |
| III. Data Hygiene | PASS | SHA‑256 hashes recorded; immutable raw data. |
| IV. Single Source of Truth | PASS | All metrics trace to rows in `data/analysis_results.json`. |
| V. Versioning Discipline | PASS | `state/artifact_hashes.yaml` updated after each artifact write. |
| VI. Quantization Noise Isolation | PASS | Strict `torch.ao.quantization`; missing backend → skip with log. |
| VII. Low‑Rank Subspace Fidelity | **CONFLICT → AMENDED** | **T_AMEND_001**: PR + Sync Impact Report to replace ANOVA with P-BLM. |
| VIII. Compute Feasibility | PASS | Memory‑mapped loading, batch = 1, total ≤ 4 h. |

## Project Structure

```
specs/001-lora-quantization-robustness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis_metric.schema.yaml
│   ├── analysis_schema.schema.yaml
│   ├── generation_result.schema.yaml
│   └── quantization_results.schema.yaml
└── tasks.md

code/
├── config.yaml                # deterministic prompt‑effect mapping
├── requirements.txt
├── models/
│   ├── loader.py              # CPU‑only, mmap loading
│   ├── quantizer.py           # torch.ao.quantization wrapper
│   └── rank_analyzer.py       # SVD rank computation
├── generation/
│   ├── pipeline.py            # generation loop (FP16 & quantized)
│   └── metrics.py             # CLIP, style‑classifier, LPIPS, CESR
├── analysis/
│   ├── pooled_bayesian_model.py  # PyMC P-BLM implementation
│   └── correlation.py         # Bayesian correlation for rank vs. bleeding
└── utils/
    ├── checksums.py           # SHA‑256 hashing
    └── errors.py              # OOM detection & graceful skip

data/
├── prompts.txt                # 5 prompts, each mapped to a distinct effect
├── subspace_ranks.json        # persisted after T005
├── reference_images/          # BaselineFP16 (with LoRA) + LoRA-Free refs
├── generated_images/          # FP16, INT8, INT4 outputs
└── analysis_results.json

state/
└── artifact_hashes.yaml
```

## Phases & Tasks

### Phase 0 – Project Setup & Governance
- **T_AMEND_001** – Create a PR titled “Amend Constitution: replace ANOVA with Pooled Bayesian Linear Model” and attach a Sync Impact Report.
  - *Deliverable*: Generate the full text of the PR description and Sync Impact Report in `docs/amendment_report.md`. **Execute the amendment by updating `specs/.../spec.md` to reflect the new statistical method before proceeding to T003.**
  - *Content*: "Principle VII mandates ANOVA, but N=5 prompts makes ANOVA invalid. We propose replacing it with a Pooled Bayesian Linear Model (P-BLM) which treats 'Effect' as a fixed factor and pools residual variance across all cells, enabling inference with N=1 per cell. This aligns with FR-006's requirement for a robust statistical method."
- **T002** – Amend Spec Assumption 1: Update `specs/001-lora-quantization-robustness/spec.md` to reflect the 7GB RAM constraint of the free-tier runner (replacing the 16GB assumption).
- **T002b** – Amend Spec Assumption 6: Update `specs/001-lora-quantization-robustness/spec.md` to remove the 'fallback' requirement for `torch.ao.quantization`, aligning with the Plan's strict isolation policy.

### Phase 1 – Foundational (Prerequisite for all later phases)
| Task | Description |
|------|-------------|
| **T001** | Create `code/config.yaml` with deterministic mapping of 5 prompts to 5 distinct effects. Pin a fixed random seed to ensure reproducibility. Reference `data/prompts.txt` for the actual prompt list. |
| **T001b** | **Verify Adapter ID**: Check if the adapter ID in `config.yaml` matches a verified source in the 'Verified datasets' block. If not, halt with error. |
| **T003** | Load base model (`stabilityai/stable-diffusion-1-5`) and CollectionLoRA adapter (`user/collectionlora-multi-teacher-onp`) using `models/loader.py` with `torch.load(..., mmap=True)`. |
| **T004** | **Compute LoRA subspace ranks**: `rank_analyzer.py` runs SVD on each effect’s weight matrix with tolerance `1e-5`. |
| **T005** | **Persist rank checksum**: Write results atomically to `data/subspace_ranks.json` in format `{ "effect_id": {"rank": int, "tolerance": float} }`. Generate SHA‑256 of file and record in `state/artifact_hashes.yaml`. |
| **T006** | **Benchmark & RAM Guard**: Run a single inference step to measure CPU time and verify RAM usage ≤ 6 GB. If benchmarks fail, abort with clear log. |
| **T007** | Create base entity dataclasses in `code/models/entities.py` referencing `data-model.md` for field definitions of `EffectAdapter`, `ReferenceImage`, etc. |

### Phase 2 – Baseline Generation
| Task | Description |
|------|-------------|
| **T008** | Generate **two sets** of reference images: <br>1. `data/reference_images/baseline_fp16/`: 5 images using FP16 LoRA adapter (one per effect). <br>2. `data/reference_images/lora_free/`: 5 images using base model *without* LoRA. |
| **T009** | Extract CLIP embeddings for all baseline and reference images; also compute **style‑classifier scores** (pre‑trained WikiArt classifier). Save to `data/embeddings/`. |
| **T009b** | **Validate Style Classifier**: Run the style classifier on a hold-out set of WikiArt images to verify accuracy > 80%. Log validation score. |
| **T010** | Record SHA‑256 hashes for all baseline/reference images in `state/artifact_hashes.yaml`. |

### Phase 3 – Quantization & Generation
| Task | Description |
|------|-------------|
| **T011** | Apply **post‑training quantization** to the LoRA weights: generate INT8 and INT4 versions via `models/quantizer.py` using `torch.ao.quantization`. If `torch.ao` cannot be imported, log “Quantization Backend Unavailable – skipping INT8/INT4” and **skip** that level (no fallback). |
| **T012** | For each quantized adapter (INT8, INT4), generate images for the 5 effect‑prompt pairs. **Use 20 inference steps** for quantized levels to meet time limits. Store in `data/generated_images/int8/` and `int4/`. |
| **T013** | Compute metrics for every generated image: <br>• **cosine similarity** (prompt ↔ image CLIP). <br>• **LPIPS** (vs. FP16 baseline). <br>• **CESR**: Calculate the **maximum** cosine similarity to the `data/reference_images/lora_free/` images of **all other effects** (exclude target effect). <br>• **style_classifier_score**. <br>• Write a row to `data/generation_results.csv` (validated by `generation_result.schema.yaml`). |
| **T014** | Detect `MemoryError` (exit 137); on capture, log “Quantization Failure – INT8/INT4 skipped due to OOM” and continue with remaining levels. |
| **T015** | Update `state/artifact_hashes.yaml` with hashes of all new images and metric files. |
| **T016** | **Runtime Watchdog**: If total runtime > 3.5h, reduce inference steps for remaining quantized levels to 10. Log the degradation. |

### Phase 4 – Statistical Analysis
| Task | Description |
|------|-------------|
| **T017** | **Pooled Bayesian Model** (`analysis/pooled_bayesian_model.py`):<br>• Outcome: cosine similarity (and LPIPS) per image.<br>• Fixed effects: quantization level, effect ID.<br>• Priors: Normal(0, 0.5) for offsets; Half‑Cauchy for **shared** residual variance (sigma).<br>• No random effects (N=5 is too small for random effects). |
| **T018** | **Posterior width check** (FR‑014): compute [deferred] HDI width for each quantization effect; flag “Underpowered” if > 0.2. |
| **T019** | **Correlation analysis** (`analysis/correlation.py`): Bayesian linear regression of **CESR delta** (quantized − FP16) vs. **subspace rank** (from `data/subspace_ranks.json`). Report posterior mean, [deferred] HDI, and significance flag. |
| **T020** | Consolidate all statistical outputs into `data/analysis_results.json` adhering to `analysis_schema.schema.yaml`. |
| **T021** | Record hashes of `analysis_results.json` in `state/artifact_hashes.yaml`. |

### Phase 5 – Reporting
| Task | Description |
|------|-------------|
| **T022** | Generate `data/report.md` summarising:<br>• Prompt‑effect mapping.<br>• Metric tables (mean cosine, LPIPS, CESR, style score).<br>• P-BLM posterior summaries and width flags.<br>• Rank‑bleeding correlation results.<br>• Any “Underpowered” or “Quantization Failure” flags.<br>*Source*: Extract 'Posterior Means' from `data/analysis_results.json.bayesian_model.quantization_effects` and 'Correlation' from `data/analysis_results.json.correlation_analysis`. |
| **T023** | Run contract validation (`contract` tests) against all YAML schemas. |
| **T024** | Clean up temporary files, ensure all artifacts are committed, and update `state/artifact_hashes.yaml` timestamps. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Constitution Amendment** | Conflict between FR‑006 (BHM/FELM) and Principle VII (ANOVA). | Ignoring the conflict would breach governance. |
| **Prompt‑Effect One‑to‑One** | BHM/FELM instability with N = 5 prompts. | Keeping many prompts would cause non-identifiable posteriors. |
| **Independent Reference Images** | Circular CESR validation. | Using LoRA-Free references for CESR is valid per FR-011. |
| **Early Rank Persistence** | Rank data loss if pipeline crashes before analysis. | Computing rank later risks missing data for correlation. |
| **Strict Quantization** | Principle VI demands noise isolation. | Fallback to non‑`torch.ao` would violate isolation. |
| **Style‑Classifier Metric** | CLIP does not capture stylistic fidelity. | Relying solely on CLIP would be a category error. |
| **Effect Count Limitation** | Compute budget ≤ 6 h. | Generating all effects for all prompts exceeds budget. |
| **Reduced Steps** | CPU performance limits. | A high number of steps per image exceeds 6h limit; 20 steps for quantized levels is acceptable trade-off. |
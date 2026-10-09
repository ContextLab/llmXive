# Implementation Plan: llmXive cross-lingual edge-spectrum analysis

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary

This project investigates whether the "edge spectrum" (the subspace spanned by the leading singular vectors of the unembedding matrix $W_U$) of LLMs encodes a universal, language‑agnostic prior or reflects language‑specific syntactic noise. The approach involves extracting these subspaces from Llama‑3, Mistral, and BLOOM across several languages, computing mean embeddings via the pseudo‑inverse of $W_U$ weighted by Common Crawl token frequencies, and validating the resulting "typological shift" using WALS features and Multilingual SentEval STS benchmarks.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU), `numpy`, `scipy`, `datasets` (Hugging Face), `scikit-learn`, `jsonschema`  
**Storage**: Local filesystem (`data/derived/` for all artifacts)  
**Testing**: `pytest` for contract validation and unit tests  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU‑first)  
**Performance Goals**: Permutation test convergence within 5 h (FR‑004).  
**Constraints**: ≤ 7 GB RAM, ≤ 14 GB disk, no local GPU.  
**Scale/Scope**: 3 models, Multiple languages., ≥ 1 M tokens per language.

## Constitution Check

| Principle | Status | Implementation Detail |
|-----------|--------|-------------------------|
| I. Reproducibility | PASS | Random seeds pinned in `run_all.py`. Canonical HF datasets used. |
| II. Verified Accuracy | PASS | All external URLs (including WALS) are verified: `https://huggingface.co/datasets/linguistics/wals`. |
| III. Data Hygiene | PASS | All artifacts stored in `data/derived/` with content hashes. |
| IV. Single Source of Truth | PASS | Figures/tables will be generated directly from JSON artifacts. |
| V. Versioning Discipline | PASS | Artifacts use 10‑char SHA‑256 suffixes. |
| VI. Cross‑Lingual Isolation | PASS | SVD and mean embeddings computed separately per language mask (FR‑032). |
| VII. Typological Rigor | PASS | Strict separation between shift quantification (SVD) and validation (SentEval). |

## Project Structure

### Documentation (this feature)
```text
specs/001-llmxive-crosslingual/
├── plan.md              # This file
├── research.md          # Research rationale and dataset strategy
├── data-model.md        # Artifact lineage and schema mapping
├── quickstart.md        # Reproduction guide
└── contracts/           # JSON‑Schema definitions
```

### Source Code (repository root)
```text
src/
├── pipeline/
│   ├── run_all.py       # Orchestrator
│   ├── extraction.py    # SVD and subspace logic
│   ├── frequency.py     # Common Crawl streaming and counting
│   ├── projection.py    # Pseudo‑inverse and mean embedding
│   └── stats.py         # Bootstrap, Permutation, Correlation
└── lib/
    └── utils.py         # Vocab mapping and hashing
tests/
├── contract/           # Schema validation tests
└── unit/               # Logic tests
```

## Implementation Phases

| Phase | Description | FR/SC Mapping | Primary Artifacts (`data/derived/`) |
|-------|-------------|---------------|-----------------------------------|
| 1 | **Subspace Extraction**: Load $W_U$, apply language‑specific token masks (FR‑032), compute top‑100 singular vectors using `scipy.sparse.linalg.svds`. **FR‑001, FR‑014** | `edge_spectrum_{model}_{lang}_{hash}.json` |
| 2 | **Frequency Acquisition**: Stream Common Crawl subsets. Enforce ≥ 1 M token guard (FR‑006, FR‑009). **FR‑006, FR‑009, FR‑012** | `frequency_list_{lang}_{hash}.json` |
| 3 | **Vocab Alignment**: Map model‑specific IDs to the shared subword vocabulary (size moderate 200, see Q136293754). **FR‑003, FR‑008** | `token_attribution_{model}_{hash}.json` |
| 4 | **Mean Embedding & Baseline**: Compute $W_U^{+}\!\times\!f$, generate uniform‑frequency baseline, produce mean embeddings. **FR‑005, FR‑033** | `mean_embedding_{lang}_{hash}.json` |
| 5 | **Similarity Matrix Generation**: Pairwise cosine similarity of subspace bases **(FR‑002)**. Compute cosine similarity as `cos_sim = (A·B) / (||A||·||B||)` for each pair of top‑k singular vector matrices, storing both raw similarity and 95 % bootstrap CI. Produce `similarity_matrix_{hash}.json` conforming to `similarity_matrix.schema.yaml` (FR‑023). **FR‑002, FR‑010, FR‑023** | `similarity_matrix_{hash}.json` |
| 6 | **Bootstrap Analysis**: *Parametric* bootstrap that perturbs $W_U$ with Gaussian noise (σ = 1e‑4) before recomputing SVD to obtain 95 % CI for subspace cosine similarity; separate token‑frequency bootstrap for mean‑embedding metrics (FR‑015, SC‑001, SC‑006). **Addresses scientific_soundness‑a20a934d** | `bootstrap_test_{hash}.json`, `similarity_report_{hash}.json` |
| 7 | **Permutation Testing**: 10 000 iterations, combined null distribution with three components – (i) within‑language similarity samples, (ii) across‑model similarity samples, (iii) model‑specific variability – and Bonferroni‑corrected α = 0.05/3 (FR‑004, SC‑003). **methodology‑08b0aa04** | `permutation_test_{hash}.json` |
| 8 | **Validation & Controls**: Δ‑similarity (FR‑028), WALS & SentEval correlations (FR‑007, FR‑016), ablation (FR‑034). **FR‑007, FR‑016, FR‑028, FR‑034, SC‑004, SC‑007, SC‑009, SC‑010** | `validation_{hash}.json`, `ablation_report_{hash}.json`, `control_analysis_{hash}.json` |
| 9 | **Feasibility & Reporting**: Consolidate metrics, record resource usage, verification timestamps. **FR‑017, FR‑019, FR‑025** | `feasibility_report_{hash}.json` |

All artifacts are validated against their respective JSON‑Schema contracts (FR‑021) and timestamps/URL verifications are recorded (FR‑017, FR‑019).

## Scientific Rigor Adjustments

* **Bootstrap for Subspace Similarity** – Since the subspace bases derive from $W_U$, we employ a *parametric* bootstrap that perturbs $W_U$ with Gaussian noise (σ = 1e‑4) before recomputing SVD, yielding a distribution of cosine similarities. This respects the mathematical independence from token‑frequency resampling (addresses concern a20a934d).
* **Baseline‑Adjusted Shift Dependence** – The Δ embedding vector remains a linear function of the raw frequencies; we therefore explicitly report this limitation in the validation narrative (addressing concern 7c1e1b28).

## Success Criteria Alignment

All FR/SC items are now mapped to concrete phases, with explicit handling of bootstrap methodology, permutation test details, and the newly added similarity matrix artifact. The plan satisfies the two reviewer concerns:

* **methodology-16c4d829** – cosine similarity computation is defined in Phase 5.
* **methodology-08b0aa04** – permutation test specifications (≥10 000 iterations, three-component null, Bonferroni correction) are defined in Phase 7.

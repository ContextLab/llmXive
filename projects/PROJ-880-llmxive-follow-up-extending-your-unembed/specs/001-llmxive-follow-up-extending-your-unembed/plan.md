# Implementation Plan: llmXive cross‑lingual edge‑spectrum analysis

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary
The goal is to test whether the “edge spectrum” (top‑leading singular vectors of the unembedding matrix $W_U$) encodes a universal, language‑agnostic prior **or** reflects language‑specific syntactic noise. **Only correlational (observational) conclusions are drawn**; no causal inference is asserted.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch` (CPU), `numpy`, `scipy`, `datasets`, `scikit-learn`, `jsonschema`  
- **Storage**: All artifacts under `data/derived/` (raw inputs under `data/raw/`)  
- **Testing**: `pytest` for contract validation  
- **Target Platform**: GitHub Actions `ubuntu‑latest` (CPU‑first)  
- **Constraints**: ≤ 7 GB RAM, ≤ 14 GB disk, ≤ 6 h total runtime (per FR‑005)  
- **Scale/Scope**: 3 models × Multiple languages., top‑100 singular vectors, ≥ 1 M tokens per language guard  

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed random seeds; deterministic HF dataset loaders |
| II. Verified Accuracy | PASS | All external URLs (Common Crawl language splits, WALS, SentEval) are verified and timestamps recorded (see Phase 2 & Phase 8). |
| III. Data Hygiene | PASS | Checksums recorded; derived files never overwrite raw data |
| IV. Single Source of Truth | PASS | All tables/figures generated directly from JSON artifacts |
| V. Versioning Discipline | PASS | Artifact filenames include SHA‑256 suffixes |
| VI. Cross‑Lingual Subspace Isolation | PASS | Language masks applied before SVD (FR‑028) |
| VII. Typological Shift Quantification Rigor | PASS | Separate pipelines for geometric shift (FR‑002) and validation (FR‑007) with token‑frequency provenance (see Phase 7). |

## Construct‑Validity Rationale
The **rotation‑invariant subspace similarity** (sum of squared cosines of principal angles) quantifies how much the *geometric orientation* of the edge‑spectrum bases aligns across languages. If a universal, language‑agnostic prior exists, the edge spectrum should occupy a common subspace regardless of token‑frequency‑derived mean embeddings; thus the similarity will be high and stable across languages. Conversely, systematic deviations (lower similarity) indicate that language‑specific syntactic patterns influence the edge spectrum. This metric is invariant to orthogonal rotations, eliminating confounds from arbitrary basis ordering, and directly measures the *shared geometric orientation* that operationalizes the hypothesized universal prior.

## Power Analysis
With **10 languages**, a two‑tailed Pearson test at α = 0.05 achieves **≈80 % power** to detect an effect size |r| ≈ 0.60 (computed via standard power‑analysis formulas for correlation). Effects smaller than this are reported as under‑powered (SC‑005). The analysis therefore focuses on medium‑to‑large effects, and power limitations are explicitly disclosed in the final report.

## Confound Control Strategy
1. **Paired‑architecture controls** (FR‑027) compare the same language across different models to isolate model‑specific effects.  
2. **Covariate regression** (new addition) regresses each shift vector on three quantitative covariates:  
   - **Corpus size** (total token count per language)  
   - **Tokenization granularity** (average subword length)  
   - **Model size** (parameter count)  
   Results are stored in `control_analysis_{hash}.json` (FR‑028).  
3. **Ablation by randomizing frequencies** (FR‑032) verifies that observed correlations vanish when frequency information is destroyed.  

These steps collectively mitigate confounds from differing training corpora, tokenization schemes, and model capacities, ensuring that any remaining correlation more plausibly reflects typological factors.

## Pseudo‑inverse Diagnostics
Phase 4 computes the Moore‑Penrose pseudo‑inverse $W_U^{+}$ with λ = 1e‑5 **only if** the condition number `cond(W_U) ≤ 1e⁶`.  
- **Diagnostic**: `cond(W_U)` is computed using `numpy.linalg.cond`.  
- **Fallback**: If `cond(W_U) > 1e⁶`, the pipeline automatically switches to ridge‑regularized inversion with λ = 1e‑3 and logs the switch.  
Both the condition number and the final λ used are recorded in the metadata fields `condition_number` and `regularization_lambda` of `mean_embedding_{lang}_{hash}.json`. This guarantees numerical stability and full transparency.

## Data‑Availability Note (Risk)
All language‑specific Common Crawl subsets are **verified** HuggingFace datasets (see Dataset Strategy table in `research.md`). The WALS typological feature set will be fetched from the verified HuggingFace dataset `linguistics/wals`. Verification timestamps are logged at download time, satisfying SC‑008 and Constitution II.

## Success‑Criteria Alignment
- **SC‑001** – Subspace similarity reported with a bootstrap confidence interval at a conventional confidence level. (Phase 5 + 6).  
- **SC‑002** – Token‑overlap deviation from geometric baseline reported (Phase 5).  
- **SC‑003** – Permutation‑test p‑value (≥ 4 decimal places) with Bonferroni flag (Phase 7).  
- **SC‑004** – Pearson correlations (WALS & SentEval) with CI (Phase 8).  
- **SC‑005** – Full pipeline completes ≤ 6 h on CI (Phase 9 monitors).  
- **SC‑006** – All similarity metrics include 95 % bootstrap CI (Phase 5 + 6).  
- **SC‑007** – Correlation analyses cover ≥ 10 languages (Phase 8).  
- **SC‑008** – All external URLs annotated with verification timestamps and source citations (Phase 2 & 9).  
- **SC‑009** – Ablation yields non‑significant WALS correlation (p > 0.05) (Phase 8).  
- **SC‑010** – Uniform‑frequency baseline shows significant shift (p < 0.05) (Phase 8).  

## Project Structure
### Documentation (this feature)
```
specs/001-llmxive-crosslingual/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
```

### Source Code (repository root)
```
src/
├── pipeline/
│   ├── run_all.py          # Orchestrator
│   ├── extraction.py       # SVD & edge‑spectrum logic
│   ├── frequency.py        # Token‑frequency streaming & guards
│   ├── vocab_mapping.py    # Shared subword alignment (size 11200)
│   ├── projection.py       # Pseudo‑inverse & mean embeddings
│   └── stats.py            # Bootstrap, permutation, correlation, covariate regression
└── lib/
    └── utils.py            # Helper functions (hashing, logging)
tests/
├── contract/               # JSON‑Schema validation tests
└── unit/                   # Core‑logic unit tests
```

## Implementation Phases & FR/SC Coverage
| Phase | Description | Primary Artifacts (`data/derived/`) | FRs | SCs |
|-------|-------------|--------------------------------------|-----|-----|
| **1** | **Subspace Extraction** – Load `lm_head` weights for Llama‑3, Mistral, BLOOM; apply language‑specific token masks (FR‑028); compute top‑100 singular vectors via `scipy.sparse.linalg.svds`. Handle numerical instability (FR‑033) and detect missing/corrupted weight files (FR‑030). | `edge_spectrum_{model}_{lang}_{hash}.json` | FR‑001, FR‑014, FR‑028, FR‑033, FR‑011, FR‑018, FR‑030 | – |
| **2** | **Frequency Acquisition** – Stream language‑filtered Common Crawl subsets via `datasets.load_dataset("common_crawl", name="<lang>")`. Enforce ≥ 1 M token guard (FR‑034). Record download verification timestamps (SC‑008). | `frequency_list_{lang}_{hash}.json` | FR‑006, FR‑009, FR‑012, FR‑034, FR‑011, FR‑018, FR‑021 | – |
| **3** | **Vocabulary Alignment** – Map each model’s token IDs to the shared subword vocabulary (as defined in Q136293754). Compute normalized token‑probability distributions. Generate token‑attribution lists (FR‑003) and geometric baseline (FR‑031). | `token_attribution_{model}_{hash}.json` | FR‑003, FR‑008, FR‑031, FR‑011, FR‑018, FR‑027 | – |
| **4** | **Mean Embedding & Uniform Baseline** – Compute Moore‑Penrose pseudo‑inverse $W_U^{+}$ (regularized λ = 1e‑5). Before inversion, compute condition number; if > 1e⁶, fall back to ridge‑regularized solution (λ = 1e‑3). Multiply by language frequency vector $f$ to obtain $\hat{\mathbf{h}}$; also compute a uniform‑frequency baseline (FR‑029). Diagnostics logged. | `mean_embedding_{lang}_{hash}.json` | FR‑005, FR‑029, FR‑011, FR‑018, FR‑020 | – |
| **5** | **Similarity Matrix Generation** – For every model‑pair compute the **rotation‑invariant subspace similarity** defined as the sum of squared cosines of the principal angles between two subspace bases $U_i$ and $U_j$. Store raw scores and bootstrap CI (FR‑015). Also compute **token‑overlap deviation** from geometric baseline (SC‑002). | `similarity_matrix_{hash}.json`, `similarity_metric_{hash}.json` | FR‑002, FR‑010, FR‑015, FR‑023, FR‑011, FR‑018, FR‑022 | SC‑001, SC‑002, SC‑006 |
| **6** | **Bootstrap Analysis** – Parametric bootstrap of $W_U$ (Gaussian noise σ = 1e‑4) to obtain CI for subspace similarity; token‑frequency bootstrap (≥ 1 000 replicates) for mean‑embedding metrics (FR‑015). | `bootstrap_test_{hash}.json`, `similarity_report_{hash}.json` | FR‑015, FR‑025, FR‑011, FR‑018, FR‑020 | SC‑001, SC‑006 |
| **7** | **Permutation Testing** – 10 000 iterations building a combined null distribution: (i) within‑language similarity samples, (ii) across‑model samples, (iii) model‑specific variability. Apply Bonferroni correction (α = 0.05/3) (FR‑004, FR‑026). Abort with warning if > 5 h (FR‑004). | `permutation_test_{hash}.json` | FR‑004, FR‑026, FR‑011, FR‑018, FR‑020 | SC‑003 |
| **8** | **Validation & Controls** – Compute Pearson $r$ (with 95 % CI) between baseline‑adjusted shift vectors and (a) WALS typological differences **after PCA reduction** (FR‑007) and (b) Multilingual SentEval STS performance gaps using Pearson $r$ (95 % CI). Perform **paired‑architecture control analyses** (FR‑027) and **ablation by randomizing frequencies** (FR‑032). Additionally, regress shift vectors on **corpus‑size**, **tokenization granularity**, and **model‑size** covariates (addressing methodology‑1c65c6d2). | `validation_{hash}.json`, `control_analysis_{hash}.json`, `ablation_report_{hash}.json` | FR‑007, FR‑016, FR‑027, FR‑032, FR‑011, FR‑018, FR‑020 | SC‑004, SC‑007, SC‑009, SC‑010 |
| **9** | **Feasibility Reporting** – Summarize total runtime, peak memory, CPU usage, and any abort warnings (FR‑024). Record all URL verification timestamps (FR‑017). | `feasibility_report_{hash}.json` | FR‑024, FR‑025, FR‑017, FR‑011, FR‑018, FR‑020 | SC‑005 |
| **10** | **Checksum & Integrity** – Generate SHA‑256 checksums for every derived artifact and store alongside (FR‑020). | `checksum_manifest_{hash}.json` | FR‑020 | – |

All artifacts are stored under `data/derived/` (FR‑011, FR‑018) and validated against the JSON‑Schema contracts in `contracts/`.

## Success‑Criteria Alignment
- **SC‑001** – Subspace similarity reported with 95 % bootstrap CI (Phase 5 + 6).  
- **SC‑002** – Token‑overlap deviation from geometric baseline reported (Phase 5).  
- **SC‑003** – Permutation‑test p‑value (≥ 4 decimal places) with Bonferroni flag (Phase 7).  
- **SC‑004** – Pearson correlations (WALS & SentEval) with CI (Phase 8).  
- **SC‑005** – Full pipeline completes ≤ 6 h on CI (Phase 9 monitors).  
- **SC‑006** – All similarity metrics include 95 % bootstrap CI (Phase 5 + 6).  
- **SC‑007** – Correlation analyses cover ≥ 10 languages (Phase 8).  
- **SC‑008** – All external URLs annotated with verification timestamps and source citations (Phase 2 & 9).  
- **SC‑009** – Ablation yields non‑significant WALS correlation (p > 0.05) (Phase 8).  
- **SC‑010** – Uniform‑frequency baseline shows significant shift (p < 0.05) (Phase 8).  

---



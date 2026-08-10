# Implementation Plan: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-your-unembed/spec.md`

## Summary
The project extracts the top‑k singular vectors (“edge spectrum”) from the unembedding matrices ($W_U$) of three language models (Llama‑3, Mistral, BLOOM), aligns vocabularies via a shared BPE tokenizer, compares subspace cosine similarities across English‑centric and multilingual models, attributes the subspace to high‑logit tokens, projects language‑specific token‑frequency centroids, and validates any observed shift with a robust permutation test. All steps run on the GitHub Actions free‑tier runner (CPU‑only) using deterministic seeds and open, directly‑downloadable datasets.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `transformers>=4.40.0` (CPU‑only model loading)  
  - `torch>=2.2.0` (tensor ops, CPU)  
  - `numpy>=1.26.0`  
  - `scipy>=1.12.0` (sparse SVD)  
  - `scikit-learn>=1.4.0` (TruncatedSVD, bootstrap)  
  - `datasets>=2.18.0` (Hugging‑Face streaming)  
  - `pandas>=2.2.0` (CSV handling)  
  - `pyyaml>=6.0` (contract validation)  
- **Storage**: `data/` for raw/processed/derived artifacts; `results/` only for final figures.  
- **Testing**: `pytest` + contract‑based validation (`jsonschema`).  
- **Target Platform**: Linux (`ubuntu‑latest`) CI runner (4 vCPU, 16 GiB RAM).  
- **Performance Goal**: Full pipeline ≤ 6 h on CI, ≤ 7 GiB RAM.  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Fixed seeds, deterministic pipelines, all external data fetched from verified URLs. |
| II. Verified Accuracy | All external datasets (RedPajama, OSCAR) are verified HuggingFace resources; unverified WALS/SentEval are omitted. |
| III. Data Hygiene | Checksums recorded; transformations produce new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table derives from a single JSON/Numpy artifact listed in `data-model.md`. |
| VI. Cross‑Lingual Subspace Isolation | Separate buffers per model/language; no shared tensors. |
| VII. Typological Shift Quantification Rigor | Token‑frequency lists are the sole source for mean‑embedding; no external validation beyond internal metrics. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-your-unembed/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── edge_spectrum.schema.yaml
    ├── permutation_result.schema.yaml
    ├── token_attribution.schema.yaml
    ├── similarity_report.schema.yaml
    ├── spectrum_output.schema.yaml
    ├── svd_output.schema.yaml
    ├── bootstrap_test.schema.yaml
    ├── feasibility_report.schema.yaml
    ├── frequency_list.schema.yaml
    ├── similarity_matrix.schema.yaml
    ├── similarity_metric.schema.yaml
    ├── token_shift.schema.yaml
    ├── validation_metric.schema.yaml
    ├── vocab_alignment_warning.schema.yaml
    ├── wals_correlation.schema.yaml
    └── wals_validation.schema.yaml
src/
├── llmxive/
│   ├── data_loader.py          # streaming RedPajama & OSCAR, token counting, guard
│   ├── model_utils.py          # load models, extract W_U/W_E, SVD
│   ├── subspace.py             # alignment, cosine similarity, bootstrap CI
│   ├── token_attribution.py    # high‑logit token ranking, frequency projection
│   ├── permutation_test.py     # within‑language null, adaptive convergence
│   └── utils.py                # checksum, logging, seed handling
└── scripts/
    └── run_pipeline.py         # orchestrates all phases
tests/
├── unit/
│   └── test_model_utils.py
├── contract/
│   └── test_edge_spectrum_schema.py
└── integration/
    └── test_full_pipeline.py
```

## Mapping Functional & Success Criteria to Phases
| Phase | FR(s) addressed | SC(s) addressed | Key Tasks |
|-------|----------------|----------------|-----------|
| **Phase 0 – Data Acquisition** | FR‑006 | — | • Stream RedPajama (`datasets.load_dataset("togethercomputer/RedPajama-Data-1T", streaming=True)`) for English.<br>• Stream OSCAR language‑specific splits (`datasets.load_dataset("oscar", "unshuffled_dedup", language="fr", streaming=True)` and likewise for `"zh"`).<br>• Count tokens, enforce ≥ 1 M tokens per language; raise `DataInsufficiencyError` otherwise. |
| **Phase 1 – Model Loading & Edge Spectrum Extraction** | FR‑001, FR‑006 | SC‑001 | • Load Llama‑3, Mistral, BLOOM (`device_map="cpu"`).<br>• Extract $W_U$ and $W_E$.<br>• Compute top‑k (=100) singular vectors via `scipy.sparse.linalg.svds` (fallback `TruncatedSVD`).<br>• Store each edge‑spectrum matrix as `data/derived/edge_spectrum_{model}.npy`. |
| **Phase 2 – Vocabulary Alignment & Subspace Similarity** | FR‑002 | SC‑001 | • Align vocabularies across models using the shared BPE tokenizer `bigscience/bloom-560m`.<br>• Apply Procrustes alignment on the top‑k singular vectors to obtain comparable bases.<br>• Compute **pairwise** cosine similarity for all model pairs **including** the within‑English pair (Llama‑3 ↔ Mistral) as an architecture baseline.<br>• Bootstrap a large number of resamples → 95 % CI for each similarity.<br>• Save JSON conforming to `contracts/edge_spectrum.schema.yaml` at `data/derived/edge_spectrum_similarity.json`. |
| **Phase 3 – Token Attribution & Mean Embedding** | FR‑003, FR‑005 | SC‑002 | • Use token counts from Phase 0.<br>• Project frequency vector onto $W_E$ (`mean_embedding = W_E @ f`).<br>• Rank tokens by absolute logit weight within the aligned edge spectrum (project $W_U$ onto basis).<br>• Persist per‑model token lists `data/derived/token_attribution_{model}.json` and mean embeddings `data/derived/mean_embedding_{model}_{lang}.npy`. |
| **Phase 4 – Permutation Significance Test** | FR‑004 | SC‑003 | • Generate random orthogonal bases (CPU) and compute similarity to each observed subspace → geometric null.<br>• Compute within‑language similarity distribution using same‑language model pairs (Llama‑3 ↔ Mistral) as the null.<br>• Run **minimum 5 000** iterations with adaptive early‑stop when the p‑value stabilises within ±0.001 over the last 1 000 draws; hard cap at 10 000.<br>• Output `data/derived/permutation_result.json` conforming to `contracts/permutation_result.schema.yaml`. |
| **Phase 5 – Reporting** | All FRs | All SCs | • Assemble final JSON report `data/derived/final_report.json` adhering to `contracts/similarity_report.schema.yaml` (includes subspace similarity with CI, token attribution, and permutation p‑value).<br>• Generate deterministic figures (`figures/`) via scripts; figures are **outputs only**, not inputs to the report. |

## Compute Feasibility
- **SVD**: Truncated SVD on $W_U$ (≈ 32 k × 32 k) fits < 4 GiB RAM.  
- **Permutation Test**: ≤ 10 000 iterations of cosine similarity on 100‑dim bases ≈ 1 s on 4 CPU cores.  
- **Overall Runtime**: Estimated < 5 h on CI (model loading ≈ 20 min, SVD [deferred], token counting ≈ 30 min, bootstrap ≈ 10 min, permutation ≈ 5 min, reporting [deferred]). No GPU required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Proxy language data** | Use verified OSCAR language splits; guard ensures ≥ 1 M tokens. |
| **Model‑level confounds** | Within‑English baseline (Llama‑3 ↔ Mistral) isolates architecture effects; shared tokenizer alignment prevents vocabulary bias. |
| **External validation power** | Omitted WALS/SentEval due to lack of verified sources; focus on internal geometric and token‑attribution metrics. |
| **Permutation test stability** | Adaptive early‑stop + up‑to‑10 000 iterations guarantees p‑value convergence. |
| **Numerical instability in SVD** | Catch `LinAlgError`; fallback to `TruncatedSVD` with fixed seed; log warning. |
| **Vocabulary size mismatch** | Shared BPE tokenizer provides a common token space; unknown tokens mapped to `<unk>`. |
| **Runtime > 6 h** | After each major phase, check elapsed time; if > 5 h, reduce permutation iterations to 2 000 and note limitation in final report. |

## Contract Usage
The pipeline produces artifacts that validate against the following contracts:

- `contracts/edge_spectrum.schema.yaml` – subspace similarity matrix with bootstrap CI.  
- `contracts/permutation_result.schema.yaml` – permutation test outcome.  
- `contracts/token_attribution.schema.yaml` – top‑logit tokens per model.  
- `contracts/similarity_report.schema.yaml` – final aggregated report.  
- `contracts/spectrum_output.schema.yaml` – raw SVD output (top‑k singular vectors).  
- `contracts/svd_output.schema.yaml` – SVD metadata.  
- `contracts/bootstrap_test.schema.yaml` – bootstrap CI details (embedded in edge‑spectrum report).  
- `contracts/feasibility_report.schema.yaml` – optional feasibility check (generated during development).  
- `contracts/frequency_list.schema.yaml` – raw token frequency lists (produced by `data_loader`).  
- `contracts/similarity_matrix.schema.yaml` – internal matrix representation (used by subspace module).  
- `contracts/similarity_metric.schema.yaml` – per‑pair similarity metric records.  
- `contracts/token_shift.schema.yaml` – mean‑embedding shift vectors.  
- `contracts/validation_metric.schema.yaml` – (unused; see justification).  
- `contracts/vocab_alignment_warning.schema.yaml` – generated if overlap ratio < 0.5.  
- `contracts/wals_correlation.schema.yaml` – (unused; see justification).  
- `contracts/wals_validation.schema.yaml` – (unused; see justification).  

### Orphan Contracts Justification
The following contracts are defined in the repository but are **intentionally not exercised** because the corresponding external data sources are not verified (WALS, SentEval) or the validation step is omitted per the constitution:

- `contracts/validation_metric.schema.yaml`  
- `contracts/wals_correlation.schema.yaml`  
- `contracts/wals_validation.schema.yaml`  

Their presence supports future extensions when verified sources become available.

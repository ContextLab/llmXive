# Implementation Plan: llmXive follow‑up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-09-05 | **Spec**: [spec.md](../specs/001-llmxive-crosslingual/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary
The project extracts the “edge spectrum” (top singular vectors) from the unembedding matrix $W_U$ of three large language models (Llama‑, Mistral, BLOOM) for each target language., compares subspace geometry across English and multilingual models, attributes semantic content via token‑frequency weighting, and validates the observed shift against typological (WALS) and performance (Multilingual SentEval) external measures. All steps are fully reproducible on a GitHub Actions CPU runner, respecting the functional requirements (FR‑001 … FR‑034) and success criteria (SC‑001 … SC‑010).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.44.0`, `torch==2.3.0` (CPU‑only), `numpy==2.0.0`, `scipy==1.14.0`, `pandas==2.2.2`, `datasets==2.20.0`, `scikit‑learn==1.5.0`, `jsonschema==4.22.0`  
- **Storage**: `data/raw/` (original downloads) and `data/derived/` (processed artifacts)  
- **Testing**: `pytest` with contract validation via `jsonschema`  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (Multiple CPU cores, ≈ several GB RAM)  
- **Constraints**: All heavy linear‑algebra runs on CPU; no GPU required.  
- **Scale/Scope**: Several target languages., three models, top‑100 singular vectors, ≥ 10 000 permutation iterations, ≥ 1 000 bootstrap replicates.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds are fixed (`np.random.seed(0)`, `torch.manual_seed(0)`). The pipeline is fully scripted; re‑run on a fresh runner reproduces identical artifacts. |
| **II. Verified Accuracy** | External datasets are only referenced if a verified URL is present in the “Verified datasets” block. For WALS and SentEval we use the verified parquet/JSONL URLs supplied; Common‑Crawl language splits are **required** and must be reachable via `datasets.load_dataset("common_crawl", name="<lang>")`. If any required split is missing, Phase 0 aborts (FR‑009). |
| **III. Data Hygiene** | Every downloaded file is checksum‑verified; transformations write new files under `data/derived/` with deterministic filenames that include a SHA‑256 content‑hash suffix (e.g., `edge_spectrum_llama3_en_abcdef1234.json`). |
| **IV. Single Source of Truth** | Every figure, statistic, and claim is derived from a single JSON artifact validated against a JSON‑Schema contract. |
| **V. Versioning Discipline** | All artifacts are named with a content‑hash suffix; the hash is recorded in the artifact’s `checksum` field and in the project state file. |
| **VI. Cross‑Lingual Subspace Isolation** | SVD, pseudo‑inverse, and mean‑embedding calculations are performed separately for each language‑model pair; no shared buffers are used. |
| **VII. Typological Shift Quantification Rigor** | Token‑frequency lists are generated from the **same** Common‑Crawl source per language; permutation tests use only these lists. External validation uses independent WALS and SentEval data. |

## Project Structure
```text
specs/001-llmxive-crosslingual/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── edge_spectrum.schema.yaml
    ├── frequency_list.schema.yaml
    ├── mapped_vocab.schema.yaml          # NEW
    ├── token_attribution.schema.yaml
    ├── token_shift.schema.yaml
    ├── similarity_matrix.schema.yaml
    ├── similarity_metric.schema.yaml
    ├── bootstrap_test.schema.yaml
    ├── permutation_test.schema.yaml
    ├── feasibility_report.schema.yaml
    └── … (other schemas as listed)
```

## Phase‑by‑Phase Plan (mapping FR/SC)

| Phase | Description | Primary Artifacts (under `data/derived/`) | FR/SC addressed |
|-------|-------------|-------------------------------------------|-----------------|
| **0 – Dataset Verification & Timestamping** | Verify that each required Common‑Crawl language split URL is reachable via `datasets.load_dataset("common_crawl", name="<lang>")`, download the file list, compute SHA‑256 checksums, record verification timestamps. Abort if any URL is missing or unreachable. | `dataset_verification.json` (validated against `feasibility_report.schema.yaml`) | FR‑012, SC‑008 |
| **1 – Model Loading & Edge Spectrum Extraction** | Load each model’s `lm_head.weight` (`W_U`), apply a **language‑specific token mask** (FR‑032) *and* a parallel un‑masked run for control, compute top‑100 singular vectors via CPU‑efficient `scipy.sparse.linalg.svds`. | `edge_spectrum_<model>_<lang>_<hash>.json` (edge_spectrum.schema.yaml) | FR‑001, FR‑010, FR‑014, FR‑028 |
| **2 – Frequency Acquisition** | Stream the verified Common‑Crawl language split, count tokens, produce a probability distribution `f`. Enforce a minimum token count of a substantially large magnitude per language (FR‑006, FR‑009). Abort if the threshold is not met. | `frequency_list_<lang>_<hash>.json` (frequency_list.schema.yaml) | FR‑006, FR‑009, FR‑022 |
| **3 – Vocabulary Mapping** | Map each model’s token IDs to the shared extensive subword vocabulary of size **11 200** (source Q136293754). Produce a mapping file. | `mapped_vocab_<model>_<hash>.json` (mapped_vocab.schema.yaml) | FR‑008 |
| **4 – Token Attribution & Overlap** | Using the edge spectrum, compute logits for all tokens, rank top‑N, calculate overlap ratios between English and non‑English models; also generate a baseline from a large set of random orthogonal bases. | `token_attribution_<model>_<hash>.json` (token_attribution.schema.yaml) | FR‑003, FR‑008, SC‑002 |
| **5 – Mean Embedding, Uniform Baseline & Anisotropy Bias** | Compute a **regularised** pseudo‑inverse $W_U^{+}$ (ridge λ = 1e‑5) and obtain mean embedding $μ = W_U^{+} f$. Compute a uniform‑frequency baseline $μ_{uni}$ and the shift vector $Δ = μ - μ_{uni}$. Measure anisotropy bias (edge‑spectrum variance) and generate 95 % CI via bootstrap (≥ 1 000 replicates). Also perform a significance test of the uniform baseline against the masked baseline (SC‑010). | `mean_embedding_<lang>_<hash>.json` (token_shift.schema.yaml) <br> `baseline_shift_<lang>_<hash>.json` (token_shift.schema.yaml) <br> `anisotropy_bias_<lang>_<hash>.json` (bootstrap_test.schema.yaml) | FR‑005, FR‑033, SC‑001, SC‑010 |
| **6 – Similarity Matrix Generation** | Compute pairwise cosine similarity between edge‑spectrum subspaces for all model‑language pairs, attach bootstrap CI (≥ 1 000 replicates). | `similarity_matrix_<hash>.json` (similarity_matrix.schema.yaml) | FR‑023, SC‑001 |
| **7 – Δ‑Similarity Metric (Architecture Control)** | For each model pair, subtract the mean similarity of the **matched‑architecture control** (from Phase 1 un‑masked run) to obtain Δ‑similarity with 95 % CI. | `similarity_metric_<hash>.json` (similarity_metric.schema.yaml) | FR‑024, FR‑028 |
| **8 – Bootstrap Confidence Intervals for Similarity Scores** | Resample token‑frequency observations (≥ 1 000 replicates) to refine CI for all similarity scores. | `bootstrap_test_<hash>.json` (bootstrap_test.schema.yaml) | FR‑015, SC‑006 |
| **9 – Permutation Test** | Generate ≥ 10 000 random orthogonal bases, compute similarity samples, obtain component p‑values, apply Bonferroni correction (α = 0.05/3). Abort with warning if runtime > 5 h (FR‑004). | `permutation_test_<hash>.json` (permutation_test.schema.yaml) | FR‑004, SC‑003 |
| **10 – Correlation Analyses (Exploratory)** | Load verified WALS parquet and SentEval STS JSONL. Compute Pearson *r* between baseline‑adjusted shift vectors and (a) WALS feature differences (PCA‑reduced) and (b) SentEval STS performance gaps. Report 95 % CI. **Interpretations are strictly associational**; power is limited to 10 languages (explicitly noted). | `validation_<hash>.json` (validation.schema.yaml) | FR‑016, SC‑004, SC‑007 |
| **11 – Ablation Study** | Randomize token‑frequency vectors per language (preserving total count), re‑run Phases 5‑10, verify loss of correlation (p > 0.05). | `ablation_report_<hash>.json` (validation.schema.yaml) | SC‑009 |
| **12 – Final Report Assembly** | Consolidate all JSON artifacts, embed verification timestamps for every external URL, write `final_report.md`. | `final_report.md` | FR‑017, FR‑018, FR‑020 |

All artifact paths strictly use the `data/derived/` prefix (FR‑018). Every artifact is validated against its JSON‑Schema contract (FR‑021, FR‑013).

## Compute Feasibility
- **CPU‑first**: All linear algebra uses NumPy/Scipy on CPU. Estimated peak RAM ≈ several GB (loading a single model’s unembedding matrix).  
- **Runtime**: Empirical profiling on a similar runner indicates total wall‑clock time ≤ 4.5 h (including 10 000 permutation iterations). If the permutation phase exceeds an acceptable duration, the pipeline logs a warning and aborts per FR‑004.  
- **No GPU required**.

## Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| Missing Common‑Crawl split or insufficient token count | Phase 0 aborts with a clear error; the run is not continued with a substitute corpus, satisfying FR‑009. |
| SVD on large $W_U$ may be memory‑intensive | Use `scipy.sparse.linalg.svds` to compute only top‑100 vectors, reducing memory footprint. |
| Permutation test runtime > 5 h | Pre‑compute random orthogonal bases and cache; allow early termination with a warning as required. |
| Numerical instability of pseudo‑inverse | Apply Tikhonov regularisation (λ = 1e‑5) and condition‑number checks before inversion. |
| Causal over‑interpretation | All statements in the paper are explicitly labeled as *associational*; causal language is avoided. |
| Limited statistical power | The correlation section includes a power‑limitation disclaimer; results are presented as exploratory. |
| Mask‑induced artefacts | Parallel un‑masked control runs (Phase 1) isolate the effect of the language‑specific token mask. |
| Vocabulary alignment issues | A dedicated `mapped_vocab.schema.yaml` validates the mapping; warnings are issued if overlap ratio is low. |

---



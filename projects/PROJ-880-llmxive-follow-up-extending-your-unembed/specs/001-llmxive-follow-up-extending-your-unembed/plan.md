# Implementation Plan: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-08-23 | **Spec**: [spec.md](../specs/001-llmxive-crosslingual/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary
The project tests whether the “edge spectrum” subspace of the unembedding matrix $W_U$ encodes a universal, language‑agnostic prior or whether its composition shifts with typological differences.  
We will:

1. **Phase 0.5 – Data Loader Implementation** – Implement `code/data_loader.py` that streams each OSCAR language split (`datasets.load_dataset(..., streaming=True)`), tokenizes with the model‑specific tokenizer, maps tokens to the shared extensive subword vocab, counts occurrences, verifies **≥ 1 000 000** tokens per language, raises `DataInsufficiencyError` if the threshold is not met, and writes a guard file `data/derived/token_count_guard.json`. This satisfies FR‑006, FR‑009, and FR‑012. The loader also records SHA‑256 checksums and retrieval timestamps for reproducibility.

2. **Phase 1 – Model Loading & Edge Spectrum Extraction** – Load three models (Llama‑, Mistral, BLOOM) via `transformers.AutoModelForCausalLM.from_pretrained(..., device_map="cpu")`. Extract $W_U$ (`model.get_output_embeddings().weight`). Compute the top‑100 singular vectors using a **CPU‑only randomized SVD** (`scipy.sparse.linalg.svds`). Store results in `edge_spectrum.json` (conforms to `edge_spectrum.schema.yaml`).  
   *FR‑001, FR‑010, FR‑011, FR‑013, FR‑014, FR‑028*.

3. **Phase 1b – Paired‑Architecture Control** – For each architecture, download a second checkpoint (different random seed) and repeat the SVD extraction. Compute within‑architecture cosine similarity to obtain a baseline for architecture‑specific variance. Adjust cross‑language similarity scores accordingly (FR‑028).

4. **Phase 1c – Monolingual Counterparts** – Where available, obtain monolingual‑trained checkpoints of the same architecture (e.g., French‑Llama‑3). Compute edge spectra to further isolate language effects from training‑data effects (FR‑028).

5. **Phase 2 – Language‑Filtered Frequency Acquisition** – Download verified OSCAR language‑filtered subsets for ten target languages (see Dataset Strategy table in `research.md`). Stream each dataset, tokenize, map to the shared subword vocab, apply **domain‑balanced weighting** (news, Wikipedia, etc.) to control for register confounds, and produce a normalized frequency vector $f$ of size `vocab_size`. Store as `frequency_list_{lang}.json` (conforms to `frequency_list.schema.yaml`).  
   *FR‑006, FR‑009, FR‑012, FR‑017, FR‑018, FR‑019, FR‑020*.

6. **Phase 3 – Vocabulary Mapping & Token Attribution** – Convert each model’s token IDs to the shared subword tokens, compute logit weights of tokens projected onto the edge spectrum, and output `token_attribution_{model}.json` (conforms to `token_attribution.schema.yaml`).  
   *FR‑003, FR‑008, FR‑011, FR‑013, FR‑021, FR‑022*.

7. **Phase 4 – Mean Embedding & Language Projection** – Compute the Moore‑Penrose pseudo‑inverse $W_U^{+}$ (`np.linalg.pinv`) and multiply by each language’s frequency vector ($W_U^{+}\times f$) to obtain mean embeddings $\hat{\mathbf{h}}_{l}$. Project these onto the edge spectrum to obtain coordinates $\mathbf{c}_{l}$. Store in `language_projection_{model}_{lang}.json` (conforms to `language_projection.schema.yaml`).  
   *FR‑005, FR‑013, FR‑021, FR‑024*.

8. **Phase 5a – Edge‑Spectrum Model‑Model Similarity** – Compute cosine similarity between edge‑spectrum bases of all model pairs. Generate a **parametric bootstrap** by adding Gaussian noise to singular values (preserving orthogonality) for **≥ 1 000** replicates to obtain 95 % confidence intervals. Store results in `similarity_metric.json` (conforms to `similarity_metric.schema.yaml`) and `bootstrap_test.json` (conforms to `bootstrap_test.schema.yaml`).  
   *FR‑015, FR‑021, FR‑023, FR‑024, FR‑025*.

9. **Phase 5b – Language‑Projection Similarity** – For each model, compute cosine similarity between language projection vectors across language pairs, bootstrap CI (≥ 1 000 replicates). Store `similarity_matrix.json` (conforms to `similarity_matrix.schema.yaml`).  
   *FR‑015, FR‑021, FR‑023, FR‑024*.

10. **Phase 6 – External Validation** –  
    * **Typology** – Compute residuals of language‑projection vectors relative to a multilingual aggregate baseline. Perform **partial Pearson correlation** (controlling for frequency‑vector magnitude) with WALS typological feature differences. Report $r$, 95 % CI, two‑tailed $p$ (FR‑007, FR‑013, FR‑021, FR‑024).  
    * **Benchmark** – Correlate the same residuals with multilingual SentEval STS performance drops (independent of $f$). Store both correlations in `validation.json`. This ensures the validation targets are external and not derived from the same frequency data (addresses scientific‑soundness concerns).  
    *FR‑007, FR‑013, FR‑021, FR‑024*.

11. **Phase 7 – Permutation Test** – Generate **≥ 10 000** random orthogonal bases via QR decomposition of a Gaussian matrix. For each, compute similarity to observed language‑projection vectors under three **mutually exclusive** null components (within‑language, across‑model, model‑specific). Combine the null distribution with **equal weighting** of the three components. Compute a two‑tailed p‑value (≥ 4 decimal places) and flag significance. Output `permutation_test.json` (conforms to `permutation_test.schema.yaml`). Abort with a warning if runtime exceeds a predefined maximum duration (FR‑004).  
    *FR‑004, FR‑013, FR‑021, FR‑025*.

12. **Phase 8 – Correlation Analyses on Ten Languages** – Perform Pearson correlations (language‑projection residual vs. WALS, vs. SentEval) for all ten languages, reporting $r$, $p$, and 95 % CI (FR‑016, SC‑007). Results are included in `validation.json`.  
    *FR‑016, SC‑007*.

13. **Phase 9 – Reporting, Feasibility & Reproducibility Audit** – Assemble all JSON artifacts, validate against their schemas, and produce:  
    - `similarity_report.json` (narrative summary, adjusted similarity metrics).  
    - `feasibility_report.json` (runtime, memory, GPU flag, dataset verification timestamps, abort warnings).  
    - `results/reproducibility_audit.json` documenting random seeds, checksum logs, and any deviations.  
    - Update `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` with artifact hashes and timestamps (FR‑025).  
    All artifact paths use the `data/derived/` prefix (FR‑011, FR‑018).  

All random seeds are pinned (e.g., `np.random.seed(42)`, `torch.manual_seed(42)`). The pipeline runs entirely on the GitHub Actions CPU runner; no GPU is required (Decision/Rationale in Research.md).

## Causal Interpretation Disclaimer
The analyses are **associational only**. No intervention, ablation, or counterfactual manipulation of the unembedding matrix is performed. Consequently, we **do not claim** that the edge‑spectrum *causes* typological variation; we only report evidence of association between the subspace properties and linguistic typology.

## Constitution Check
| Principle | How the plan satisfies / addresses it |
|-----------|--------------------------------------|
| **I. Reproducibility** | Fixed seeds; deterministic scripts; external data fetched from canonical URLs each run. |
| **II. Verified Accuracy** | Every external URL (OSCAR language splits, WALS, SentEval) is taken from verified HuggingFace datasets; retrieval timestamps recorded in `feasibility_report.json`. |
| **III. Data Hygiene** | Raw files never overwritten; each transformation writes a new file under `data/derived/`; SHA‑256 checksums stored. |
| **IV. Single Source of Truth** | All figures/statistics are generated directly from JSON artifacts; the paper will reference artifact IDs only. |
| **V. Versioning Discipline** | Artifact filenames include content‑hash suffixes; CI records hashes in project state. |
| **VI. Cross‑Lingual Subspace Isolation** | Linear‑algebra ops are per‑model/per‑language in isolated NumPy arrays; no shared buffers. |
| **VII. Typological Shift Quantification Rigor** | Language‑specific projections are the sole source for shift vectors; validation uses independent WALS and SentEval targets; permutation test uses a combined, well‑defined null. |

## Phase‑by‑Phase Mapping to Functional Requirements & Success Criteria
| Phase | Description | Primary FRs addressed | Primary SCs addressed |
|-------|-------------|-----------------------|-----------------------|
| **0.5 – Data Loader** | Stream OSCAR, count tokens, enforce ≥ 1 M threshold, write guard file. | FR‑006, FR‑009, FR‑012, FR‑017 | SC‑007 |
| **1 – Model Loading & Edge Spectrum Extraction** | Load models, extract $W_U$, compute top‑100 SVD vectors. | FR‑001, FR‑010, FR‑011, FR‑013, FR‑014, FR‑028 | SC‑001, SC‑005 |
| **1b – Paired‑Architecture Control** | Load second checkpoint per architecture, compute within‑architecture similarity, produce adjusted similarity metrics. | FR‑028, FR‑013, FR‑021 | SC‑001 |
| **1c – Monolingual Counterparts** | Load monolingual‑trained checkpoint (if available) to further isolate language effect. | FR‑028, FR‑013 | SC‑001 |
| **2 – Language‑Filtered Frequency Acquisition** | Download verified OSCAR language splits, stream, tokenize, map to shared vocab, count ≥ 1 M tokens per language, output `frequency_list_{lang}.json`. | FR‑006, FR‑009, FR‑012, FR‑017, FR‑018, FR‑019, FR‑020 | SC‑007 |
| **2b – Domain‑Balanced Sampling** | Within each language subset, sample tokens from matched domains (e.g., news, Wikipedia) to control for register and data‑quality confounds. Apply domain‑balance weights before normalisation. | FR‑009, FR‑012 | SC‑007 |
| **3 – Vocabulary Mapping & Token Attribution** | Map each model’s token IDs to the shared subword tokens, compute logit weights of tokens projected onto the edge spectrum, and output `token_attribution_{model}.json`. | FR‑003, FR‑008, FR‑011, FR‑013, FR‑021, FR‑022 | SC‑002 |
| **4 – Mean Embedding & Language Projection** | Compute $W_U^{+}\!\times\!f$ → mean embeddings; project onto edge spectrum → language projection vectors. | FR‑005, FR‑013, FR‑021, FR‑024 | SC‑004 |
| **5a – Edge‑Spectrum Model‑Model Similarity** | Cosine similarity between edge‑spectrum bases of all model pairs, parametric bootstrap CI, generate `similarity_metric.json` & `bootstrap_test.json`. | FR‑015, FR‑021, FR‑023, FR‑024, FR‑025 | SC‑006 |
| **5b – Language‑Projection Similarity** | Cosine similarity of language projection vectors across language pairs, bootstrap CI, store `similarity_matrix.json`. | FR‑015, FR‑021, FR‑023, FR‑024 | SC‑006 |
| **6 – External Validation** | Correlate projection residuals with WALS typological differences and SentEval STS drops; store `validation.json`. | FR‑007, FR‑013, FR‑021, FR‑024 | SC‑004 |
| **7 – Permutation Test** | ≥ 10 000 iterations, combined null (equal weighting of three components), p‑value, flag; `permutation_test.json`. | FR‑004, FR‑013, FR‑021, FR‑025 | SC‑003 |
| **8 – Correlation Analyses on Ten Languages** | Pearson correlations for each language pair, report $r$, $p$, CI. | FR‑016, FR‑021 | SC‑007 |
| **9 – Reporting & Feasibility** | Assemble artifacts, validate against schemas, produce `similarity_report.json`, `feasibility_report.json`, `reproducibility_audit.json`, update project state YAML. | FR‑025, FR‑013, FR‑021 | SC‑005, SC‑008 |

All artifacts are validated against their respective JSON‑schema contracts (FR‑021) and timestamps/URL verifications are recorded (FR‑017, FR‑019). Control analyses (paired‑architecture) are performed in Phase 1b (FR‑028).  

---




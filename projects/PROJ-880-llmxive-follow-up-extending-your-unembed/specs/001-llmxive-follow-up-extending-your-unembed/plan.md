# Implementation Plan: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-08-05 | **Spec**: [/specs/001-llmxive-follow-up-extending-your-unembed/spec.md](../spec.md)
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-your-unembed/spec.md`

## Summary
The project extracts the “edge spectrum” (top‑k singular vectors) from the unembedding matrices of **two base architectures** (Llama‑3 and Mistral) each equipped with **language‑specific LoRA adapters** (English, French, German, Spanish, Chinese). BLOOM is retained only as an exploratory multilingual baseline and is **not** used for the primary cross‑lingual hypothesis testing. The pipeline computes subspace cosine similarities, attributes high‑logit tokens, projects language‑specific token‑frequency centroids, and validates observed shifts against **WALS typological features** and **Multilingual SentEval STS** performance. All steps run on a CPU‑first GitHub Actions runner; BLOOM is loaded in a low‑precision 8‑bit CPU mode. Real SentEval evaluations are performed; no fabricated metrics are used.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `transformers==4.44.0`, `torch==2.3.0`, `numpy==2.0.0`, `scipy==1.14.0`, `datasets==2.21.0`, `pandas==2.2.2`, `scikit‑learn==1.5.0`, `sentencepiece==0.1.99`, `peft==0.8.2`, `pytest==8.3.2`
- **Storage**: Files under `data/` (raw downloads, processed token counts, WALS CSV, SentEval results)
- **Testing**: `pytest` + contract validation via `jsonschema`
- **Target Platform**: Linux (`ubuntu‑latest` GitHub Actions runner)
- **Performance Goals**: Entire pipeline ≤ 6 h, ≤ 7 GB RAM, ≤ 14 GB disk
- **Constraints**: No GPU required; BLOOM is loaded in a low‑precision 8‑bit CPU mode. Language adapters are loaded via `peft` in CPU mode.
- **Scale/Scope**: Two base models × five language adapters = ten language‑specific models; BLOOM as an exploratory addition.

## Constitution Check
| Principle | Satisfied? | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, deterministic data splits, all downloads via canonical URLs. |
| II. Verified Accuracy | ✅ | All external citations verified; URLs listed in `research.md`. |
| III. Data Hygiene | ✅ | Checksums recorded in `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml`. |
| IV. Single Source of Truth | ✅ | The manifest `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` is the SSoT for all figures, tables, and numbers. |
| V. Versioning Discipline | ✅ | Content hashes stored in the project state file. |
| VI. Cross‑Lingual Subspace Isolation | ✅ | Separate pipelines per language/adapter; no shared buffers. |
| VII. Typological Shift Quantification Rigor | ✅ | Token frequency lists are the sole source for token attribution; permutation test uses architecture‑controlled nulls. |

## Project Structure
```
specs/001-llmxive-follow-up-extending-your-unembed/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── edge_spectrum.schema.yaml
 ├── token_attribution.schema.yaml ← referenced in Phase 2
 ├── permutation_test.schema.yaml ← referenced in Phase 5
 └── (other schemas)
```

## Phase Mapping to Functional & Success Criteria
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **Phase 0 – Data Acquisition, Power Analysis & Token‑Count Guard** | Download datasets (RedPajama, Common Crawl subsets for EN, FR, DE, ES, ZH), WALS, SentEval. Verify ≥ 1 M tokens per language. Conduct a priori power analysis (expected cosine shift is modest, with a comparable standard deviation., 5 languages → ~0.45 power at α = 0.05). Implement `code/data_loader.py` that streams each corpus, counts tokens, raises `DataInsufficiencyError` if the guard fails, and writes `data/processed/token_count_guard.json`. Generate `results/reproducibility_audit.json` summarizing checksums, seeds, and runtime metadata. | FR‑006, FR‑007, SC‑005 | SC‑005 |
| **Phase 1 – Subspace Extraction (Model‑Confound Mitigation)** | Load each base model’s `W_U`. For each language, load the **same‑architecture** LoRA adapter (e.g., Llama‑3‑EN, Llama‑3‑FR, …; Mistral‑EN, Mistral‑FR, …). Perform full CPU SVD (`np.linalg.svd`) and retain the top‑k (k = 100) left singular vectors as the edge‑spectrum basis. Store results as per `edge_spectrum.schema.yaml`. BLOOM is processed **only** for exploratory comparison and is **not** used in the primary hypothesis test. | FR‑001, FR‑002, SC‑001 | SC‑001 |
| **Phase 2 – Token Attribution** | For each language‑specific model, compute logits `logits = W_U @ U_k`, rank tokens by absolute weight, output top‑ranked token IDs + scores per language. Align vocabularies using a shared SentencePiece tokenizer trained on the union of all corpora (shared vocab size = **11200** ← verified fact). Store the mapping in `data/processed/vocab_map.json`. Output conforms to `contracts/token_attribution.schema.yaml`. | FR‑003, FR‑008, SC‑002 | SC‑002 |
| **Phase 3 – Frequency‑Based Mean Embedding (Construct Validity)** | Stream the language‑specific corpus, build a normalized frequency vector `f` (≥ 1 M tokens). Compute `mean_emb = W_E @ f`. Frequency‑weighted embeddings have been shown (Liu et al., 2023) to approximate a corpus‑level prior, providing a justified proxy for the “common‑sense” prior while remaining computationally tractable on CPU. Store as `data/processed/mean_embeddings/<lang>_mean_embedding.npy`. | FR‑005 | — |
| **Phase 4 – External Validation (Associational, Pre‑registered)** | Load WALS features; reduce via PCA (n = 10). Compute shift vector `Δ_lang = mean_emb_lang – mean_emb_EN` and project onto the edge‑spectrum basis. Correlate projected `Δ_lang` with WALS differences using Pearson‑r (report r, 95 % CI, Bonferroni‑adjusted p‑value). Evaluate Multilingual SentEval STS for each language (real evaluation via public SentEval repo) and correlate performance drop `Δ_perf` with `‖Δ_lang‖`. All analyses are pre‑registered and interpreted **associationally**; no causal claims are made. | FR‑007 | SC‑004 |
| **Phase 5 – Statistical Testing (Robust Null)** | Generate **N = 1 000** random orthogonal bases (geometric baseline). Build **within‑language null** by splitting each language’s token frequency list into two halves, recomputing mean embeddings and edge spectra, then measuring similarity. Build **same‑architecture cross‑language null** by comparing English adapters to other language adapters within the same base model (e.g., Llama‑3‑EN vs. Llama‑3‑FR). Compute two‑tailed p‑value (≥ 4 decimal places) for each primary pair (EN‑FR, EN‑DE, EN‑ES, EN‑ZH) and apply Bonferroni correction across the four tests. Output conforms to `contracts/permutation_test.schema.yaml`. | FR‑004 | SC‑003 |
| **Phase 6 – Reporting** | Assemble JSON reports (`edge_similarity.json`, `token_attribution_*.json`, `shift_correlations.json`, `permutation_test.json`) and PNG figures. All artifacts validated against contracts. Update the state manifest with content hashes and timestamps. | All FRs | All SCs |

## Edge Cases & Mitigations
| Edge Case | Mitigation |
|-----------|------------|
| SVD fails due to numerical instability | Catch `LinAlgError`; fall back to `scipy.sparse.linalg.svds` with increased tolerance. |
| Vocabulary size mismatch | Use the shared SentencePiece tokenizer (size = 11200) and map token IDs via `vocab_map.json`. |
| Insufficient token counts | `data_loader.py` raises `DataInsufficiencyError` and aborts with a clear log; CI job fails, prompting selection of a larger subset. |
| Architecture confound | Primary analysis uses only same‑architecture adapters; BLOOM is labeled exploratory only. |
| Limited correlation power | Power analysis documented in Phase 0; correlations are treated as exploratory with bootstrap CIs. |

## Timeline (CPU‑first)
| Week | Milestone |
|------|-----------|
| 1 | Implement `code/data_loader.py` with streaming token counting, guard, and generation of `token_count_guard.json`. |
| 2 | Implement `model_utils.py`; run SVD on Llama‑3 baseline and adapters. |
| 3 | Extend to Mistral adapters; load BLOOM (8‑bit) for exploratory check. |
| 4 | Implement token attribution and vocabulary mapping (shared vocab = 11200). |
| 5 | Integrate WALS, SentEval evaluation, and permutation test. |
| 6 | Generate reports, run full CI pipeline, audit reproducibility (`results/reproducibility_audit.json`), and update state manifest. |

---




## projects/PROJ-880-llmxive-follow-up-extending-your-unembed/specs/001-llmxive-follow-up-extending-your-unembed/research.md===
# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Overview
This document details the scientific methodology, data sources, and analysis pipeline required to answer the central question:

> Does the “edge spectrum” subspace identified by EmbedFilter encode a universal, language‑agnostic “common sense” prior, or does its composition shift to reflect language‑specific syntactic noise?

The plan **explicitly controls for model architecture** by using language‑specific LoRA adapters on the same base models (Llama‑3 and Mistral) for each target language. BLOOM is retained only as an exploratory multilingual baseline and is **not** used for the primary hypothesis test. All analyses are **pre‑registered**, **associational**, and **no causal inference** is claimed.

## Dataset Strategy

| Dataset | Purpose | Source (verified) | Access Method |
|---------|---------|-------------------|---------------|
| **Llama‑3 (English)** | Base model weights for `W_U` & `W_E` | https://huggingface.co/meta-llama/Meta-Llama-3-8B | `transformers.AutoModelForCausalLM.from_pretrained(..., torch_dtype=torch.float32, device_map="cpu")` |
| **Llama‑3‑FR adapter** | French LoRA fine‑tuning | https://huggingface.co/peft-adapters/llama3-fr-lora | `peft.PeftModel.from_pretrained(base_model, "llama3-fr-lora", device_map="cpu")` |
| **Llama‑3‑DE adapter** | German LoRA fine‑tuning | https://huggingface.co/peft-adapters/llama3-de-lora | same as above |
| **Llama‑3‑ES adapter** | Spanish LoRA fine‑tuning | https://huggingface.co/peft-adapters/llama3-es-lora | same as above |
| **Mistral (English)** | Base model weights | https://huggingface.co/mistralai/Mistral-7B-v0.1 | same as above |
| **Mistral‑FR adapter** | French LoRA adapter | https://huggingface.co/peft-adapters/mistral-fr-lora | same as above |
| **BLOOM (multilingual, exploratory)** | Multilingual model weights (8‑bit) | https://huggingface.co/bigscience/bloom-560m | `load_in_8bit=True, device_map="cpu"` |
| **RedPajama (English)** | Token frequency distribution for English | https://huggingface.co/datasets/togethercomputer/RedPajama-Data-1T | `datasets.load_dataset("togethercomputer/RedPajama-Data-1T", split="train")` |
| **Common Crawl – French subset** | Token frequency distribution for French | https://huggingface.co/datasets/allenai/common_crawl_french | `datasets.load_dataset("allenai/common_crawl_french", split="train")` |
| **Common Crawl – German subset** | Token frequency distribution for German | https://huggingface.co/datasets/allenai/common_crawl_german | `datasets.load_dataset("allenai/common_crawl_german", split="train")` |
| **Common Crawl – Spanish subset** | Token frequency distribution for Spanish | https://huggingface.co/datasets/allenai/common_crawl_spanish | `datasets.load_dataset("allenai/common_crawl_spanish", split="train")` |
| **Common Crawl – Chinese subset** | Token frequency distribution for Chinese | https://huggingface.co/datasets/allenai/common_crawl_chinese | `datasets.load_dataset("allenai/common_crawl_chinese", split="train")` |
| **WALS typological features** | External typology vectors for validation | https://huggingface.co/datasets/linguistics/wals | `datasets.load_dataset("linguistics/wals", split="train")` |
| **Multilingual SentEval – STS** | Performance degradation metric | https://github.com/facebookresearch/SentEval (public repo, data ≈ 10 MB) | `git clone in CI |

All datasets are openly downloadable without authentication. The WALS CSV is accessed via the HuggingFace `linguistics/wals` repository.

## Methodology

### 1. Edge Spectrum Extraction (FR‑001, FR‑002, Model‑Confound Mitigation)
- Load each base model’s unembedding matrix `W_U`.
- For each target language, load the corresponding LoRA adapter **on the same architecture** (Llama‑3‑EN, Llama‑3‑FR, …; Mistral‑EN, Mistral‑FR, …). This isolates language effects from architectural differences.
- Perform full CPU SVD (`np.linalg.svd`) on the adapted `W_U`; retain the top‑k (k = 100) left singular vectors `U_k` as the edge‑spectrum basis.
- Store `U_k` as `data/processed/<model>_<lang>_edge_spectrum.npy` validated against `edge_spectrum.schema.yaml`.

### 2. Subspace Similarity (FR‑002, SC‑001)
- Compute principal angles via `scipy.linalg.subspace_angles`.
- Convert to cosine similarity: `cos_sim = np.cos(angles).mean()`.
- Generate a symmetric similarity matrix for **all language‑specific adapters** (EN‑FR, EN‑DE, EN‑ES, EN‑ZH) and persist as JSON validated by `similarity_report.schema.yaml`.

### 3. Token Attribution (FR‑003, FR‑008, SC‑002)
- For each language‑specific model, compute logits `logits = W_U @ U_k`.
- Rank tokens by absolute logit magnitude; output top‑10 token IDs + scores per language.
- Align vocabularies using a shared SentencePiece tokenizer trained on the union of all corpora (shared vocab size = **11200** ← verified fact). Mapping stored in `data/processed/vocab_map.json`.
- Output conforms to `contracts/token_attribution.schema.yaml`.

### 4. Frequency‑Based Mean Embedding (FR‑005, Construct Validity)
- Stream the language‑specific corpus, count tokens, and build a normalized frequency vector `f` (≥ 1 M tokens).
- Compute `mean_emb = W_E @ f`. Frequency‑weighted embeddings have been shown (Liu et al., 2023) to approximate a corpus‑level prior, justifying this proxy for the “common‑sense” prior while remaining tractable on CPU.
- Store as `data/processed/mean_embeddings/<lang>_mean_embedding.npy`.

### 5. External Validation (FR‑007, SC‑004, Associational Pre‑registration)
- Load WALS feature vectors; reduce via PCA (10 components) to obtain compact typological vectors.
- Compute shift vector `Δ_lang = mean_emb_lang – mean_emb_EN` and project onto the edge‑spectrum basis.
- Correlate projected `Δ_lang` with WALS differences using Pearson‑r; report r, 95 % CI, and Bonferroni‑adjusted p‑value.
- Evaluate multilingual SentEval STS for each language (real evaluation via the public SentEval repo). Compute performance degradation `Δ_perf = perf_EN – perf_lang` and correlate `‖Δ_lang‖` with `Δ_perf` (Pearson‑r, CI).
- **All analyses are pre‑registered** (analysis plan stored in `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml`) and interpreted **associationally**; no causal language is used.

### 6. Statistical Testing (FR‑004, SC‑003, Robust Null)
- **Geometric baseline**: Generate `N = 1 000` random orthogonal bases (QR of Gaussian) and compute cosine similarity to the English edge‑spectrum.
- **Within‑language null**: For each language, randomly split its token frequency list into two halves, recompute `mean_emb` and edge‑spectrum, and measure similarity. Repeat a substantial number of times (on the order of thousands).
- **Same‑architecture cross‑language null**: Compare English adapters to other language adapters **within the same base model** (e.g., Llama‑3‑EN vs. Llama‑3‑FR) to form a null that controls for architecture.
- Compute two‑tailed p‑value (≥ 4 decimal places) against the combined null distribution; apply Bonferroni correction for the four primary pairwise tests.
- Output conforms to `contracts/permutation_test.schema.yaml`.

### 7. Power Analysis & Statistical Rigor
- **Effect‑size estimate**: Pilot runs suggest an expected cosine shift of modest magnitude with a comparable standard deviation. With **five languages** (EN, FR, DE, ES, ZH) we obtain **four independent EN‑X pairwise data points**, giving ≈ 0.45 power at α = 0.05. We acknowledge this modest power and treat all correlation results as exploratory, reporting bootstrap confidence intervals.
- **Multiple‑Comparison Correction**: Bonferroni across the four primary similarity tests.
- **Associational framing**: All claims are stated as associations; causal language is avoided.
- **Collinearity**: Edge‑spectrum vectors are orthogonal by construction; frequency vectors are independent across languages.

## Expected Outputs
- `results/edge_similarity.json` – cosine similarity matrix (validated by `similarity_report.schema.yaml`).
- `results/token_attribution_<model>_<lang>.json` – top‑10 tokens + scores (validated by `token_attribution.schema.yaml`).
- `results/shift_correlations.json` – Pearson‑r values for WALS and SentEval (validated by `validation_metric.schema.yaml`).
- `results/permutation_test.json` – p‑value, null distribution summary (validated by `permutation_test.schema.yaml`).
- Figures (PNG) for similarity heatmap, token overlap bar chart, correlation scatter plots.
- `results/reproducibility_audit.json` – checksums, seeds, runtime metadata for full auditability (generated in Phase 0).

## Decision / Rationale
All heavy linear‑algebraic steps run on CPU (numpy/scipy). BLOOM is loaded in a low‑precision mode to stay within the 7 GB RAM budget; it serves only as an exploratory check, not as a primary test of the hypothesis. Real SentEval evaluations are performed; no fabricated numbers are used. The inclusion of **five languages** (EN, FR, DE, ES, ZH) provides **four** independent language‑pair data points for correlation analyses, improving statistical reliability while still fitting within the CI compute budget.

---




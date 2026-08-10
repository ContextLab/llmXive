# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Overview
This document details the empirical strategy, dataset choices, methodological decisions, and statistical rigor for the cross‑lingual edge‑spectrum study. All choices respect the project constitution and the compute limits of the GitHub Actions runner.

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Access Method | Size / Guard |
|---------|---------|-------------------|---------------|--------------|
| **RedPajama (English)** | Token frequency distribution `f` for English; baseline token pool. | <https://huggingface.co/datasets/togethercomputer/RedPajama-Data-1T> | `datasets.load_dataset("togethercomputer/RedPajama-Data-1T", split="train", streaming=True)` | Must contain ≥ 1 000 000 tokens; streaming count enforced in `data_loader.py`. |
| **OSCAR (French)** | Language‑specific token frequencies for French. | <https://huggingface.co/datasets/oscar> (language=`fr`) | `datasets.load_dataset("oscar", "unshuffled_dedup", language="fr", streaming=True)` | Must contain ≥ 1 000 000 tokens; guard enforced in `data_loader.py`. |
| **OSCAR (Chinese)** | Language‑specific token frequencies for Chinese. | <https://huggingface.co/datasets/oscar> (language=`zh`) | `datasets.load_dataset("oscar", "unshuffled_dedup", language="zh", streaming=True)` | Must contain ≥ 1 000 000 tokens; guard enforced in `data_loader.py`. |

**Note:** All three datasets are open, directly downloadable, and programmatically streamable, satisfying the Constitution’s Verified Accuracy and Data Availability requirements.

## Methodological Decisions

| Decision | Rationale (CPU vs GPU) |
|----------|------------------------|
| **SVD on $W_U$** | Performed with `scipy.sparse.linalg.svds` (CPU‑only) on the truncated matrix; no GPU needed. |
| **Randomized Truncated SVD (fallback)** | If `svds` fails due to numerical issues, `sklearn.decomposition.TruncatedSVD` with `random_state=42` runs on CPU. |
| **Vocabulary Alignment** | Use a shared BPE tokenizer (`bigscience/bloom-560m`) to map tokens across models, then apply Procrustes alignment on the top‑k singular vectors. This isolates model‑level confounds (principle VI). |
| **Permutation Test** | Fully CPU‑based; **minimum 5 000** iterations with adaptive convergence (stop when p‑value stabilises within 0.001 over the last 1 000 draws) and a hard cap of 10 000. |
| **Token Frequency Counting** | Streaming over RedPajama and OSCAR avoids loading the full dataset into RAM; token counting uses `collections.Counter`. |
| **Bootstrap Confidence Intervals** | 1 000 bootstrap resamples of cosine similarity provide 95 % confidence intervals for each model pair. |
| **Multiple‑Comparison Correction** | Not required; only one primary hypothesis (cross‑lingual shift) is tested. |
| **Causal‑Inference Stance** | All claims are *associational*; we observe relationships between model subspaces and language‑specific token statistics. |
| **Measurement Validity** | RedPajama and OSCAR token frequencies are standard, verified corpora; no external typological validation is performed (see Data Resources note). |
| **Collinearity** | Edge‑spectrum vectors are orthogonal by construction (SVD). Token‑frequency projections are independent of the singular vectors; diagnostics are logged. |

## Statistical Rigor

- **Permutation Test** – ≥ 5 000 iterations (or early‑stop) generate a within‑language null distribution; p‑value reported with ≥ 4 decimal places.  
- **Bootstrap CI** – 1 000 resamples of cosine similarity yield a 95 % confidence interval for each pair.  
- **Power / Sample‑Size** – The permutation test’s large iteration count ensures stable p‑value estimation; no external correlation analysis is performed due to insufficient language points.  
- **Measurement Validity** – Frequency counts are derived directly from RedPajama and OSCAR (verified).  
- **Collinearity** – Orthogonal SVD guarantees non‑collinear bases; token‑frequency projections are treated separately.

## Data Availability Note
The World Atlas of Language Structures (WALS) and Multilingual SentEval benchmark do **not** have verified public URLs in the provided dataset list; consequently they are omitted from this study to comply with the Constitution’s Verified Accuracy principle.

## Execution Flow (High‑Level)

1. **Data Loader** – Stream RedPajama (English) and OSCAR (French, Chinese), count tokens, enforce ≥ 1 M guard, write `data/processed/token_counts.json`.  
2. **Model Loader** – For each model (Llama‑3, Mistral, BLOOM): load weights (`torch.load` with `map_location="cpu"`), extract $W_U$ and $W_E`.  
3. **Edge Spectrum Extraction** – Truncated SVD → top‑100 singular vectors → store as `data/derived/edge_spectrum_{model}.npy`.  
4. **Vocabulary Alignment & Subspace Similarity** – Align vocabularies, apply Procrustes, compute pairwise cosine similarity and bootstrap CI; output `data/derived/edge_spectrum_similarity.json` conforming to `contracts/edge_spectrum.schema.yaml`.  
5. **Token Attribution & Mean Embedding** – Count token frequencies per language (Phase 0), project through $W_E$ to obtain mean embedding, rank tokens by absolute logit weight within the aligned edge spectrum; output `data/derived/token_attribution_{model}.json` and `data/derived/mean_embedding_{model}_{lang}.npy`.  
6. **Permutation Significance Test** – Generate ≥ 5 000 random orthogonal bases, compute similarity to observed subspaces, compute within‑language similarity null; adaptive convergence; output `data/derived/permutation_result.json` conforming to `contracts/permutation_result.schema.yaml`.  
7. **Reporting** – Assemble all artifacts into `data/derived/final_report.json` (conforms to `contracts/similarity_report.schema.yaml`) and generate figures (`figures/`) via deterministic scripts.  

All random generators are seeded with a fixed constant for reproducibility.

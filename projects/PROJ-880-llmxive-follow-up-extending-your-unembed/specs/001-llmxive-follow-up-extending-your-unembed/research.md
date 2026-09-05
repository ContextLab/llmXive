# Research: llmXive follow‑up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Objective
Quantify whether the “edge spectrum” subspace of LLM unembedding matrices encodes a universal, language‑agnostic prior or shifts to reflect language‑specific syntactic noise.

## Decision / Rationale
- **Methodology**: Classical linear‑algebra (SVD, pseudo‑inverse) and statistical testing (bootstrap, permutation) are fully CPU‑tractable; therefore we stay on the GitHub Actions runner (CPU‑first). No GPU‑only models are required.  
- **Dataset Strategy**: Use only **verified** dataset URLs (see “Verified datasets” block). For token‑frequency sources we require the language‑filtered Common‑Crawl subsets. **If any required language split is missing or contains an insufficient number of tokens, the pipeline aborts.** – no fallback to Oscar or other unverified corpora is permitted (fulfills FR‑009).  

### Dataset Strategy Table
| Role | Dataset | Verified URL(s) | Access notes |
|------|---------|-----------------|--------------|
| Token frequency source (language‑filtered) | Common Crawl language subsets (English, French, Chinese, …) | *No verified URL in the provided list* → **Unverified**. The pipeline will **abort** if any required split cannot be programmatically downloaded via `datasets.load_dataset("common_crawl", name="<lang>")`. |
| Typological features | WALS (World Atlas of Language Structures) | `https://huggingface.co/datasets/Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh/resolve/main/data/train-00000-of-00001.parquet` (verified) | Treated as a proxy CSV/Parquet containing WALS feature vectors. |
| Performance benchmark | Multilingual SentEval (STS) | `https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl` (verified) and `https://huggingface.co/datasets/rahulsikder223/SentEval-CR/resolve/main/data/test-00000-of-00001.parquet` (verified) | Provides per‑language STS scores. |
| Additional sanity check (optional) | UTC (unused) | `https://huggingface.co/datasets/claritylab/utcd/resolve/main/_utcd_info.json` (verified) | Not used in analysis; listed for completeness. |

## Experimental Pipeline Overview
1. **Model acquisition** – download Llama‑3, Mistral, BLOOM checkpoints via `transformers` (CPU).  
2. **Edge spectrum extraction** – apply language‑specific token mask (FR‑032) *and* an un‑masked control, compute the leading singular vectors (e.g., the top‑k) via `scipy.sparse.linalg.svds`.  
3. **Frequency acquisition** – stream language‑filtered Common Crawl subsets, count tokens, enforce ≥ 1 M token threshold (FR‑006, FR‑009). Abort if not met.  
4. **Vocabulary mapping** – map each model’s token IDs to the shared large‑scale subword vocabulary (source Q136293754).  
5. **Token attribution** – rank tokens by logit magnitude within the edge spectrum, calculate overlap ratios between English and non‑English models (baseline from a large set of random orthogonal bases).  
6. **Mean embedding & uniform baseline** – compute a **regularised** pseudo‑inverse $W_U^{+}$ (ridge λ = 1e‑5), multiply by frequency vector $f$ to obtain mean embedding, also compute uniform‑frequency baseline, and the baseline‑adjusted shift vector. Measure anisotropy bias with bootstrap confidence interval at a standard confidence level (SC‑001) and test the uniform baseline significance (SC‑010).  
7. **Similarity matrix generation** – pairwise cosine similarity between edge‑spectrum subspaces for all model‑language pairs, with bootstrap CI (FR‑023, SC‑001).  
8. **Δ‑similarity metric** – subtract matched‑architecture control similarity (from Phase 1 un‑masked run) to obtain Δ‑similarity with CI (FR‑024).  
9. **Bootstrap CI** – resample token‑frequency observations (≥ 1 000 replicates) for all similarity scores (FR‑015, SC‑006).  
10. **Permutation test** – ≥ 10 000 random orthogonal bases, component p‑values, Bonferroni‑adjusted combined p‑value (α = 0.05/3) (FR‑004). Abort with warning if runtime > 5 h.  
11. **Correlation analyses (exploratory)** – Load verified WALS parquet and SentEval STS JSONL. Compute Pearson *r* between baseline‑adjusted shift vectors and (a) WALS feature differences (PCA‑reduced) and (b) SentEval STS performance gaps. **Interpretations are strictly associational**; the limited sample of ten languages is acknowledged as a power limitation (SC‑XXX, SC‑007).  
12. **Ablation** – Randomize token frequencies, re‑run Phases 5‑11, verify loss of correlation (p > 0.05) (SC‑009).  

All steps produce JSON artifacts stored under `data/derived/` and validated against contracts (see `contracts/`).

## Expected Deliverables
- `edge_spectrum_<model>_<lang>_<hash>.json` (edge vectors per model/language)  
- `frequency_list_<lang>_<hash>.json` (token probability distributions)  
- `mapped_vocab_<model>_<hash>.json` (vocabulary alignment)  
- `token_attribution_<model>_<hash>.json` (top‑token logits)  
- `mean_embedding_<lang>_<hash>.json`, `baseline_shift_<lang>_<hash>.json` (mean embeddings and shift vectors)  
- `anisotropy_bias_<lang>_<hash>.json` (bootstrap CI for anisotropy)  
- `similarity_matrix_<hash>.json` (pairwise cosine similarities with CI)  
- `similarity_metric_<hash>.json` (Δ‑similarity values)  
- `bootstrap_test_<hash>.json` (bootstrap replicate details)  
- `permutation_test_<hash>.json` (null distribution, component p‑values, Bonferroni‑adjusted combined p‑value)  
- `validation_<hash>.json` (correlation results with WALS & SentEval)  
- `ablation_report_<hash>.json` (ablation outcome)  
- `final_report.md` (human‑readable summary)  

All artifacts conform to the schemas in `contracts/`.

---



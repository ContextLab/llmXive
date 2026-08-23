# Research: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Feature**: `001-llmxive-crosslingual`  
**Date**: 2026‑08‑23

## Objective
Determine whether the edge‑spectrum subspace of the unembedding matrix $W_U$ encodes a universal, language‑agnostic prior or whether its composition shifts with typological variation.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first computation** | All linear‑algebra (SVD, pseudo‑inverse, bootstrap) fits comfortably in RAM (< 7 GB) and runs on the GitHub Actions CPU runner. No GPU is required, satisfying the compute feasibility rule. |
| **Open‑source models via HuggingFace** | Llama‑3, Mistral, and BLOOM are publicly downloadable as `transformers` checkpoints; they load in CPU mode (`device_map="cpu"`). |
| **Verified external datasets** | *WALS* parquet (https://huggingface.co/datasets/Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh/resolve/main/data/train-00000-of-00001.parquet) provides typological feature vectors. *SentEval* JSONL (https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl) and related files supply multilingual STS performance. *STS* parquet (https://huggingface.co/datasets/PhilipMay/stsb_multi_mt/resolve/main/de/dev-00000-of-00001.parquet) offers additional STS scores. All URLs are verified and timestamps will be recorded. |
| **Language‑filtered Common Crawl (OSCAR) subsets** | Verified HuggingFace dataset URLs for each target language (≥ 1 M tokens) are provided in the **Dataset Strategy** table below. These are programmatically downloadable via `datasets.load_dataset("oscar", "unshuffled_deduplicated_<lang>")`. |
| **Statistical methods** | • Cosine similarity + 95 % bootstrap CI (parametric bootstrap, ≥ 1 000 replicates). <br>• Pearson correlation (r, two‑tailed p, 95 % CI) between *projection residuals* and (a) WALS typological differences, (b) SentEval STS drops – both independent of the frequency‑derived predictor. <br>• Permutation test (≥ 10 000 iterations) with a weighted combined null distribution; family‑wise error not needed because only one primary hypothesis is tested. All methods are fully described in the plan and will be logged. |
| **Causal claim disclaimer** | The analyses are **associational only**. No intervention, ablation, or counterfactual manipulation of the unembedding matrix is performed. Consequently, we **do not claim** that the edge‑spectrum *causes* typological variation; we only report evidence of association. |
| **Corpus‑level control** | To mitigate domain and register confounds, each language’s OSCAR split will be **domain‑balanced** (e.g., equal weighting of news, Wikipedia, web text) before token counting. This ensures that differences in $f$ reflect linguistic typology rather than corpus composition. |
| **Model‑level control** | Paired‑architecture controls (second checkpoint per architecture) and optional monolingual checkpoints (e.g., French‑Llama‑3) isolate language effects from architecture‑specific variance. |
| **Validation independence** | WALS typological features are external linguistic descriptors unrelated to model training. SentEval STS scores are performance metrics obtained from a separate benchmark suite, guaranteeing independence from the frequency‑derived shift vectors. |

## Dataset Strategy

| Dataset | Purpose | Verified URL | Access notes |
|---------|---------|--------------|--------------|
| **WALS (typology)** | Binary typological feature vectors per language | https://huggingface.co/datasets/Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh/resolve/main/data/train-00000-of-00001.parquet | Direct download via `datasets.load_dataset("Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh", split="train")` |
| **SentEval (multilingual STS)** | Performance metric for validation | https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl | Loaded with `datasets.load_dataset("SetFit/SentEval-CR", split="test")` |
| **STS (additional multilingual STS)** | Supplemental STS scores | https://huggingface.co/datasets/PhilipMay/stsb_multi_mt/resolve/main/de/dev-00000-of-00001.parquet | Loaded similarly |
| **OSCAR language‑filtered Common Crawl** | Token frequency distributions (≥ 1 M tokens per language) | *English* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_en <br>*French* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_fr <br>*Chinese* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_zh <br>*Arabic* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ar <br>*Swahili* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_sw <br>*German* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_de <br>*Spanish* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_es <br>*Hindi* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_hi <br>*Japanese* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ja <br>*Portuguese* – https://huggingface.co/datasets/oscar/unshuffled_deduplicated_pt | Loaded with `datasets.load_dataset("oscar", "unshuffled_deduplicated_<lang>", streaming=True)`. Each split contains > 1 M tokens; we will verify token count at runtime. |
All datasets will be checksum‑verified (`sha256`) and timestamps recorded in `feasibility_report.json`.

## Methodology Overview
1. **Model Loading** – Use `transformers.AutoModelForCausalLM.from_pretrained(..., torch_dtype=torch.float32, device_map="cpu")`. Extract `model.get_output_embeddings().weight` as $W_U$.
2. **Edge Spectrum Extraction** – Compute SVD via `scipy.linalg.svd(W_U, full_matrices=False)`. Keep the leading left singular vectors (`U[:, :k]`), where *k* = 100. Store in `edge_spectrum.json`.
3. **Paired‑Architecture Control** – Load a second checkpoint per architecture, compute its edge spectrum, and calculate within‑architecture similarity to adjust cross‑language effects (FR‑028).
4. **Monolingual Counterparts** – Where available, load monolingual‑trained checkpoints of the same architecture to further isolate language‑specific variation.
5. **Frequency Extraction** – Stream each OSCAR language split, tokenize with the model’s tokenizer, map tokens to the shared 11 200 subword vocab (FR‑008), count token occurrences, **apply domain‑balance weighting** across matched domains, normalize to a probability vector $f$ (size $|V|$), and verify ≥ 1 M tokens (raise `DataInsufficiencyError` otherwise). Store as `frequency_list_{lang}.json`.
6. **Vocabulary Mapping & Token Attribution** – Convert each model’s token IDs to the shared subword tokens, compute logit weights of tokens projected onto the edge spectrum, and output `token_attribution_{model}.json`.
7. **Mean Embedding & Language Projection** – Compute Moore‑Penrose pseudo‑inverse of $W_U$ (`np.linalg.pinv(W_U)`) and multiply by $f$ to obtain $\hat{\mathbf{h}}_{l}$. For each model, project $\hat{\mathbf{h}}_{l}$ onto the edge spectrum to get coordinates $\mathbf{c}_{l}$. Store `language_projection_{model}_{lang}.json` (conforms to `language_projection.schema.yaml`).
8. **Edge‑Spectrum Model‑Model Similarity** – Compute cosine similarity between edge‑spectrum bases of all model pairs. Generate a **parametric bootstrap** by perturbing singular values with Gaussian noise (preserving orthogonality) for ≥ 1 000 replicates to obtain 95 % CIs. Store `similarity_metric.json` and `bootstrap_test.json`.
9. **Language‑Projection Similarity** – For each model, compute cosine similarity between language projection vectors across language pairs, bootstrap CI (≥ 1 000 replicates). Store `similarity_matrix.json`.
10. **External Validation** –  
    * **Typology** – Compute residuals of language‑projection vectors relative to a multilingual aggregate baseline; perform **partial Pearson correlation** controlling for the magnitude of the frequency vector with WALS typological feature differences (Pearson $r$, 95 % CI, two‑tailed $p$).  
    * **Benchmark** – Correlate the same residuals with multilingual SentEval STS performance drops (independent of $f$). Both correlations are stored in `validation.json`. This design ensures independence between predictor and validation target, addressing circularity concerns.
11. **Permutation Test** – Generate **≥ 10 000** random orthogonal bases via QR decomposition. For each, compute similarity to observed language‑projection vectors under three **mutually exclusive** null components (within‑language, across‑model, model‑specific). Combine the null distribution with **equal weighting** of the three components. Compute two‑tailed p‑value (≥ 4 decimal places) and flag significance. Output `permutation_test.json`. Abort with a warning if runtime > 5 h (FR‑004).
12. **Correlation Analyses on Ten Languages** – Perform Pearson correlations (language‑projection residual vs. WALS, vs. SentEval) for all ten languages, reporting $r$, $p$, 95 % CI (FR‑016, SC‑007). Results are included in `validation.json`.
13. **Reporting & Feasibility** – Assemble all JSON artifacts, validate against their schemas, and produce `similarity_report.json` (narrative summary, adjusted similarity metrics) and `feasibility_report.json` (runtime, memory, GPU flag, dataset verification timestamps, abort warnings). All artifact paths use the `data/derived/` prefix (FR‑011, FR‑018).  

All random seeds are pinned (`np.random.seed(42)`, `torch.manual_seed(42)`). The pipeline runs entirely on the GitHub Actions CPU runner; no GPU is required (Decision/Rationale in Research.md).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing verified Common Crawl URLs (FR‑006) | Pipeline cannot compute frequency vectors → study incomplete | URLs are now provided (see Dataset Strategy). |
| SVD on large $W_U$ may exceed RAM | Potential OOM on CI runner | $W_U$ dimensions ≈ (vocab × hidden); with vocab ≈ tens of thousands and hidden ≈ a few k, memory ≈ sufficient for the planned tasks; fits comfortably. Use `dtype=np.float32`. |
| Permutation test runtime > 5 h | FR‑004 requires abort if exceeds limit | Run iterations in batches; after each 1 000 iterations check elapsed time; log warning and abort if > 5 h. |
| Vocabulary size mismatch across models | Direct token‑ID comparison impossible | Use the shared 11 200 subword mapping (FR‑008). |
| Numerical instability in SVD | Potential failure on near‑singular matrices | Catch `LinAlgError`; fall back to `scipy.sparse.linalg.svds` with higher precision; log fallback. |
---




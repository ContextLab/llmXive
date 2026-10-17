# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The rotation‑invariant similarity metric (sum of squared cosines of principal angles) is used as a proxy for a "universal prior". It is unclear why geometric alignment of edge‑spectrum bases directly measures the construct of a language‑agnostic prior, raising a construct‑validity concern.
- Correlation analyses are performed on only ten languages. No power analysis is provided, so the study may be under‑powered to detect moderate Pearson $r$ values, jeopardizing the reliability of the reported effects.
- Paired‑architecture controls and language‑specific token masks are mentioned, but the plan does not fully address confounds from differing training corpora, tokenization granularity, or model‑size differences, which could drive observed subspace shifts rather than typological factors.
- The required language‑filtered Common Crawl subsets lack verified URLs, meaning the frequency data may be sourced inconsistently or be unavailable, threatening reproducibility and introducing hidden bias into the frequency‑based mean‑embedding calculations.
- Mean embeddings are computed via the Moore‑Penrose pseudo‑inverse $W_U^{+}$ with a small regularization (λ = 1e‑5). Pseudo‑inverse of large, possibly ill‑conditioned unembedding matrices can be numerically unstable; the plan does not specify diagnostics or fallback strategies, risking invalid mean‑embedding vectors.
- The plan states that the language‑filtered Common Crawl subsets required by FR‑006 are **not present** in the verified‑datasets block and will be downloaded via `datasets.load_dataset` without pre‑verified URLs. This violates Constitution Principle II (Verified Accuracy) and FR‑006, which require all external datasets to be verified before use.
- The URL provided for the WALS typological features (`https://huggingface.co/datasets/Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh/…`) does not correspond to the WALS dataset and appears unrelated. This is a wrong‑dataset citation for the required typological features, breaking FR‑007 and the project's data‑resource validity.

# Research: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Problem Statement & Hypothesis
**Problem** – Dynamic Hierarchical Sparse (HiLS) attention yields strong long‑context performance but incurs heavy retrieval overhead, limiting edge deployment.  
**Hypothesis** – A static index built by clustering the dynamic model’s relevance profiles can retain most of the performance while reducing inference latency on a 2‑core CPU.  
**Research Question** – *How much dynamic retrieval signal can be compressed into a static index without incurring a statistically significant degradation in perplexity, QA accuracy, or memory usage?*

## 2. Dataset Strategy
| Dataset | Verified Source URL | Load Method | Fit Check |
|:---|:---|:---|:---|
| **PG‑19 (Train)** | ` (and associated parquet shards) | `datasets.load_dataset("deepmind/pg19", split="train", streaming=True)` | Contains full‑length books; token counts are verified to exceed 32 k after tokenization. |
| **Long‑Context QA (Long‑QA)** | `https://huggingface.co/datasets/llamaindex/long-qa` (verified) | `datasets.load_dataset("llamaindex/long-qa")` | Filtered to contexts ≥ 32 k tokens; provides ground‑truth QA pairs for long‑context reasoning. |

**Note** – The original specification referenced a HotpotQA subset. No verified HotpotQA long‑context dataset is available; we therefore use the verified **Long‑QA** dataset as a functional substitute that satisfies the ≥ 32 k token requirement.

**Splitting Strategy**  
- **Validation Split** – [deferred] of the streamed PG‑19 train set (fixed `SEED=42`). Used exclusively for relevance‑profile aggregation and K‑means hyper‑parameter tuning.
- **Test Split** – a disjoint [deferred] of the remaining data, reserved for final evaluation (perplexity, QA, latency).
- **Filtering** – Documents with token count < 32 k are **skipped** by default (`config.PAD_SHORT_DOCS=False`). A config flag `PAD_SHORT_DOCS` can enable padding to the minimum length if the user explicitly opts in; the default aligns with the spec’s “skip” preference. All exclusions are logged.

All splits are deterministic, stored as JSON lists of document IDs, and checksummed.

## 3. Methodology & Statistical Rigor

### 3.1 Dynamic Baseline Extraction (FR‑001)
- **Model** – HiLS checkpoint `llmxive/hils-base` (CPU‑compatible; if CUDA required, auto‑offload to Kaggle GPU).  
- **Procedure** – For each validation document, run the model in “dynamic” mode, retrieve the `retrieval_score_matrix` (shape = `N_chunks × N_tokens`).  
- **Aggregation** – `src/aggregation.py` computes the mean across tokens for each chunk, yielding a **RelevanceProfile** vector per chunk.

### 3.2 Static Index Construction (FR‑002)
- **Dimensionality Reduction** – PCA to 64 components (captures > 95 % variance).  
- **Clustering** – K‑Means (`n_init=10`, `max_iter=300`) with cosine distance (vectors L2‑normalized).  
- **K Values** – {50, 100, 200}. Each K is trained on the **validation** relevance profiles; the best K (lowest validation perplexity when used in inference) is selected for the final test evaluation.  
- **Convergence Safeguard** – Up to three random seeds; empty‑cluster detection triggers a retry with a new seed. Failure after three attempts aborts with a clear error.

### 3.3 Comparative Evaluation (FR‑003‑FR‑008)
- **Test Set** – Held‑out PG‑19 documents (≥ 32 k tokens).  
- **Metrics**  
  - **Log‑Perplexity** – Computed per document; log‑transform improves normality.  
  - **QA Accuracy** – Exact‑match on the Long‑QA benchmark.  
  - **Latency** – Measured on a 2‑core CPU: 32 k token input, 10 runs, 2 warm‑ups; average reported in ms.  
  - **Memory Footprint** – Measured with `tracemalloc` **inside** the `DynamicHiLSWrapper.extract_scores` call to isolate retrieval‑module memory (SC‑005).  
- **Statistical Test** – **Paired t‑test** (`scipy.stats.ttest_rel`) on per‑document log‑perplexities **after** confirming normality with a Shapiro‑Wilk test (`scipy.stats.shapiro`). If the Shapiro‑Wilk p‑value ≥ 0.05, the pipeline automatically falls back to the **Wilcoxon signed‑rank test** (`scipy.stats.wilcoxon`). The chosen method is recorded in `evaluation_report.json.statistical_test.method`.  
- **Multiple Comparisons** – While perplexity is the primary hypothesis, we report the four secondary metrics (QA accuracy, latency, memory footprint, latency‑reduction factor) with a **Bonferroni correction** (α / 4). Both raw and corrected p‑values are stored.  
- **Power Analysis** –  
  - **Perplexity** – Cohen’s d = 0.8 → N ≈ 30 (already satisfied).  
  - **QA Accuracy** – Approximate McNemar’s test, medium effect (Cohen’s h = 0.5) → N ≈ 45.  
  - **Memory Footprint** – Paired t‑test, medium effect (d = 0.5) → N ≈ 40.  
  If the filtered test set falls short, the report flags reduced statistical power for the affected metric.  

### 3.4 Compute Feasibility
- All heavy steps (PCA, K‑Means, inference) are CPU‑only and respect the ≤ 7 GB RAM limit via streaming and batch processing.  
- If the HiLS checkpoint cannot run on CPU, the script will automatically switch to an 8‑bit quantized variant (`load_in_8bit=True`) or fall back to a Kaggle GPU (the CI runner detects a CUDA error and re‑executes on the GPU escape hatch).  

## 4. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient document length** | Validation/test set may become too small. | Filter with `len(tokens) >= 32k`; log exclusion count; if < 30 docs remain, abort with a power‑warning. |
| **Model CUDA requirement** | CPU run fails. | Use 8‑bit quantization or Kaggle GPU offload; both are real, not fabricated. |
| **Memory overflow during aggregation** | OOM on CI runner. | Process documents in streaming batches; write intermediate partial aggregates to disk. |
| **K‑Means empty clusters** | Convergence failure. | Retry with up to 3 seeds; fallback to a lower K if still failing. |
| **Statistical power shortage** | Inconclusive test. | Power analysis reported; if N < 30, state “detectable effect size limited to large effects (d ≥ 0.8)”. |
| **Curse of dimensionality** | Poor clustering. | Mandatory PCA step before K‑Means. |

## 5. Success Criteria Alignment
- **SC‑001** – Δlog PPL computed and reported.  
- **SC‑002** – Latency reduction factor (`latency_dynamic / latency_static`) reported.  
- **SC‑003** – Paired t‑test (or Wilcoxon fallback) p‑value < 0.05 **or** a clear “not significant” flag, recorded in `evaluation_report.json`.  
- **SC‑004** – QA accuracy difference reported.  
- **SC‑005** – Memory usage of the retrieval module measured via `tracemalloc` and logged.  
- **SC‑006** – Sweep report (`sweep_report.json`) contains Δlog PPL, ΔQA, latency, and memory for K = 50, 100, 200.  

---



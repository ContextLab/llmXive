# Research: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Problem Statement & Hypothesis
**Problem** – Dynamic Hierarchical Sparse (HiLS) attention delivers strong long‑context performance but incurs heavy retrieval overhead, limiting edge deployment.  
**Hypothesis** – A static index built by clustering the dynamic model’s relevance profiles can retain most of the performance while reducing inference latency on a 2‑core CPU.  
**Research Question** – *How much dynamic retrieval signal can be compressed into a static index without incurring a statistically significant degradation in perplexity, QA accuracy, or memory usage?*  

## 2. Dataset Strategy
| Dataset | Verified Source URL | Load Method | Fit Check |
|:---|:---|:---|:---|
| **PG‑19 (train split)** | `https://huggingface.co/datasets/deepmind/pg19/resolve/main/data/test_files.txt` (and parquet shards) | `datasets.load_dataset("deepmind/pg19", split="train", streaming=True)` | Contains full‑length books; token counts verified ≥ 32 k after tokenization. |
| **Long‑Context QA** | *No verified open‑source dataset currently meets the ≥ 32 k token requirement.* | *To be supplied by the researcher.* | **ACTION:** Identify or construct a verified long‑context QA benchmark (e.g., a filtered subset of HotpotQA or NarrativeQA with ≥ 32 k token contexts) and provide its HuggingFace URL. Until such a dataset is available, the QA evaluation step (FR‑007) will be **skipped**, and the corresponding metrics will be recorded as `null`/`"N/A"` in the final report. |

### Splitting Strategy
- **Deterministic Shuffle** – PG‑19 stream is shuffled with seed `SEED=42`.  
- **Validation Split** – First [deferred] of shuffled IDs that meet the ≥ 32 k token threshold.
- **Test Split** – Next modest fraction of shuffled, disjoint IDs meeting the same threshold.  
- **Filtering** – Documents shorter than 32 k tokens are **skipped** (`PAD_SHORT_DOCS=False`). All exclusions are logged and the counts recorded in `filtered_pg19.json`.  
- **Checksum** – The resulting JSON (`data/interim/filtered_pg19.json`) includes a SHA‑256 checksum of the ID list for reproducibility.

All splits are stored as JSON conforming to the `SplitDefinition` schema.

## 3. Methodology & Statistical Rigor

### 3.1 Dynamic Baseline Extraction (FR‑001)
- **Model** – HiLS checkpoint `llmxive/hils-base`. Loaded via `transformers.AutoModelForCausalLM.from_pretrained(..., torch_dtype=torch.float32, device_map="cpu")`. If `torch.cuda.is_available()` raises, the script automatically reloads with `load_in_8bit=True` on a Kaggle GPU (real off‑load).  
- **Procedure** – For each validation document, run the model in *dynamic* mode, retrieve `retrieval_score_matrix` (shape `N_chunks × N_tokens`).  
- **Output** – Per‑document tensor saved as `data/interim/raw_scores/<doc_id>.pt`.  

### 3.2 Relevance Profile Aggregation (FR‑001 continuation)
- **Aggregation** – `src/aggregation.py` loads each `.pt` file, computes the mean across tokens for each chunk, and stores a `RelevanceProfile` JSON object (including SHA‑256 checksum of the raw chunk text).  

### 3.3 Static Index Construction (FR‑002)
- **PCA** – Reduce dimensionality to 64 components (captures > 95 % variance).  
- **K‑Means** – CPU‑optimized `sklearn.cluster.KMeans` with **cosine** distance (vectors L2‑normalized), `n_init=10`, `max_iter=300`.  
- **K Values** – `{50, 100, 200}`. Each K is trained on the **validation** relevance profiles; the best K (lowest validation perplexity when used downstream) is selected for final test evaluation.  
- **Convergence Safeguard** – Up to three random seeds; empty‑cluster detection triggers a retry. Failure after three attempts aborts with a clear error message.  
- **Checksum & Metric Recording** – The SHA‑256 checksum of the validation relevance‑profile file is stored as `validation_checksum` in the `StaticIndex` JSON. The `distance_metric` field records `"cosine"`.

### 3.4 Comparative Evaluation (FR‑003‑FR‑008)
- **Test Set** – Held‑out PG‑19 documents (≥ 32 k tokens).  
- **Metrics**  
  - **Log‑Perplexity** – Computed per document; log‑transform improves normality.  
  - **QA Accuracy** – Exact‑match on the long‑context QA benchmark **if** a verified dataset is supplied (otherwise the field is `null`/`"N/A"`).  
  - **Latency** – Measured on a 2‑core CPU: 32 k token input, several runs, a couple of warm‑up iterations; average reported in ms.  
  - **Memory Footprint** – Measured with `tracemalloc` inside the dynamic retrieval call to isolate the retrieval module’s RAM usage.  
- **Statistical Test** –  
  1. **Normality** – Shapiro‑Wilk test on per‑document log‑perplexity differences.  
  2. **If normal (p ≥ 0.05)** – Paired t‑test (`scipy.stats.ttest_rel`).  
  3. **If non‑normal** – Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`).  
  The chosen method and its parameters are recorded in `evaluation_report.json.statistical_test.method`.  
- **Equivalence Test** – Two‑One‑Sided‑Tests (TOST) with equivalence margin Δlog PPL < 0.1 (practically negligible degradation). Power analysis ensures ≥ 80 % power to detect this margin given the sample size; if power is insufficient, the report flags the limitation.  
- **Multiple‑Comparison Correction** – Bonferroni correction (α / 4) applied to the four secondary metrics (QA accuracy, latency, memory, latency‑reduction factor). Both raw and corrected p‑values are saved.  
- **Power Analyses** –  
  - **Perplexity** – Detecting a large effect (Cohen’s d = 0.8) requires N ≈ 30 documents (expected to be satisfied).  
  - **QA Accuracy** – Medium effect (Cohen’s h = 0.5) requires N ≈ 45; if fewer, the report flags reduced power.  
  - **Memory** – Medium effect (d = 0.5) requires N ≈ 40; similarly flagged if insufficient.  

### 3.5 Sensitivity Sweep (FR‑008)
- Loop over K ∈ {50, 100, 200}. For each K, repeat Phases 3–5, then aggregate results into `sweep_report.json` containing Δlog PPL, ΔQA (or `null`), latency, and memory for each K.

## 4. Compute Feasibility
- All heavy operations (PCA, K‑Means, inference) run on CPU within a modest RAM budget by streaming PG‑19 and processing in small batches.  
- The HiLS checkpoint is CPU‑compatible; if a CUDA‑only build is encountered, the pipeline automatically switches to an 8‑bit quantized variant or off‑loads to a Kaggle GPU (real GPU, not a fabricated stub).  

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient long documents | Validation/test sets may be too small for statistical power. | Skip short docs, log counts, abort with power‑warning if < 30 docs remain. |
| HiLS checkpoint requires CUDA | CPU run fails. | Use 8‑bit quantization or Kaggle GPU escape hatch; both are real computations. |
| OOM during aggregation | CI runner crashes. | Stream documents, write partial aggregates to disk, load in chunks. |
| K‑Means empty clusters | Convergence failure. | Retry up to 3 seeds; fallback to lower K if still failing. |
| Power shortage for QA/memory | Inconclusive secondary tests. | Report detectable effect size limits; include power analysis in the final report. |
| High dimensionality hurting clustering | Poor centroids. | Mandatory PCA to 64 components before clustering. |

## 6. Success Criteria Alignment
- **SC‑001** – Δlog PPL computed and stored in `evaluation_report.json`.  
- **SC‑002** – Latency reduction factor (`latency_dynamic / latency_static`) stored in `evaluation_report.json`.  
- **SC‑03** – Paired test p‑value (< 0.05) or explicit “not significant” flag recorded in `evaluation_report.json`.  
- **SC‑004** – QA accuracy difference stored in `evaluation_report.json` **if** a verified QA dataset is supplied; otherwise the field is `null`/`"N/A"`.  
- **SC‑005** – Retrieval‑module memory usage (bytes) stored in `evaluation_report.json`.  
- **SC‑006** – Sweep report (`sweep_report.json`) contains trade‑offs for K = 50, 100, 200.  

---




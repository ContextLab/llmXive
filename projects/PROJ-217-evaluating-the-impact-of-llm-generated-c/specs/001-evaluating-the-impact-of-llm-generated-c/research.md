# Research: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Objective
Quantify how LLM‑generated comments affect developer task performance (completion time, accuracy) relative to human‑written docstrings and a no‑comment baseline, and assess whether standard automated readability metrics (BLEU, ROUGE‑L, Sentence‑BERT similarity) predict those human outcomes.

## Dataset Strategy
| Requirement | Source | Loader | Remarks |
|-------------|--------|--------|---------|
| Code snippets + human docstrings | CodeSearchNet Python (parquet) | `datasets.load_dataset("kejian/codesearchnet-python-raw", split="train", streaming=False)` | Verified URLs: <br>• https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet <br>• https://huggingface.co/datasets/kejian/codesearchnet-python-pep8-v1/resolve/main/data/test-00000-of-00001.parquet <br>• https://huggingface.co/datasets/kejian/codesearchnet-python-raw-457k/resolve/main/data/train-00000-of-00003-a17d5a115f8766d8.parquet |
| LLM inference (CodeLlama‑7B) | HuggingFace Inference API (remote) | `requests.post` with `Authorization: Bearer $HF_TOKEN` | No local GPU needed; inference runs on HF infra. |
| BLEU reference data (optional sanity check) | Sample BLEU dataset (parquet) | `datasets.load_dataset("ravithejads/sample_bleu_data", split="test")` | URL: https://huggingface.co/datasets/ravithejads/sample_bleu_data/resolve/main/data/test-00000-of-00001.parquet |
| ROUGE‑L reference data | Sample ROUGE‑L dataset (parquet) | `datasets.load_dataset("gswamy/pythia-1.4B-tldr-sft_tldr_pythia_1.4b_ROUGE-L_iter_1", split="train")` | URL: https://huggingface.co/datasets/gswamy/pythia-1.4B-tldr-sft_tldr_pythia_1.4b_ROUGE-L_iter_1/resolve/main/data/train-00000-of-00004.parquet |
| Sentence‑BERT embeddings | `sentence-transformers/all-MiniLM-L6-v2` (fallback `paraphrase-MiniLM-L3-v2`) | `SentenceTransformer` from `sentence_transformers` | Loaded on CPU; memory < 2 GB. |
| Human evaluation data | Collected via external survey platform (CSV) | pandas `read_csv` | Must contain columns: `snippet_id`, `condition` (`llm`, `human`, `none`), `completion_time_sec`, `accuracy`, `subjective_helpfulness`. |

All datasets are openly downloadable; no gated data required.

## Methodology

### 1. Data Preparation
1. **Download** the three CodeSearchNet parquet files, verify SHA‑256 checksums (recorded in `data/artifact_hashes.yaml`).  
2. **Extract** fields `code` (string) and `docstring` (string).  
3. **Validate** each docstring: non‑empty, length ≥ 5 tokens, and passes a simple Python `ast.parse` sanity check. Invalid records are written to `excluded_records.json` with a `reason` field.  
4. **Select** a random seed‑controlled subset of **N = 500** snippets (ensures ≥ 30 per experimental condition after human study).  

### 2. Comment Generation (LLM)
- Use **CodeLlama‑7B‑Instruct** via the HF Inference API (`/v1/completions`).  
- Prompt template:  
  ```
  """Generate a concise, helpful comment for the following Python function."""
  <code>
  ```  
- **Retry policy**: up to 3 attempts, exponential back‑off (60 s base).  
- **Truncation**: If tokenized code > 1024 tokens, truncate at the nearest newline before the limit; log warning.  

### 3. Automated Readability Metrics
- **BLEU**: `nltk.translate.bleu_score.sentence_bleu` with smoothing (`method1`). Normalized to 0‑1.  
- **ROUGE‑L**: `rouge_score.rouge_scorer.RougeScorer(['rougeL'])`. Normalized to 0‑1.  
- **Semantic similarity**: cosine similarity between Sentence‑BERT embeddings of the comment and the original docstring.  
- **Fallback**: If `all-MiniLM-L6-v2` fails to load, automatically switch to `paraphrase-MiniLM-L3-v2`.  

### 4. Human Study
- Participants (≥ 30 per condition) perform a **code‑modification task** on each snippet under the assigned comment condition.  
- Metrics collected: `completion_time_sec`, `accuracy` (binary correct/incorrect), and `subjective_helpfulness` (1‑5 Likert).  
- Recruitment tools are validated before launch (e.g., Prolific, MTurk) – logged in `human_study_setup.log`.  

### 5. Statistical Analyses
| Analysis | Method | Software | Multiple‑Comparison Correction |
|----------|--------|----------|--------------------------------|
| Power analysis | `FTestAnovaPower` (effect size = 0.25, α = 0.05) | `statsmodels.stats.power` | N/A |
| One‑way ANOVA (time) | `statsmodels.stats.anova.anova_lm` | `statsmodels` | N/A |
| One‑way ANOVA (accuracy) | `statsmodels.stats.anova.anova_lm` (after arcsine sqrt transform) | `statsmodels` | N/A |
| Correlation (metric ↔ outcome) | Pearson r, two‑tailed | `scipy.stats.pearsonr` | Bonferroni (α/3) for the three metric‑outcome pairs |

- **Assumptions**: Normality of residuals (checked via Shapiro‑Wilk), homogeneity of variance (Levene’s test).  
- **Causal claim**: None. Results are framed as **associational** because the study is experimental with random assignment of comment condition, satisfying isolation principle VII.  

### 6. Reporting
- Generate CSV tables (`anova_results.csv`, `correlations.csv`), PDF figures (`time_by_condition.pdf`, `corr_heatmap.png`).  
- `results_summary.md` cites each table/figure with a direct row identifier per the Single Source of Truth principle.  

## Decision / Rationale
- **CPU‑first**: All local computations (download, preprocessing, metric calc, stats) run on CPU; LLM inference is remote via API (no GPU needed).  
- **Open data**: All inputs are openly hosted on HuggingFace; no gated data required.  
- **Model choice**: CodeLlama‑7B is the smallest instruction‑tuned LLM in the spec that can generate meaningful comments; using the API avoids local GPU constraints.  
- **Embedding fallback**: `all-MiniLM-L6-v2` fits comfortably in ≤ 2 GB RAM; fallback ensures robustness against OOM.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| HF API quota exhausted | Pipeline stops early | Use exponential back‑off; limit total snippets to 500; monitor usage via `X-RateLimit-Remaining` header. |
| Code snippet > context window | Truncated comment may be low quality | Log truncation; later analysis can flag these rows. |
| Human study recruitment shortfall | Power < 0.80 | Power analysis performed upfront; if recruitment fails, report limitation per SC‑005. |
| Metric‑human correlation weak | May not validate automated metrics | Still report correlation values; discuss in `results_summary.md`. |

---

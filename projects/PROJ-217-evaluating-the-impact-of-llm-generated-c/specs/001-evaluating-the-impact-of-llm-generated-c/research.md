# Research: Evaluating the Impact of LLM‑Generated Code Comments on Code Readability

## Objective
Quantify the causal effect of **LLM‑generated comments** on developer task completion time and accuracy relative to human‑written docstrings and a no‑comment baseline, and test whether standard automated readability metrics (BLEU, ROUGE‑L, Sentence‑BERT similarity) predict those human outcomes.

## Dataset Strategy
| Requirement | Source | Loader | Verified URL |
|-------------|--------|--------|--------------|
| Code snippets + human docstrings (Python) | CodeSearchNet Python | `datasets.load_dataset("kejian/codesearchnet-python-raw", split="train", streaming=False)` | https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet |
| Additional CodeSearchNet test split (optional validation) | CodeSearchNet Python test | `datasets.load_dataset("kejian/codesearchnet-python-pep8-v1", split="test", streaming=False)` | https://huggingface.co/datasets/kejian/codesearchnet-python-pep8-v1/resolve/main/data/test-00000-of-00001.parquet |
| BLEU sanity‑check data (not used for primary analysis) | Sample BLEU dataset | `datasets.load_dataset("ravithejads/sample_bleu_data", split="test")` | https://huggingface.co/datasets/ravithejads/sample_bleu_data/resolve/main/data/test-00000-of-00001.parquet |
| ROUGE‑L sanity‑check data (not used for primary analysis) | Sample ROUGE‑L dataset | `datasets.load_dataset("gswamy/pythia-1.4B-tldr-sft_tldr_pythia_1.4b_ROUGE-L_iter_1", split="train")` | https://huggingface.co/datasets/gswamy/pythia-1.4B-tldr-sft_tldr_pythia_1.4b_ROUGE-L_iter_1/resolve/main/data/train-00000-of-00004.parquet |
| Sentence‑BERT embeddings | `sentence-transformers/all-MiniLM-L6-v2` (fallback `paraphrase-MiniLM-L3-v2`) | `SentenceTransformer` from `sentence_transformers` | — (model hosted on HuggingFace, publicly downloadable) |
| Human evaluation data | Collected via Prolific/Mturk (CSV) | `pandas.read_csv` | — (generated during the study) |

All datasets are openly downloadable; no gated data is required.

## Methodology

### 1. Data Preparation
1. **Download** the three verified parquet files; verify their SHA‑256 checksums (recorded in `data/artifact_hashes.yaml`).  
2. **Extract** `code` and `docstring` fields.  
3. **Validate** each docstring: non‑empty, ≥ 5 tokens, and passes a simple `ast.parse` sanity check. Invalid records → `excluded_records.json` with a `reason`.  
4. **Assign** a UUID `snippet_id` to each retained record.  
5. **Select** a deterministic random‑seed‑controlled subset of **N = 500** snippets (ensures ≥ 30 per experimental condition after the human study).  

### 2. LLM Comment Generation
- **Model**: CodeLlama‑7B‑Instruct via the HuggingFace Inference API (`/v1/completions`).  
- **Prompt**:  
  ```
  """Generate a concise, helpful comment for the following Python function."""
  <code>
  ```  
- **Truncation**: If tokenized length > 1024, truncate at the nearest newline before the limit; log the snippet ID.  
- **Retry policy**: Up to 3 attempts, exponential back‑off with base 60 s.  
- **Output**: `llm_comments.jsonl` containing `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty string).  

### 3. Automated Readability Metrics
- **BLEU**: `nltk.translate.bleu_score.sentence_bleu` with `SmoothingFunction().method1`; normalized to 0‑1.  
- **ROUGE‑L**: `rouge_score.rouge_scorer.RougeScorer(['rougeL'])`; normalized to 0‑1.  
- **Semantic similarity**: Cosine similarity between Sentence‑BERT embeddings of **LLM comment** and **human docstring**.  
- **Auxiliary**: Comment character length; Flesch‑Kincaid readability (`textstat.flesch_kincaid_grade`).  
- **Fallback**: If `all-MiniLM-L6-v2` cannot be loaded (OOM), automatically switch to `paraphrase-MiniLM-L3-v2`.  
- **Result file**: `readability_metrics.csv`. For human and none conditions, primary metric columns are `null`.  

### 4. Human Study (Within‑Subject Counterbalanced Design)
- **Participants**: Recruit via Prolific/Mturk; each participant **sees every snippet under all three comment conditions** (LLM, Human, None) in a randomized order to control for learning effects.  
- **Task**: Code‑modification / bug‑fix task on each snippet under the assigned comment condition.  
- **Collected metrics** (per participant‑snippet‑condition): `completion_time_sec`, `accuracy` (0/1), `subjective_helpfulness` (1‑5 Likert).  
- **Data file**: `human_study_responses.csv` (must conform to `contracts/dataset.schema.yaml`).  

### 5. Statistical Analyses
| Analysis | Method | Software | Multiple‑Comparison |
|----------|--------|----------|----------------------|
| Power analysis | `FTestAnovaPower` (effect size = 0.25, α = 0.05) | `statsmodels.stats.power` | N/A |
| One‑way ANOVA (time) | `statsmodels.stats.anova.anova_lm` | `statsmodels` | N/A |
| One‑way ANOVA (accuracy) | Same, after arcsine‑sqrt transform | `statsmodels` | N/A |
| Correlation (metric ↔ outcome) | Pearson *r*, two‑tailed (`scipy.stats.pearsonr`) – **LLM‑only rows only** | `scipy` | Bonferroni (α/4) |

- **Assumptions checks**: Shapiro‑Wilk for normality, Levene’s test for homogeneity.  
- **Causal claim**: Randomisation of condition order within participants permits a causal interpretation **provided the achieved power ≥ 0.80** (reported in `power_report.txt`).  

### 6. Reporting
- Generate CSV tables (`anova_results.csv`, `correlations.csv`), PDF/PNG figures (`fig_time_by_condition.pdf`, `fig_corr_heatmap.png`).  
- Write `results_summary.md` that cites each table/figure with a direct row identifier (e.g., `analysis_dataset.csv: row 12345`).  

## Decision / Rationale
- **CPU‑first**: All heavy computation runs on CPU; LLM inference is remote, so no GPU is needed on the CI runner.  
- **Open data**: Every input source is openly hosted on HuggingFace; no gated data required.  
- **Model choice**: CodeLlama‑7B is the smallest instruction‑tuned model that can generate meaningful comments while staying within the free‑tier API quota.  
- **Embedding fallback**: `all-MiniLM-L6-v2` fits comfortably in ≤ 2 GB RAM; the fallback guarantees robustness on the limited CI box.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| HF API quota exhausted | Pipeline stops early | Limit to 500 snippets; monitor `X-RateLimit-Remaining`; exponential back‑off. |
| Code snippet > context window | Truncated comment may be low quality | Log truncations; later analysis can flag those rows. |
| Human‑study recruitment shortfall | Power < 0.80 | Power analysis performed upfront; target 60 participants; if unmet, report limitation per SC‑005. |
| Weak metric‑human correlation | May not validate automated metrics | Still report raw correlations; auxiliary metrics (length, readability) provide additional insight. |
| Checksum mismatch on download | Failure to produce verified data | Abort with clear error; CI job fails, preventing downstream fabrication. |
| Recruitment platform inaccessible | Study cannot start | Phase 0.5 validates API access before any participant work. |

---




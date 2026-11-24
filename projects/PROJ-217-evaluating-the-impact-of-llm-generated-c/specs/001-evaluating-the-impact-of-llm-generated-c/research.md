# Research: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Objective
Quantify the effect of LLM‑generated comments on developer task completion time and accuracy relative to human‑written docstrings and a no‑comment baseline, and test whether automated similarity metrics (BLEU, ROUGE‑L, Sentence‑BERT cosine) **and a direct readability metric (Flesch‑Kincaid Grade)** predict those human outcomes.

## Dataset Strategy
All sources are open, directly downloadable, and verified.

| Requirement | Source | Loader | Verified URL |
|-------------|--------|--------|--------------|
| Code snippets + human docstrings (Python) | `kejian/codesearchnet-python-raw` (train shard) | `datasets.load_dataset(..., streaming=False)` → `pandas.read_parquet` | https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet |
| Optional test split (validation) | `kejian/codesearchnet-python-rebalanced` (test) | same | https://huggingface.co/datasets/kejian/codesearchnet-python-rebalanced/resolve/main/data/test-00000-of-00001-3967e86c21fe91c3.parquet |
| Sentence‑BERT embeddings | `sentence-transformers/multi-qa-mpnet-base-dot-v1` (fallback `all-MiniLM-L6-v2`) | `SentenceTransformer` | — (public HF Hub model) |
| Human evaluation data | Collected via **Prolific**; consent form stored at `data/consent_form.pdf` | `pandas.read_csv` | — (generated during the study) |

## Methodology

### 1. Data Preparation
1. **Download** the verified parquet with `hf_hub_download` (3‑attempt retry, SHA‑256 verification).  
2. **Convert** the parquet directly to `data/raw_snippets.jsonl` preserving all original fields.  
3. **Parse** columns tolerant to either `code`/`docstring` or `func_code_string`/`func_documentation_string`.  
4. **Validate** each record: docstring length ≥ 5 tokens, code parses with `ast`. Invalid records → `data/excluded_records.json` with a `reason`.  
5. **Log** total, valid, excluded counts to `data/dataset_preparation.log`.  
6. **Deterministically sample** 500 snippets (seed 42) → `data/validated_snippets.jsonl`.  

### 2. LLM Comment Generation
- **Model**: CodeLlama‑7B‑Instruct via HuggingFace Inference API.  
- **Prompt**: `"Generate a concise, helpful comment for the following Python function."` + code.  
- **Truncation**: Code > 2048 tokens is truncated at the nearest newline; each event logged to `data/truncation_warnings.log`.  
- **Batching & Checkpointing**: Process snippets in batches of 50. After each batch, append results to `data/llm_comments.jsonl` and a checkpoint entry to `data/generation_log.txt`.  
- **Retry**: ≤ 3 attempts per batch with exponential backoff (60 s base).  
- **Failure handling**: If a snippet cannot be generated after retries, **fallback** to a deterministic placeholder comment (`"Generated comment for function <name>."`). This ensures a non‑empty `llm_comment` and keeps the pipeline verifiable.  
- **Output**: For each snippet, record `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty string).  

### 3. Automated Readability Metrics
- **BLEU & ROUGE‑L**: Computed with NLTK & `rouge_score`.  
- **Semantic Similarity**: Cosine similarity of Sentence‑BERT embeddings. Primary model `multi-qa-mpnet-base-dot-v1`; fallback to `all-MiniLM-L6-v2` on OOM.  
- **Direct Readability**: Compute **Flesch‑Kincaid Grade** for each comment (using `textstat.flesch_kincaid_grade`). This provides an intrinsic readability measure, addressing construct‑validity concerns.  
- **Reference Sets**:  
  - LLM comment vs. human docstring.  
  - Human comment vs. source code.  
  - No‑comment → metrics set to `null`.  
- **Normalization**: BLEU, ROUGE‑L, and similarity scores scaled to 0‑1; readability grade kept as raw grade.  
- **Auxiliary**: Comment length recorded.  
- **Performance**: 500 × 3 = 1500 metric calculations must finish ≤ 30 min on the CPU runner.  

#### Construct Validity Note (Constitution VI)
Metrics are treated as *similarity proxies* and, for readability, the Flesch‑Kincaid Grade provides a direct textual readability estimate. Correlation analysis (Phase 6) will confirm whether these metrics meaningfully predict comprehension outcomes; weak correlations will be reported transparently and metrics will not be claimed as readability without evidence.

### 4. Human Study (Latin‑Square Within‑Subject Design)
- **Recruitment platform**: Prolific (validated in Phase 2).  
- **Design**: Each participant sees each of a substantial number of snippets exactly once, under one of the three comment conditions, with assignments balanced across participants via a Latin‑Square schedule.  
- **Task**: Code‑modification/bug‑fix for the presented snippet.  
- **Collected per trial**: `completion_time_sec`, `accuracy` (0/1), `subjective_helpfulness` (1‑5).  
- **File**: `data/human_study_responses.csv`.  

### 5. Statistical Analyses
| Analysis | Method | Software | Multiple‑Comparison |
|----------|--------|----------|---------------------|
| Power analysis | Repeated‑measures `statsmodels.stats.power.FTestAnovaPower` (effect size f = 0.25, α = 0.05, within‑subject ρ = 0.5) | statsmodels | N/A |
| Completion time | **One‑way ANOVA** on participant‑averaged times (as required by FR‑005) **and** mixed‑effects ANOVA (`statsmodels.MixedLM`) with fixed effects `condition` + `trial_number`, random intercepts for `participant_id` + `snippet_id` and random slope for `trial_number` per participant | statsmodels | α = 0.05 |
| Accuracy | Mixed‑effects logistic regression (`statsmodels.GLM`, binomial) with same fixed/random structure | statsmodels | α = 0.05 |
| Correlations | Pearson r on **snippet‑level aggregated** outcomes vs each readability metric; Bonferroni‑corrected α / 12 | scipy | Bonferroni |
| Assumption checks | Shapiro‑Wilk (normality), Levene (homogeneity) | scipy | — |

- **Power justification**: Required **N ≥ 30 participants** to achieve ≥ 0.80 power given the assumed parameters; if fewer participants are recruited, the achieved power will be reported and noted as a limitation (SC‑009).  
- **Learning/fatigue**: `trial_number` captures practice effects, modeled as both a fixed effect and a random slope per participant, mitigating confounding (addresses methodology‑55d13f8b).  

### 6. Reporting
- Produce CSV tables, figures (`fig_time_by_condition.pdf`, `fig_corr_heatmap.png`), and `results/results_summary.md` that explicitly cite rows in `merged_dataset.csv`.  
- All outputs validated against the two JSON/YAML contracts; any schema violation aborts CI.  

## Decision / Rationale
- **CPU‑first**: All heavy lifting (metrics, stats, figures) runs on a multi‑core CPU box. LLM inference is remote via HF API, so no GPU escape hatch is required.  
- **Open data**: Primary input is a verified, programmatically downloadable parquet; no gated datasets are used.  
- **Robust generation**: Batch‑checkpointed generation with explicit logs guarantees a verifiable `generation_log.txt`; placeholder comments ensure the output file is always schema‑valid even if the API fails.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| HF API quota exhausted | Generation stops early | Cap at 500 snippets; backoff; placeholder fallback ensures schema compliance. |
| Parquet schema change (T001) | Download/parse failure | Column‑tolerant mapping + explicit error listing; abort on unrecoverable mismatch. |
| Recruitment shortfall | Power < 0.80 | Power analysis performed up‑front; if power insufficient, report limitation per SC‑009. |
| Weak metric‑human correlation | Metrics not validated | Correlations reported honestly; no claim that metrics predict comprehension unless significant. |
| Checksum mismatch | Unverified data | Abort CI; checksum recorded in `artifact_hashes.yaml`. |
| Carry‑over learning | Biased condition effects | Latin‑Square design + `trial_number` covariate and random slope in mixed‑effects models. |
| Generation script crash | Partial results | Batch‑checkpointing ensures progress; CI fails on unrecoverable errors. |

---



# Research: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Objective
Quantify the effect of LLM‑generated comments on developer task completion time and accuracy relative to human‑written docstrings and a no‑comment baseline, and test whether automated readability **similarity** metrics (BLEU, ROUGE‑L, Sentence‑BERT cosine) predict those human outcomes.

## Dataset Strategy
All sources are from the verified block; no gated data.

| Requirement | Source | Loader | Verified URL |
|-------------|--------|--------|--------------|
| Code snippets + human docstrings (Python, primary) | `kejian/codesearchnet-python-raw` (train shard) | `huggingface_hub.hf_hub_download` → `pandas.read_parquet` | https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet |
| CodeSearchNet test split (optional validation) | `kejian/codesearchnet-python-pep8-v1` (test) | same | https://huggingface.co/datasets/kejian/codesearchnet-python-pep8-v1/resolve/main/data/test-00000-of-00001.parquet |
| Sentence‑BERT embeddings | `sentence-transformers/multi-qa-mpnet-base-dot-v1` (fallback `all-MiniLM-L6-v2`) | `SentenceTransformer` | — (public model on HuggingFace Hub) |
| Human evaluation data | Controlled within‑subject user study collected via **Prolific**; consent form at `data/consent_form.pdf` | `pandas.read_csv` | — (collected during the study) |

## Methodology

### 1. Data Preparation
1. Download verified parquet via `hf_hub_download` (3‑attempt retry, SHA‑256 verification). Column‑tolerant parsing maps either `code`/`docstring` or `func_code_string`/`func_documentation_string`. Invalid records → `excluded_records.json` with `reason`. <br>
2. Write `data/raw_snippets.jsonl`; then filter/validate to produce `data/validated_snippets.jsonl` (docstrings ≥ 5 tokens, code parses with `ast`). <br>
3. Deterministic seeded subset of **N = 500** snippets; completeness check ensures ≥ 90 % have all three comment variants (SC‑006). Log to `dataset_preparation.log`.

### 2. LLM Comment Generation
- Model: **CodeLlama‑7B‑Instruct** via HuggingFace Inference API. <br>
- Prompt: `"Generate a concise, helpful comment for the following Python function."` + code. <br>
- Truncate code > 2048 tokens (tiktoken) at nearest newline; log truncations. <br>
- Retry ≤ 3 attempts with exponential backoff (60 s base). <br>
- Output: `data/llm_comments.jsonl` with `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty).

### 3. Automated Readability Metrics
- **LLM comment**: BLEU & ROUGE‑L against the *human docstring*; Sentence‑BERT cosine between LLM comment and human docstring. <br>
- **Human comment**: BLEU & ROUGE‑L against the *source code*; Sentence‑BERT cosine between human comment and source code. <br>
- **No comment**: metrics set to `null`. <br>
- Primary embedding model: `sentence-transformers/multi-qa-mpnet-base-dot-v1`; fallback to `all-MiniLM-L6-v2` on OOM. <br>
- Scores normalized to 0‑1; auxiliary length & Flesch‑Kincaid recorded. <br>
- Unit tests validate implementations against hand‑computed fixtures (tolerance 0.001). <br>
- Batch of 500 pairs must finish ≤ 30 min on CPU (SC‑005).

#### Construct Validity Note
BLEU, ROUGE‑L, and Sentence‑BERT here measure **similarity to the appropriate reference** (human docstring for LLM comments, source code for human comments). They are used as *proxies* under the hypothesis that higher textual overlap with the human‑written explanation or code indicates greater helpfulness for developers. This limitation is explicitly reported; if correlations are weak, the metrics are deemed unsuitable for readability prediction (per Constitution VI).

### 4. Human Study (Latin‑Square Within‑Subject Design)
- **Recruitment platform**: **Prolific**; consent workflow stored at `data/consent_form.pdf`. <br>
- Each participant sees **each snippet exactly once**, assigned to one of the three comment conditions. Across participants, each snippet appears equally often under each condition (Latin‑Square), eliminating learning/carry‑over. <br>
- Task: code‑modification/bug‑fix per snippet‑condition. <br>
- Collected per trial: `completion_time_sec`, `accuracy` (0/1), `subjective_helpfulness` (1‑5). <br>
- File: `data/human_study_responses.csv` (validated post‑merge against `contracts/dataset.schema.yaml`).

### 5. Statistical Analyses
| Analysis | Method | Software | Multiple‑comparison |
|----------|--------|----------|---------------------|
| Power analysis | Within‑subject `FTestPower` (f = 0.25, α = 0.05) | statsmodels | N/A |
| ANOVA (time) | Mixed‑effects ANOVA (`statsmodels.MixedLM`) with random intercepts for participant & snippet | statsmodels | report α = 0.05 |
| Accuracy | Mixed‑effects logistic regression (`statsmodels.GLM`, binomial) with same random effects | statsmodels | report α = 0.05 |
| Correlations | Pearson r on **snippet‑level aggregated** outcomes (mean time, mean accuracy, mean helpfulness) vs each readability metric; Bonferroni α / 12 | scipy | Bonferroni |
| Assumption checks | Shapiro‑Wilk (normality of residuals), Levene (homogeneity) | scipy | — |

- **Power justification**: If achieved power ≥ 0.80, we claim causal inference; otherwise we report the limitation (SC‑009). <br>
- **Effect of carry‑over**: Latin‑Square design removes systematic order effects; any residual learning is modeled via random effects.

### 6. Reporting
- CSV tables, figures (`fig_time_by_condition.pdf`, `fig_corr_heatmap.png`), and `results/results_summary.md` citing exact rows in `merged_dataset.csv`. <br>
- All outputs validated against contracts; any schema violation aborts the CI run.

## Decision / Rationale
- **CPU‑first**: All local processing (metrics, statistics, figures) runs on the 2‑core CPU box; LLM inference is remote via HF API, so no GPU escape hatch is needed. If the API were unavailable, a scaled‑down Kaggle GPU run (reduced‑precision CodeLlama on a 200‑snippet subset) would be used—not a fabricated stand‑in. <br>
- **Open data**: Primary input is a verified, directly downloadable parquet; no gated data. <br>
- **T001 fix**: Download now uses `hf_hub_download` with retry, column‑tolerant mapping, and SHA‑256 verification; aborts with clear column list if mapping fails.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| HF API quota exhausted | Generation stops early | 500‑snippet cap; backoff; partial results persisted |
| Parquet schema mismatch (T001) | Download/parse failure | Column‑tolerant mapping + explicit error; retry |
| Recruitment shortfall | Power < 0.80 | Upfront power analysis; report limitation per SC‑009 |
| Weak metric‑human correlation | Metrics not validated | Report raw correlations honestly; note construct limitation |
| Checksum mismatch | Unverified data | Abort; CI fails |
| Carry‑over learning | Biased condition effects | Latin‑Square design + random‑effects modeling |

---



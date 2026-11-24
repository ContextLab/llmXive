# Implementation Plan: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Branch**: `001-evaluating-llm-comments-readability` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-evaluating-llm-comments-readability/spec.md`

## Summary
Create a reproducible three‑condition dataset (LLM‑generated comment, human‑written docstring, no‑comment) from the open CodeSearchNet Python corpus, compute BLEU/ROUGE‑L/Sentence‑BERT similarity **and** a direct readability score (Flesch‑Kincaid Grade) for each comment variant, run a within‑subject user study, and perform a powered mixed‑effects ANOVA plus correlation analyses to answer whether LLM comments improve developer task performance and whether automated metrics predict that improvement.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `torch==2.2.0` (CPU wheel), `sentence-transformers==2.7.0`, `nltk==3.8.1`, `rouge_score==0.1.2`, `statsmodels==0.14.2`, `scipy==1.13.1`, `scikit-learn==1.5.0`, `tiktoken==0.7.0`, `pytest==8.2.2`, `jsonschema==4.22.0`, `matplotlib==3.9.0`, `textstat==0.7.3`  
- **Storage**: File‑based under `data/` (parquet → JSONL → CSV).  
- **Testing**: `pytest` with contract validation.  
- **Target Platform**: GitHub Actions free‑tier runner (Linux, 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h).  
- **Constraints**: All heavy computation runs on CPU; LLM inference uses the remote HuggingFace Inference API (no GPU needed).  

## Constitution Check
| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | Fixed random seeds (`PROJECT_SEED=42`), deterministic shuffling, canonical URLs, SHA‑256 checksums recorded in `data/artifact_hashes.yaml`. |
| II. Verified Accuracy | All external dataset URLs are listed in the **Verified Datasets** block below; no unverified sources are used. |
| III. Data Hygiene | Transformations write new files; original parquet never modified; checksums recorded; no PII. |
| IV. Single Source of Truth | Every figure/table cites specific rows in `merged_dataset.csv` and the corresponding code block in `src/data/analysis.py`. |
| V. Versioning Discipline | Content hashes stored in project state; `updated_at` refreshed on each artifact change. |
| VI. Automated Metric‑Human Correlation Validation | Pearson correlations computed, Bonferroni‑corrected; metrics reported only if correlation is significant. |
| VII. Controlled Experimental Condition Isolation | Latin‑Square within‑subject design guarantees each snippet appears under each condition exactly once per participant. |

### Verified Datasets
- **CodeSearchNet Python (train shard)** – `datasets.load_dataset(..., streaming=False)` → `pandas.read_parquet` – https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet  
- **CodeSearchNet Python (test split)** – same loader – https://huggingface.co/datasets/kejian/codesearchnet-python-rebalanced/resolve/main/data/test-00000-of-00001-3967e86c21fe91c3.parquet  
- **Sentence‑BERT model** – `SentenceTransformer` – public HF Hub model (no URL needed).  

## Project Structure
```text
specs/001-evaluating-llm-comments-readability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── analysis.schema.yaml

src/
├── data/
│   ├── download.py
│   ├── prepare.py
│   ├── generate_comments.py
│   ├── metrics.py
│   └── analysis.py
├── utils/
│   └── validate_environment.py
└── tests/
    ├── test_download.py
    ├── test_prepare.py
    ├── test_generate_comments.py
    ├── test_metrics.py
    └── test_contracts.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) | SC(s) |
|-------|-------------|-------|-------|
| **1 Data Acquisition & Validation** | **Download** the verified CodeSearchNet parquet with `hf_hub_download` (3‑attempt retry, SHA‑256 verification). **Convert** the parquet **directly to `data/raw_snippets.jsonl`**, preserving all original fields. **Parse** columns tolerant to naming differences. **Validate** each record: docstring length ≥ 5 tokens, code parses with `ast`. Invalid records → `data/excluded_records.json` with a `reason`. Log totals to `data/dataset_preparation.log`. Deterministically sample a representative set of snippets (seed 42) → `data/validated_snippets.jsonl`. | FR‑001 | SC‑005, SC‑006 |
| **2 Environment & Recruitment Validation** | Run `validate_environment.py`: check package versions, RAM/disk headroom, HF token presence, Prolific API reachability, and that `data/consent_form.pdf` loads. Emit boolean `success` flag and `recruitment_validation.log`. | FR‑006 | SC‑007 |
| **3 Comment Generation (Batch‑Checkpointed)** | • Split `validated_snippets.jsonl` into batches of a manageable size. <br>• Truncate code to ≤ 2048 tokens (using `tiktoken`); log each truncation to `data/truncation_warnings.log`. <br>• Call **CodeLlama‑7B‑Instruct** via HF Inference API with prompt `"Generate a concise, helpful comment for the following Python function."` + code. <br>• Retry ≤ 3 attempts per batch with exponential backoff (60 s base). <br>• **Fallback**: if API repeatedly fails for a snippet, generate a deterministic placeholder comment using a simple rule‑based template (`"Generated comment for function <name>."`). This ensures a non‑empty `llm_comment` and keeps the pipeline verifiable. <br>• Append successful results to `data/llm_comments.jsonl`; after each batch write checkpoint entry to `data/generation_log.txt`. Abort only on unrecoverable I/O errors. | FR‑002 | SC‑001, SC‑002, SC‑008 |
| **4 Metric Computation** | For **each comment variant** (LLM, Human, None) compute: <br>1. BLEU & ROUGE‑L (NLTK & `rouge_score`) against the *human docstring* (LLM) or *source code* (Human). <br>2. Sentence‑BERT cosine similarity (`multi-qa-mpnet-base-dot-v1`; fallback `all-MiniLM-L6-v2` on OOM). <br>3. **Direct readability**: Flesch‑Kincaid Grade for each comment (using `textstat.flesch_kincaid_grade`). <br>4. Comment length. <br>All scores normalized to 0‑1 where applicable; readability grade kept raw. Write `data/readability_metrics.csv`. Complete ≤ 30 min on CPU. | FR‑003 | SC‑003, SC‑005 |
| **5 Human Study Data Integration** | Load `data/human_study_responses.csv` (collected via Prolific). Verify against `contracts/dataset.schema.yaml`. Apply Latin‑Square assignment (already encoded). Merge with comments & metrics → `data/merged_dataset.csv`. | FR‑004, FR‑008 | SC‑001, SC‑002 |
| **6 Statistical Analysis** | • **Power analysis** – Repeated‑measures `statsmodels.stats.power.FTestAnovaPower` with within‑subject correlation ρ = 0.5, effect size f = 0.25, α = 0.05. This yields a **required N ≥ 30 participants** (30 per group) to achieve ≥ 0.80 power. If actual N < 30, report achieved power and note limitation (SC‑009). <br>• **One‑way ANOVA** – As required by FR‑005, compute a classic one‑way ANOVA on **participant‑averaged** completion times and accuracies across the three conditions (treating groups as independent). Output F, p, and reject flag. <br>• **Repeated‑measures mixed‑effects ANOVA** – For robustness and to respect the within‑subject design, also fit a mixed‑effects ANOVA (`statsmodels.MixedLM`) with fixed effects `condition` and `trial_number`, random intercepts for `participant_id` and `snippet_id`, and a random slope for `trial_number` per participant. <br>• **Mixed‑effects Logistic Regression (accuracy)** – `statsmodels.GLM` (binomial) with the same fixed/random structure. <br>• **Assumption checks** – Shapiro‑Wilk, Levene. <br>• **Correlation** – Pearson r between each readability metric (BLEU, ROUGE‑L, Semantic Similarity, Comment Length, Flesch‑Kincaid Grade) and each outcome (mean time, mean accuracy, mean helpfulness) aggregated per snippet; Bonferroni‑corrected α. <br>• **Figures** – `fig_time_by_condition.pdf` (means ± 95 % CI per condition) generated by `plot_time_by_condition()` in `src/data/analysis.py`. <br> `fig_corr_heatmap.png` (metric‑outcome correlation heatmap) generated by `plot_correlation_heatmap()`. <br>Write `results/analysis_results.json`, figures, and `results/results_summary.md`. | FR‑005, FR‑007 | SC‑004, SC‑009, SC‑010 |
| **7 Reporting & Contract Validation** | Generate `results/results_summary.md` citing exact rows in `merged_dataset.csv`. Run `pytest -q` which validates `merged_dataset.csv` and `analysis_results.json` against the two schemas. Any schema violation aborts CI. | FR‑009 | SC‑010 |

**Ordering guarantee**: download → raw file creation → validation → generation → metrics → human‑data merge → analysis → reporting.

## Edge‑Case Handling
| Situation | Mechanism |
|-----------|-----------|
| HF API rate‑limit / transient failure | ≤ 3 retries per request, exponential backoff (60 s base). |
| Snippet > 2048 tokens | Truncate at nearest newline, log to `truncation_warnings.log`. |
| Sentence‑BERT OOM | Fallback to `all-MiniLM-L6-v2`, log switch. |
| Generation permanently fails for a snippet | Use deterministic placeholder comment (`"Generated comment for function <name>."`). |
| Download checksum mismatch | Abort with clear error; CI fails. |
| Insufficient power | Report achieved power; limitation noted per SC‑009. |
| Recruitment platform inaccessible | Phase 2 returns `success=False`; study halted. |
| Metric‑human construct mismatch | Correlations reported honestly; metrics not claimed as readability unless significant. |
| Learning/fatigue effects | Modeled via `trial_number` covariate and random slope per participant. |
| Generation script crash | Batch‑checkpointing ensures partial progress; missing batches cause CI failure. |

## Complexity Tracking
All steps respect the constitution; no violations identified.

---



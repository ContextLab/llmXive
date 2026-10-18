# Implementation Plan: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Branch**: `001-evaluating-llm-comments-readability` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

## Summary
Build a reproducible three‑condition dataset (LLM‑generated comment, human‑written docstring, no comment) from the open CodeSearchNet Python corpus, compute BLEU/ROUGE‑L/Sentence‑BERT similarity for **all comment variants** against **both the source code and the human docstring**, integrate a Latin‑Square within‑subject user study data, and run a powered mixed‑effects analysis plus correlation analyses to answer whether LLM comments improve developer task performance and whether automated similarity metrics predict that improvement.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `pyarrow==16.1.0`, `requests==2.32.3`, `huggingface-hub==0.23.2`, `sentence-transformers==2.7.0`, `torch==2.2.0` (CPU wheel), `nltk==3.8.1`, `rouge_score==0.1.2`, `statsmodels==0.14.2`, `scipy==1.13.1`, `scikit-learn==1.5.0`, `textstat==0.7.3`, `tiktoken==0.7.0`, `pytest==8.2.2`, `jsonschema==4.22.0`, `matplotlib==3.9.0`
- **Storage**: File‑based under `data/` (parquet → JSONL → CSV).
- **Testing**: pytest (unit + contract tests).
- **Target Platform**: Linux GitHub Actions runner (CPU‑only, 2 cores, ≤ 7 GB RAM, ≤ 6 h).
- **Constraints**: LLM inference via remote HuggingFace Inference API (no local GPU needed); all local computation runs on CPU.

## Constitution Check
| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | Fixed seed (`PROJECT_SEED=42`), canonical verified dataset URLs, SHA‑256 checksums, pinned `requirements.txt`. |
| II. Verified Accuracy | Citations limited to the verified URLs in the “Verified datasets” block; no invented URLs. |
| III. Data Hygiene | SHA‑256 recorded in `data/artifact_hashes.yaml`; every transformation writes a new file; no in‑place edits; no PII. |
| IV. Single Source of Truth | Every figure/statistic traces back to a row in `data/merged_dataset.csv` and a code block in `src/`. |
| V. Versioning Discipline | Content hashes recorded in the project state file; `updated_at` refreshed on each artifact change. |
| VI. Automated Metric‑Human Correlation Validation | Pearson correlations computed on **snippet‑level aggregated outcomes**; Bonferroni‑corrected; similarity metrics are explicitly framed as *proxies* for readability (see Research §3). |
| VII. Controlled Experimental Condition Isolation | Latin‑Square design ensures each snippet appears under each condition across participants, eliminating within‑subject carry‑over. |

## Project Structure
```text
specs/001-evaluating-llm-comments-readability/
├── plan.md, research.md, data-model.md, quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── analysis.schema.yaml

src/
├── data/
│   ├── download.py            # verified parquet download + checksum (fixed T001)
│   ├── prepare.py             # validation, exclusion, three‑condition assembly
│   ├── generate_comments.py   # HF Inference API wrapper, retry/backoff, 2048‑token truncation
│   ├── metrics.py             # BLEU, ROUGE‑L, Sentence‑BERT + dual‑reference scores
│   └── analysis.py            # power, mixed‑effects ANOVA, mixed logistic regression, correlation, reporting
├── utils/
│   └── validate_environment.py  # FR‑006 environment & recruitment check
└── tests/
    ├── test_download.py
    ├── test_metrics.py
    └── test_contracts.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) | SC(s) |
|-------|-------------|-------|-------|
| **0 Setup** | Install pinned deps; export `HF_TOKEN`. | — | — |
| **1 Data Acquisition & Validation** | Download the **verified** CodeSearchNet parquet files via `hf_hub_download` (3‑attempt retry, SHA‑256 verification). Column‑tolerant parsing maps either `code`/`docstring` or `func_code_string`/`func_documentation_string`. Invalid records are written to `excluded_records.json` with a `reason`. Deterministic seeded subset of **N = 500** snippets is written to `data/raw_snippets.jsonl` and then filtered/validated into `data/validated_snippets.jsonl`. | FR-001 | SC-005, SC-006 |
| **2 Environment & Recruitment Validation** | Run `validate_environment.py`: verify required packages, RAM/disk headroom, HF token validity, **Prolific** API reachability, and that `data/consent_form.pdf` loads without error. Emit boolean `success` flag and `recruitment_validation.log`. | FR-006 | SC-007 |
| **3 Comment Generation** | Truncate code to ≤ **2048 tokens** (tiktoken) at nearest newline, log `truncation_warnings.log`. Call **CodeLlama‑7B‑Instruct** via HF Inference API; retry ≤ 3 attempts, exponential backoff (60 s base). Write `data/llm_comments.jsonl` containing `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty). | FR-002 | SC-001, SC-002, SC-008 |
| **4 Metric Computation** | For **each comment variant** (LLM, Human, None) compute **two sets** of metrics: <br>1. **Against source code** – BLEU, ROUGE‑L, and Sentence‑BERT cosine similarity. <br>2. **Against the human docstring** – BLEU, ROUGE‑L, and Sentence‑BERT cosine similarity. <br>For the **None** condition both sets are `null`. <br>Primary embedding model: `sentence-transformers/multi-qa-mpnet-base-dot-v1`; fallback to `all-MiniLM-L6-v2` on OOM. All scores normalized to 0‑1. Auxiliary length & Flesch‑Kincaid recorded. Output `data/readability_metrics.csv` with columns `BLEU_vs_source`, `BLEU_vs_human`, `ROUGE_L_vs_source`, `ROUGE_L_vs_human`, `Semantic_Similarity_vs_source`, `Semantic_Similarity_vs_human`. Must complete ≤ 30 min CPU. | FR-003 | SC-003, SC-005 |
| **5 Human Study Data Integration** | Load **Prolific**‑collected `data/human_study_responses.csv` (validated against `contracts/dataset.schema.yaml` after merge). Apply **Latin‑Square** assignment: each participant sees each snippet **once**, under a condition assigned such that across participants every snippet appears equally in all three conditions. Merge with comments and metrics on `snippet_id` + `condition` → `data/merged_dataset.csv`. | FR-004, FR-008 | SC-001, SC-002 |
| **6 Statistical Analysis** | **Power analysis** – within‑subject `statsmodels.stats.power.FTestPower` with effect size f = 0.25, α = 0.05 → `results/power_report.txt`. <br>**Mixed‑effects ANOVA** – `statsmodels.MixedLM` for `completion_time_sec` with random intercepts for `participant_id` and `snippet_id`. <br>**Mixed‑effects Logistic Regression** – `statsmodels.GLM` (binomial) for `accuracy` with same random effects. <br>**Assumption checks** – Shapiro‑Wilk (normality of residuals), Levene (homogeneity). <br>**Correlation** – aggregate per `snippet_id` (mean completion time, mean accuracy, mean helpfulness) then Pearson correlation with each readability metric (both source‑ and human‑reference scores); Bonferroni‑corrected α = 0.05/12. Output `results/analysis_results.json` (power, ANOVA, logistic, correlations) and figures (`fig_time_by_condition.pdf`, `fig_corr_heatmap.png`). | FR-005, FR-007 | SC-004, SC-009 |
| **7 Reporting & Contract Validation** | Generate `results/results_summary.md` citing exact rows in `merged_dataset.csv`. Run `pytest -q` which validates all outputs against `contracts/dataset.schema.yaml` and `contracts/analysis.schema.yaml`. Any checksum mismatch aborts the run. | FR-009 | SC-010 |

**Ordering guarantee**: data downloaded (Phase 1) before generation (3) and metrics (4); comments generated before metrics; metrics + human data merged before analysis (6); figures generated before inclusion in the report (7).

## Edge‑Case Handling
| Situation | Mechanism |
|-----------|-----------|
| HF API rate limit / transient failure | ≤ 3 retries, exponential backoff (60 s base) |
| Snippet > context window | Truncate at 2048 tokens (nearest newline), log to `truncation_warnings.log` |
| Sentence‑BERT OOM | Fallback to `all-MiniLM-L6-v2`, log switch |
| Download failure / checksum mismatch (T001) | 3‑attempt retry; column‑tolerant schema mapping with explicit error listing; abort on checksum mismatch |
| Insufficient power | Report achieved power; limitation noted, no causal claim |
| Recruitment platform inaccessible | Phase 2 returns `success=False`; study halted |
| Carry‑over / learning effects | Latin‑Square design eliminates repeated exposure; each snippet appears once per participant |
| Metric‑human construct mismatch | Metrics framed as similarity proxies; justification provided in Research §3 |

## Complexity Tracking
None — no constitution violations.

---


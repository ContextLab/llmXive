# Implementation Plan: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Branch**: `001-evaluating-llm-comments-readability` | **Date**: 2026-10-17 | **Spec**: [spec.md](../specs/001-evaluating-llm-comments-readability/spec.md)

## Summary
Build a reproducible three‑condition dataset (LLM‑generated comment, human‑written docstring, no comment) from the open CodeSearchNet Python corpus, compute BLEU/ROUGE‑L/Sentence‑BERT similarity for the LLM comments, conduct a **within‑subject, counterbalanced** human performance study, and run a powered one‑way ANOVA plus correlation analyses to answer whether LLM comments improve developer task performance and whether the automated metrics predict that improvement.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `datasets==2.19.0`, `torch==2.2.0`, `transformers==4.41.0`, `sentence-transformers==2.7.0`, `nltk==3.8.1`, `rouge_score==0.1.2`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `tqdm==4.66.2`, `requests==2.32.3`, `textstat==0.7.3`  
- **Storage**: File‑based under `data/` (parquet → JSONL → CSV).  
- **Testing**: `pytest==8.2.2` (unit + contract tests).  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only, ≤ 7 GB RAM, ≤ 6 h).  
- **Constraints**: All heavy computation runs on CPU; LLM inference is performed via the remote HuggingFace Inference API (no GPU needed).

## Constitution Check
| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | Fixed random seed (`PROJECT_SEED`), deterministic dataset URLs, checksum‑verified downloads, pinned `requirements.txt`. |
| II. Verified Accuracy | All citations (CodeSearchNet, CodeLlama, BLEU/ROUGE datasets) are limited to the verified URLs listed in the spec. |
| III. Data Hygiene | SHA‑256 checksums recorded in `data/artifact_hashes.yaml`; every transformation writes a new file; no in‑place edits. |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/` and a line in `code/`. |
| V. Versioning Discipline | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Automated Metric‑Human Correlation Validation | Correlation analysis is performed **only on LLM‑only rows**; human/none rows have `null` metric fields. |
| VII. Controlled Experimental Condition Isolation | **Each snippet is presented to every participant under all three comment conditions (LLM, Human, None) in a randomized, counterbalanced order**, ensuring that snippet difficulty is held constant across conditions and enabling causal attribution. |

## Project Structure
```text
specs/001-evaluating-llm-comments-readability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis.schema.yaml
    └── dataset.schema.yaml

src/
├── data/
│   ├── download.py               # download & checksum CodeSearchNet
│   ├── prepare.py                # validation, exclusion, three‑condition assembly
│   ├── generate_comments.py      # HF API wrapper with retry/backoff
│   ├── metrics.py                # BLEU, ROUGE‑L, Sentence‑BERT + aux metrics
│   └── analysis.py               # power, ANOVA, correlation, reporting
├── utils/
│   └── logging.py
└── cli/
    └── run_pipeline.py           # orchestrates all stages
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|------------------|
| **0 Setup** | Install dependencies, export `HF_TOKEN`. | — | — |
| **0.5 Recruitment Platform Validation** | Verify access to Prolific/Mturk API, check that consent workflow files exist, and perform a dry‑run of participant creation (no real participants). Record a `recruitment_validation.log`. | **FR‑006** | SC‑005 |
| **1 Data Acquisition & Validation** | • Download three verified CodeSearchNet parquet files (see URLs in `research.md`). <br>• Verify SHA‑256 checksums (recorded in `data/artifact_hashes.yaml`). <br>• Extract `code` & `docstring`, drop malformed records to `excluded_records.json`. <br>• Assign UUID `snippet_id`; keep a deterministic random‑seed‑controlled subset of **N = 500** snippets. | FR‑001 | SC‑005 |
| **2 Comment Generation** | For each retained snippet: <br>• Truncate to ≤ 1024 tokens (tiktoken) if needed, log warning. <br>• Call **CodeLlama‑7B‑Instruct** via HuggingFace Inference API with the prompt template. <br>• Retry up to 3 times, exponential back‑off (60 s base). <br>• Write `llm_comments.jsonl` containing `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty). | FR‑002 | SC‑001, SC‑002 |
| **3 Metric Computation** | Compute per‑snippet: <br>• BLEU (nltk, smoothing) <br>• ROUGE‑L (rouge_score) <br>• Sentence‑BERT cosine similarity (load `all-MiniLM-L6-v2`; fallback `paraphrase-MiniLM-L3-v2`). <br>• Auxiliary: character length, Flesch‑Kincaid readability (textstat). <br>• Normalize primary scores to 0‑1; set them to `null` for human/none rows. <br>• Output `readability_metrics.csv`. | FR‑003 | SC‑003 |
| **4 Human Study Data Integration** | Load the externally collected `human_study_responses.csv` (must conform to **`contracts/dataset.schema.yaml`**). Merge with `llm_comments.jsonl` and `readability_metrics.csv` on `snippet_id` → `analysis_dataset.csv`. | FR‑004, FR‑006 | SC‑001, SC‑002 |
| **5 Statistical Analysis** | • **Power analysis**: `FTestAnovaPower` (effect size f = 0.25, α = 0.05) → required a sufficiently large sample size per group; target a sufficient number of participants per condition. Write `power_report.txt`. <br>• **One‑way ANOVA** on `completion_time_sec` and on `accuracy` (arcsine‑sqrt transformed) across the three **within‑subject** conditions → `anova_results.json`. <br>• **Correlation**: Pearson *r* between each LLM‑only metric (BLEU, ROUGE‑L, Semantic_Similarity, Comment_Length) and each human outcome; Bonferroni‑corrected α/4. Output `correlations.csv`. | FR‑005, FR‑007 | SC‑004, SC‑005 |
| **6 Reporting** | Assemble tables (`anova_results.csv`, `correlations.csv`), figures (`fig_time.pdf`, `fig_corr.png`), and a markdown summary `results_summary.md` that cites exact rows in `analysis_dataset.csv`. | — | — |
| **7 Contract Validation** | Run `pytest -q` which checks: <br>• All output files (`analysis_dataset.csv`, `readability_metrics.csv`, `human_study_responses.csv`, `results/*.json/csv`) against **both** `contracts/dataset.schema.yaml` **and** `contracts/analysis.schema.yaml`. <br>• Any checksum mismatches abort the run. | — | — |

## Edge‑Case Handling
| Situation | Mechanism |
|-----------|-----------|
| HF API rate‑limit / transient failure | Retry wrapper: up‑to‑3 attempts, exponential back‑off (60 s). |
| Code snippet exceeds CodeLlama‑7B context window | Tokenize with `tiktoken`, truncate at the nearest newline before 1024 tokens; log `truncation_warnings.log`. |
| Sentence‑BERT OOM | Load `all-MiniLM-L6-v2`; on failure fall back to `paraphrase-MiniLM-L3-v2`. |
| Insufficient power after recruitment | Power analysis reports achieved power; if < 0.80, `results_summary.md` notes the limitation and refrains from causal claims. |
| Correlation tautology | Correlation is restricted to **LLM‑only** rows; human/none rows have `null` metric fields. |
| Download checksum mismatch | Script aborts with a clear error; the CI job fails, preventing downstream fabrication. |
| Recruitment platform inaccessible | Phase 0.5 aborts with a logged error, preventing the study from starting. |

## Timeline (estimated CI minutes)
| Step | Approx. runtime (CPU) |
|------|-----------------------|
| Download & checksum | 2 min |
| Validation & exclusion | 3 min |
| Recruitment platform validation | 1 min |
| Comment generation (≈ 500 snippets) | 12 min (API latency dominates) |
| Metric computation | 4 min |
| Merge human data | 1 min |
| Power + ANOVA + correlation | 3 min |
| Reporting & contract check | 2 min |
| **Total** | **[deferred]** (well within 6 h limit) |

---




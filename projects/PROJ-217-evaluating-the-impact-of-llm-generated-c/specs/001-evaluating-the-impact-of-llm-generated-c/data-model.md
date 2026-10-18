# Data Model: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Overview
Six core entities flow through the pipeline; each stored under `data/`.

| Entity | Primary File(s) | Format | Key Fields |
|--------|----------------|--------|------------|
| **CodeSnippet** | `raw_snippets.jsonl` | JSON Lines | `snippet_id` (UUID), `code`, `human_comment`, `metadata` |
| **ValidatedSnippet** | `validated_snippets.jsonl` | JSON Lines | `snippet_id`, `code`, `human_comment`, `metadata` (post‑validation) |
| **CommentVariant** | `llm_comments.jsonl` | JSON Lines | `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty) |
| **ReadabilityMetric** | `readability_metrics.csv` | CSV | `snippet_id`, `variant_type` (llm/human/none), `BLEU_vs_source`, `BLEU_vs_human`, `ROUGE_L_vs_source`, `ROUGE_L_vs_human`, `Semantic_Similarity_vs_source`, `Semantic_Similarity_vs_human`, `Comment_Length`, `Flesch_Kincaid` (metrics computed for *all* comment variants; `null` where not applicable) |
| **HumanEvaluation** | `human_study_responses.csv` | CSV | `participant_id`, `snippet_id`, `condition`, `completion_time_sec`, `accuracy`, `subjective_helpfulness` |
| **AnalysisResult** | `results/` | JSON/CSV/TXT/PDF/PNG | conforms to `contracts/analysis.schema.yaml` |

## File‑level Schemas
- `raw_snippets.jsonl` – one CodeSnippet per line; produced from checksum‑verified parquet; invalid records go to `excluded_records.json` with `reason`. <br>
- `validated_snippets.jsonl` – subset of `raw_snippets.jsonl` after docstring relevance checks; immutable after creation. <br>
- `llm_comments.jsonl` – extends `validated_snippets.jsonl` with `llm_comment`; `no_comment` always empty string. <br>
- `readability_metrics.csv` – one row per `snippet_id` **per comment variant** (LLM, Human, None). For each variant we record **two sets** of similarity scores: one against the source code (`*_vs_source`) and one against the human docstring (`*_vs_human`). For the **None** variant all metric fields are `null`. <br>
- `human_study_responses.csv` – one row per participant‑snippet‑condition; three rows per participant‑snippet in the Latin‑Square design. <br>
- `merged_dataset.csv` – merge of `llm_comments.jsonl`, `readability_metrics.csv`, and `human_study_responses.csv` on `snippet_id` + `condition`; conforms to `contracts/dataset.schema.yaml`. <br>
- `results/analysis_results.json` – JSON summary of power analysis, mixed‑effects ANOVA, mixed logistic regression, and correlation tables (see `contracts/analysis.schema.yaml`). <br>

All transformations are pure functions writing new files; no in‑place edits (Principle III). Raw parquet is preserved unchanged; derivations to new filenames; SHA‑256 of every `data/` file recorded in `data/artifact_hashes.yaml`.

---




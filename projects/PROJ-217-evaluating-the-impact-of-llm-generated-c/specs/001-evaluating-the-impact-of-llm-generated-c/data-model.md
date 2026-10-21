# Data Model: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Overview
Six core entities flow through the pipeline; each is stored under `data/` with a dedicated schema.

| Entity | Primary File(s) | Format | Key Fields |
|--------|----------------|--------|------------|
| **CodeSnippet** | `raw_snippets.jsonl` | JSON Lines | `snippet_id` (UUID), `code`, `human_comment`, `metadata` |
| **ValidatedSnippet** | `validated_snippets.jsonl` | JSON Lines | `snippet_id`, `code`, `human_comment`, `metadata` |
| **CommentVariant** | `llm_comments.jsonl` | JSON Lines | `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` |
| **ReadabilityMetric** | `readability_metrics.csv` | CSV | `snippet_id`, `variant_type` (llm/human/none), `BLEU_vs_source`, `BLEU_vs_human`, `ROUGE_L_vs_source`, `ROUGE_L_vs_human`, `Semantic_Similarity_vs_source`, `Semantic_Similarity_vs_human`, `Comment_Length`, `Flesch_Kincaid_Grade` |
| **HumanEvaluation** | `human_study_responses.csv` | CSV | `participant_id`, `snippet_id`, `condition`, `completion_time_sec`, `accuracy`, `subjective_helpfulness` |
| **MergedDataset** | `merged_dataset.csv` | CSV | Conforms to `contracts/dataset.schema.yaml` (see below). |
| **AnalysisResult** | `results/analysis_results.json` (plus PNG/PDF figures) | JSON/PNG/PDF | Conforms to `contracts/analysis.schema.yaml`. |

## File‑level Schemas
- **raw_snippets.jsonl** – Direct conversion from the verified parquet; each line contains the original fields. Invalid rows are omitted and recorded in `excluded_records.json` with a `reason`.  
- **validated_snippets.jsonl** – Subset after docstring relevance checks; immutable after creation.  
- **llm_comments.jsonl** – Extends `validated_snippets.jsonl` with `llm_comment`; `no_comment` is the empty string.  
- **readability_metrics.csv** – One row per `snippet_id` × `variant_type`. For the **none** variant all metric columns are `null`. Includes a direct readability score (`Flesch_Kincaid_Grade`).  
- **human_study_responses.csv** – One row per participant‑snippet‑condition (Latin‑Square ensures three rows per participant‑snippet).  
- **merged_dataset.csv** – Join of `llm_comments.jsonl`, `readability_metrics.csv`, and `human_study_responses.csv` on `snippet_id` + `condition`. Must validate against `contracts/dataset.schema.yaml`.  
- **results/analysis_results.json** – JSON summary of power analysis, mixed‑effects ANOVA (time & accuracy), and correlation tables; must validate against `contracts/analysis.schema.yaml`.  

All transformations are pure functions that write new files; no in‑place edits (Principle III). SHA‑256 of every `data/` artifact is recorded in `data/artifact_hashes.yaml`.

---


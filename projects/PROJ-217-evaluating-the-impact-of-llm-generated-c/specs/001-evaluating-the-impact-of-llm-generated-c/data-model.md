# Data Model: Evaluating the Impact of LLM‑Generated Code Comments on Code Readability

## Overview
Five core entities flow through the pipeline; each is stored under `data/` in the indicated format.

| Entity | Primary File(s) | Format | Key Fields |
|--------|----------------|--------|------------|
| **CodeSnippet** | `raw_snippets.jsonl` (post‑validation) | JSON Lines | `snippet_id` (UUID), `code` (str), `human_comment` (str), `metadata` (object) |
| **CommentVariant** | `llm_comments.jsonl` | JSON Lines | `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty) |
| **ReadabilityMetric** | `readability_metrics.csv` | CSV | `snippet_id`, `BLEU` (0‑1 or null), `ROUGE_L` (0‑1 or null), `Semantic_Similarity` (0‑1 or null), `Comment_Length` (int), `Flesch_Kincaid` (float) |
| **HumanEvaluation** | `human_study_responses.csv` | CSV | `participant_id`, `snippet_id`, `condition` (`llm`/`human`/`none`), `completion_time_sec` (float), `accuracy` (0/1), `subjective_helpfulness` (1‑5) |
| **AnalysisResult** | `results/` (JSON/CSV/TXT) | Various | Structured per the `contracts/analysis.schema.yaml`. |

## File‑level Schemas
- **`raw_snippets.jsonl`** – each line conforms to the *CodeSnippet* schema (see `contracts/analysis.schema.yaml` for the merged schema).  
- **`llm_comments.jsonl`** – extends *CodeSnippet* with `llm_comment`; `no_comment` is always the empty string.  
- **`readability_metrics.csv`** – one row per `snippet_id`; primary metrics are populated **only for LLM comments**; they are `null` for human/none rows.  
- **`human_study_responses.csv`** – one row per participant‑snippet‑condition interaction; each participant contributes **three rows per snippet** (one for each condition) due to the within‑subject, counterbalanced design; `condition` must be one of the three allowed values.  
- **`analysis_dataset.csv`** – result of merging the above tables on `snippet_id` (and `condition` for human data).  

All transformations are pure functions; no in‑place file modifications occur, satisfying **Data Hygiene** (Principle III).  

---



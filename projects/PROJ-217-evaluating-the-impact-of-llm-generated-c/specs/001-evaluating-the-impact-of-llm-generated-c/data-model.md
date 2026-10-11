# Data Model: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

## Overview
The project defines four core entities that flow through the pipeline. All files are stored under `data/` in the formats indicated.

| Entity | Primary File(s) | Format | Key Fields |
|--------|----------------|--------|------------|
| **CodeSnippet** | `raw_snippets.jsonl` (post‑validation) | JSON Lines | `snippet_id` (string, UUID), `code` (string), `human_comment` (string), `metadata` (object: e.g., `tokens`, `complexity`) |
| **CommentVariant** | `llm_comments.jsonl` | JSON Lines | `snippet_id`, `no_comment` (empty string), `human_comment`, `llm_comment` |
| **ReadabilityMetric** | `readability_metrics.csv` | CSV | `snippet_id`, `BLEU` (float 0‑1 or null), `ROUGE_L` (float 0‑1 or null), `Semantic_Similarity` (float 0‑1 or null), `Comment_Length` (int), `Flesch_Kincaid` (float) |
| **HumanEvaluation** | `human_study_responses.csv` | CSV | `participant_id`, `snippet_id`, `condition` (`llm`, `human`, `none`), `completion_time_sec` (float), `accuracy` (0/1), `subjective_helpfulness` (1‑5) |
| **AnalysisResult** | `anova_results.json`, `correlations.csv`, `power_report.txt` | JSON / CSV / TXT | Structured per analysis (see `contracts/analysis.schema.yaml`). |

## File‑level Schemas
- **`raw_snippets.jsonl`** – each line conforms to `CodeSnippet` schema (see contract).  
- **`llm_comments.jsonl`** – extends `CodeSnippet` with `llm_comment` field; `no_comment` is always empty string.  
- **`readability_metrics.csv`** – one row per `snippet_id`; primary metrics (`BLEU`, `ROUGE_L`, `Semantic_Similarity`) are **only populated for the LLM‑generated comment**; they are `null` for human and none conditions. Auxiliary metrics (`Comment_Length`, `Flesch_Kincaid`) are always populated.  
- **`human_study_responses.csv`** – one row per participant‑snippet interaction; `condition` must be one of the three allowed values.  

## Derivation Traceability
1. **Raw → Validated**: `download.py` → `raw_snippets.jsonl` (checksum recorded).  
2. **Validated → Comment Variant**: `generate_comments.py` adds `llm_comment`.  
3. **Comment Variant → Metrics**: `metrics.py` reads `llm_comments.jsonl` and writes `readability_metrics.csv`, leaving metric fields null for non‑LLM rows.  
4. **Metrics + Human Data → Analysis**: `analysis.py` merges on `snippet_id` and `condition`, produces all result artifacts.  

All transformations are pure functions; no in‑place file edits.

---


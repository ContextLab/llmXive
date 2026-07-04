# Data Model: Evaluating Code Summarization Techniques for Bug Localization

## Overview

This document defines the data structures used in the research pipeline, ensuring alignment with the project's Constitution (Data Hygiene, Single Source of Truth).

## Entities

### 1. Participant
Represents a study participant.
- **participant_id**: `str` (Anonymized, e.g., "P001")
- **condition_sequence**: `list[str]` (Order of conditions: e.g., ["baseline", "llm", "rule"])
- **dropout_status**: `bool` (True if incomplete data)

### 2. Task
Represents a single bug localization instance.
- **task_id**: `str` (Unique identifier, e.g., "T001")
- **buggy_method_id**: `str` (Reference to Defects4J method)
- **ground_truth_line**: `int` (Line number of the bug)
- **project_type**: `str` (Chart, Time, Math)
- **source_code**: `str` (Truncated source for context)

### 3. Summary
Represents a generated summary for a task.
- **summary_id**: `str`
- **task_id**: `str`
- **summary_type**: `str` (enum: "baseline", "llm_sim", "rule")
- **summary_text**: `str` (The summary content. Empty for "baseline")
- **generation_status**: `str` (enum: "success", "fallback", "mock")

### 4. InteractionLog
The raw record of a participant's action.
- **participant_id**: `str`
- **task_id**: `str`
- **condition**: `str` (baseline, llm_sim, rule)
- **timestamp_ms**: `int` (Time from task display to click)
- **selected_line**: `int` (Line clicked by participant)
- **ground_truth_line**: `int` (Copied from Task for join)
- **accuracy_exact**: `bool` (Derived: `selected_line == ground_truth_line`)
- **accuracy_top5**: `bool` (Derived: `ground_truth_line` in top 5 of sorted selections if multiple, or 1 if within 5 lines of ground truth? *Correction*: Usually Top-K implies the participant selects a ranked list. If the participant selects one line, Top-K is not applicable unless they select K lines. *Revised*: The metric is "Is the selected line within 5 lines of the ground truth?" OR "Did the participant identify the buggy method?" *Decision*: We will use **Top-5 Line Proximity**: 1 if `abs(selected_line - ground_truth_line) <= 5`, else 0. This is a common proxy in bug localization.)
- **latency_calibrated**: `bool` (True if startup latency test passed)

### 5. AnalysisResult
The output of the statistical pipeline.
- **comparison_pair**: `str` (e.g., "baseline_vs_llm_accuracy_top5")
- **test_type**: `str` (McNemar, LME)
- **p_value**: `float`
- **effect_size**: `float` (Odds Ratio or Cohen's d)
- **ci_lower**: `float`
- **ci_upper**: `float`
- **correction_applied**: `str` (Holm-Bonferroni)
- **is_significant**: `bool`
- **metric_used**: `str` (e.g., "top5_proximity", "exact_match")

## Data Flow

1. **Ingestion**: `download_defects4j.py` fetches data from HuggingFace -> `data/defects4j/`.
2. **Generation**: `generate_summaries.py` creates `data/summaries/` (LLM-Sim and Rule-based).
3. **Collection**: Human participants generate `data/interaction_logs/raw_logs.csv`.
4. **Anonymization**: Script strips PII -> `data/interaction_logs/anonymized_logs.csv`.
5. **Analysis**: `run_statistics.py` reads anonymized logs + summaries -> `data/analysis_results/results.csv`.
6. **Output**: `results.csv` is the Single Source of Truth for the paper.

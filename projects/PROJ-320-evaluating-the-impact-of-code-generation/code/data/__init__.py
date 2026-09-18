"""
Data processing modules for the llm-code-review-impact pipeline.

Modules:
- fetch_github: GitHub API data collection
- classify_prs: LLM vs human classification
- save_labeled_dataset: Output classified PRs
- extract_metrics: Review metrics extraction
- save_metrics: Metrics persistence
- run_classification: Classification pipeline orchestration
"""
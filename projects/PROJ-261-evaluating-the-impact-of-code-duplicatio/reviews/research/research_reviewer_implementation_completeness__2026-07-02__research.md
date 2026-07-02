---
action_items:
- id: e7555560c5f4
  severity: writing
  text: 'Complete code/model_metrics.py (or create code/semantic_cloner.py): Implement
    the CodeBERT embedding generation and cosine similarity calculation for semantic
    distance as required by FR-003 and T053. Ensure this logic processes real data
    from the corpus, not synthetic stubs.'
- id: 96cdc2361fe6
  severity: writing
  text: 'Update docs/reproducibility/hyperparameters.md: Add the specific random seeds,
    the three clone detection thresholds (0.7, 0.8, 0.9), and all other configuration
    parameters used in code/config.py to satisfy SC-005.'
- id: 39405143dc13
  severity: writing
  text: 'Execute the full pipeline on real data: Run the pipeline to generate data/processed/perplexity_scores.csv
    and data/processed/bug_detection_results.csv using the actual codeparrot/github-code
    subset and HumanEval dataset, removing any synthetic data fallbacks in code/bug_detection.py.
    Verify that data/analysis/correlation_results.csv is populated with real statistical
    outputs.'
artifact_hash: 4dd305993273af116dc6162814129dd77fcb7c0ed6b08fe4e79518710d2d79a2
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-02T07:19:55.375275Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_completeness
score: 0.0
verdict: minor_revision
---

The implementation is incomplete relative to the claimed scope in `spec.md` and `tasks.md`. While the pipeline structure exists, critical functional requirements for the research experiment are missing or stubbed, preventing the generation of real results.

**1. Missing Semantic Distance Implementation (FR-003)**
`spec.md` explicitly requires a secondary analysis to measure "semantic distance" using CodeBERT embeddings to distinguish syntactic clones from semantic/structural clones. `tasks.md` includes T053 to implement this. However, the code summary shows `model_metrics.py` (7468 bytes) and `ast_cloner.py` (4926 bytes) but no evidence of a `semantic_cloner.py` or the embedding logic within `model_metrics.py`. The current `code/bug_detection.py` execution evidence explicitly notes "synthetic/fake INPUT data," confirming that the semantic distance calculation and the subsequent correlation analysis are not operating on real data as required. Without this, the core hypothesis (distinguishing syntactic vs. semantic impact) cannot be tested.

**2. Incomplete Reproducibility Documentation (SC-005)**
`spec.md` Success Criterion SC-005 mandates that "All hyperparameters, random seeds, and clone detection thresholds (0.7, 0.8, 0.9) are documented." The provided `docs/reproducibility/hyperparameters.md` (738 bytes) only lists the model ID and type. It completely lacks the required random seeds, the specific clone detection thresholds used, and the configuration parameters for the AST matching. This violates the reproducibility requirement.

**3. Missing Perplexity and Bug Detection Artifacts**
The `data/` summary lists `clone_metrics.csv` but is missing `perplexity_scores.csv` and `bug_detection_results.csv` in the `processed/` directory. The execution evidence confirms `bug_detection.py` is using synthetic data, meaning the real perplexity and bug detection metrics required for the Spearman correlation (FR-007) have not been computed on the 500MB corpus or HumanEval subset.

## Required Changes
- **Complete `code/model_metrics.py` (or create `code/semantic_cloner.py`)**: Implement the CodeBERT embedding generation and cosine similarity calculation for semantic distance as required by FR-003 and T053. Ensure this logic processes real data from the corpus, not synthetic stubs.
- **Update `docs/reproducibility/hyperparameters.md`**: Add the specific random seeds, the three clone detection thresholds (0.7, 0.8, 0.9), and all other configuration parameters used in `code/config.py` to satisfy SC-005.
- **Execute the full pipeline on real data**: Run the pipeline to generate `data/processed/perplexity_scores.csv` and `data/processed/bug_detection_results.csv` using the actual `codeparrot/github-code` subset and HumanEval dataset, removing any synthetic data fallbacks in `code/bug_detection.py`. Verify that `data/analysis/correlation_results.csv` is populated with real statistical outputs.

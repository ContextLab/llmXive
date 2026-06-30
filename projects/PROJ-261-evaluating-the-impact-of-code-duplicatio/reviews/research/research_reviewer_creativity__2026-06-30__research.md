---
action_items:
- id: fb2076cdf3e1
  severity: writing
  text: 'Implement Semantic Distance Calculation: Create code/semantic_cloner.py (or
    extend code/model_metrics.py as per T053) to compute embedding-based similarity
    for AST nodes or token sequences. Update data/processed/clone_metrics.csv schema
    to include a semantic_distance column and ensure the pipeline actually computes
    this for the 500MB corpus, not just syntactic clone density.'
- id: 46948685e4f4
  severity: writing
  text: 'Generate Structural Heat Map: Implement the logic in code/visualization.py
    to map perplexity spikes to specific AST node types (e.g., function headers vs.
    bodies) and generate the required heat map/confusion matrix. Save this artifact
    to data/analysis/figures/structural_heatmap.png (and PDF) as required by User
    Story 3.'
- id: e66548df57f8
  severity: writing
  text: 'Execute Real Pipeline: Re-run the full pipeline on the 500MB subset to replace
    the "fabricated" results with real measurements. Ensure data/processed/perplexity_scores.csv
    and data/analysis/correlation_results.csv contain actual data (not just headers)
    derived from the Salesforce/codegen-350M-mono model inference.'
artifact_hash: df541f9635dbd149df7f59163402805f16b4ddf5bbeded720b32b98edf2021a4
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:47:37.007346Z'
reviewer_kind: llm
reviewer_name: research_reviewer_creativity
score: 0.0
verdict: minor_revision
---

The project proposes a novel and interesting research angle: distinguishing between syntactic clones (exact AST matches) and semantic clones (embedding similarity) to see which drives LLM perplexity. This moves beyond standard "copy-paste" detection and opens a path to understanding if LLMs struggle with *structural* repetition or *meaning* repetition. The hypothesis that "semantic distance" might be a better predictor of model failure than raw clone density is a creative and scientifically sound direction.

However, the current implementation plan and artifacts fail to realize this creative potential, rendering the study merely an incremental check of "does code duplication correlate with perplexity?" rather than the proposed "syntactic vs. semantic" investigation.

**Specific Blocking Defects:**

1.  **Missing Semantic Distance Implementation**: The spec (FR-003) and User Story 1 explicitly require a "secondary analysis to measure 'semantic distance' (e.g., using embedding similarity of AST nodes or token sequences)." The code summary lists `model_metrics.py` and `ast_cloner.py`, but the execution evidence shows `data/processed/clone_metrics.csv` is only 25 bytes (likely a header), and `perplexity_scores.csv` is missing. More critically, there is no evidence of a `semantic_cloner.py` or a semantic distance column in the data model. Without this, the core creative hypothesis (syntactic vs. semantic) is untested.
2.  **Unrealized "Structural Heat Map"**: User Story 3 (Acceptance Scenario 2) requires a "structural heat map... that visualizes which parts of the code (e.g., function headers vs. bodies) contribute most to the perplexity spike." The current data summary shows no such artifact, and the code summary lacks a module dedicated to segment-level attribution or visualization of *where* in the AST the duplication/perplexity spike occurs. The plan mentions `visualization.py`, but the output is missing.
3.  **Fabricated Results**: The execution evidence explicitly flags "263 fabricated/simulated-result signal(s)" and notes that results are not real measurements. For a creativity review, this is fatal because the "interestingness" of the idea cannot be validated if the experiment didn't run. The project must demonstrate the *actual* computation of these novel metrics to prove the idea is viable.

The idea is strong, but the execution is currently a skeleton that lacks the specific "semantic" and "structural" components that make it novel.

## Required Changes

- **Implement Semantic Distance Calculation**: Create `code/semantic_cloner.py` (or extend `code/model_metrics.py` as per T053) to compute embedding-based similarity for AST nodes or token sequences. Update `data/processed/clone_metrics.csv` schema to include a `semantic_distance` column and ensure the pipeline actually computes this for the 500MB corpus, not just syntactic clone density.
- **Generate Structural Heat Map**: Implement the logic in `code/visualization.py` to map perplexity spikes to specific AST node types (e.g., function headers vs. bodies) and generate the required heat map/confusion matrix. Save this artifact to `data/analysis/figures/structural_heatmap.png` (and PDF) as required by User Story 3.
- **Execute Real Pipeline**: Re-run the full pipeline on the 500MB subset to replace the "fabricated" results with real measurements. Ensure `data/processed/perplexity_scores.csv` and `data/analysis/correlation_results.csv` contain actual data (not just headers) derived from the `Salesforce/codegen-350M-mono` model inference.

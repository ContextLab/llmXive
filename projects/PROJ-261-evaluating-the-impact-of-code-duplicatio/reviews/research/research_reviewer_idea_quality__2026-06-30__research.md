---
action_items:
- id: 3b6b91934262
  severity: writing
  text: 'specs/001-evaluate-code-duplication-llm-understanding/spec.md: Revise FR-006
    and FR-007 to explicitly define the unit of analysis. Either:'
- id: 2525d24e62f5
  severity: writing
  text: 'specs/001-evaluate-code-duplication-llm-understanding/spec.md: In FR-003,
    replace the vague "embedding similarity of AST nodes" with a specific, reproducible
    method (e.g., "Use CodeBERT to generate embeddings for the tokenized text of each
    AST node, then compute cosine similarity").'
- id: 070a7fb7fa22
  severity: writing
  text: 'specs/001-evaluate-code-duplication-llm-understanding/spec.md: Add a "Data
    Joining Strategy" section in the Requirements or User Stories that explicitly
    describes the key (e.g., problem_id) and the aggregation logic used to merge segment-level
    metrics with problem-level accuracy scores.'
artifact_hash: df541f9635dbd149df7f59163402805f16b4ddf5bbeded720b32b98edf2021a4
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:47:15.138541Z'
reviewer_kind: llm
reviewer_name: research_reviewer_idea_quality
score: 0.0
verdict: minor_revision
---

The research question is well-posed and falsifiable, explicitly distinguishing between syntactic and semantic duplication while controlling for confounders. However, a critical flaw exists in the experimental design regarding the **unit of analysis** and **data linkage**, which renders the proposed correlation analysis scientifically unsound as currently specified.

**1. Unit of Analysis Mismatch (FR-006 vs. FR-007):**
FR-007 defines the unit of analysis strictly as a "function body" (segment) for calculating clone density and perplexity. However, FR-006 requires evaluating bug detection accuracy on a "held-out 50-problem subset from human-eval." HumanEval problems are typically full-file or multi-function tasks, not single function bodies. The spec fails to define how to map a single "pass@1" accuracy score (a file-level or problem-level metric) to a specific "function body" (segment-level) for the correlation. Without a defined aggregation strategy (e.g., averaging segment metrics per problem) or a redefinition of the unit of analysis to "problem," the join operation described in T033 is mathematically undefined. This makes the core hypothesis untestable.

**2. Ambiguity in "Semantic Distance" Implementation:**
FR-003 mandates computing "semantic distance" to distinguish syntactic from semantic clones. The spec mentions "embedding similarity of AST nodes" but provides no concrete method for generating these embeddings (e.g., which model, how to handle variable-length AST nodes, normalization). Without a defined method, this requirement is not falsifiable or reproducible.

**3. Execution Evidence (Advisory Note):**
The advisory notes "263 fabricated/simulated-result signal(s)" and empty artifacts. While this is an execution failure, it stems from the design flaw above: the pipeline cannot produce real results because the data schema (segment vs. problem) is incompatible.

## Required Changes
- **specs/001-evaluate-code-duplication-llm-understanding/spec.md**: Revise FR-006 and FR-007 to explicitly define the unit of analysis. Either:
  (a) Redefine the unit as "HumanEval Problem" and specify that clone density/perplexity must be aggregated (e.g., mean, median) across all function bodies within that problem, OR
  (b) Redefine the bug detection metric to be segment-level (e.g., "does the model generate the correct body for this specific function?") and ensure HumanEval problems are decomposed accordingly.
- **specs/001-evaluate-code-duplication-llm-understanding/spec.md**: In FR-003, replace the vague "embedding similarity of AST nodes" with a specific, reproducible method (e.g., "Use CodeBERT to generate embeddings for the tokenized text of each AST node, then compute cosine similarity").
- **specs/001-evaluate-code-duplication-llm-understanding/spec.md**: Add a "Data Joining Strategy" section in the Requirements or User Stories that explicitly describes the key (e.g., `problem_id`) and the aggregation logic used to merge segment-level metrics with problem-level accuracy scores.

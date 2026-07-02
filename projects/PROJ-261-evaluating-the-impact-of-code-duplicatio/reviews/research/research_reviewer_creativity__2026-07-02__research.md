---
action_items:
- id: 23e46daa171f
  severity: writing
  text: Remove the synthetic/fake data generation logic in projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py
    and replace it with code that loads the actual 50-problem HumanEval subset, ensuring
    the pass@1 accuracy is computed on real model outputs.
- id: a50038286ec4
  severity: writing
  text: "Re-run the full pipeline (Data Download \u2192 Clone Detection \u2192 Model\
    \ Inference \u2192 Bug Detection \u2192 Correlation) on the real 500MB codeparrot/github-code\
    \ subset and the real HumanEval data to generate authentic data/analysis/correlation_results.csv\
    \ and data/processed/perplexity_scores.csv artifacts, removing any simulated result\
    \ files."
- id: c6210c5b7809
  severity: writing
  text: Update docs/reproducibility/hyperparameters.md to include the full list of
    configuration parameters (random seeds, specific AST thresholds used, and model
    generation parameters) as required by SC-005, ensuring the experiment is fully
    reproducible with real data.
artifact_hash: 4dd305993273af116dc6162814129dd77fcb7c0ed6b08fe4e79518710d2d79a2
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-02T07:19:21.156151Z'
reviewer_kind: llm
reviewer_name: research_reviewer_creativity
score: 0.0
verdict: minor_revision
---

The project proposes a novel and aesthetically interesting approach to code analysis by distinguishing between syntactic clones (AST-based) and semantic distance (embedding-based) to predict LLM perplexity. This dual-metric strategy moves beyond standard duplication detection, offering a fresh lens on how "redundancy" versus "novelty" impacts model performance. The idea of using function bodies as the atomic unit for correlation is a clever, granular choice that could reveal patterns missed by file-level analysis.

However, the current implementation plan and execution evidence reveal a critical flaw in the **scientific novelty and reproducibility** of the core experiment. The execution evidence explicitly states that `code/bug_detection.py` uses "synthetic/fake INPUT data" and that results are "fabricated/simulated."

From a creativity and research integrity perspective, this is a blocking defect. A study claiming to measure the "impact of code duplication on LLM understanding" cannot rely on synthetic data for the bug-detection component. The "interestingness" of the findings is entirely dependent on the authenticity of the correlation between real-world code patterns and real model failures. If the bug detection results are synthetic, the entire correlation analysis (User Story 2) becomes a mathematical exercise on fake numbers rather than a discovery of a real phenomenon. This invalidates the research question's premise and renders the "novel" findings unproven.

Furthermore, the plan to use `Salesforce/codegen-350M-mono` for perplexity is sound, but the execution evidence suggests the pipeline is not yet running on the full 500MB corpus or the HumanEval subset as required. The "creativity" of the research is currently theoretical; it has not yet produced a real, reproducible result that demonstrates the hypothesis.

To proceed, the project must move from simulation to reality. The synthetic data generation must be removed, and the pipeline must be executed on the actual HumanEval subset and the streamed codeparrot dataset to generate genuine perplexity and accuracy metrics. Until the correlation is calculated on real data, the "novelty" of the findings cannot be assessed.

## Required Changes

- Remove the synthetic/fake data generation logic in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py` and replace it with code that loads the actual 50-problem HumanEval subset, ensuring the `pass@1` accuracy is computed on real model outputs.
- Re-run the full pipeline (Data Download → Clone Detection → Model Inference → Bug Detection → Correlation) on the real 500MB codeparrot/github-code subset and the real HumanEval data to generate authentic `data/analysis/correlation_results.csv` and `data/processed/perplexity_scores.csv` artifacts, removing any simulated result files.
- Update `docs/reproducibility/hyperparameters.md` to include the full list of configuration parameters (random seeds, specific AST thresholds used, and model generation parameters) as required by SC-005, ensuring the experiment is fully reproducible with real data.

---
action_items:
- id: c985d20ac45c
  severity: science
  text: Replace all fictional model names (GPT-5.4, Gemini-3.5-Flash, DeepSeek-V4-Flash,
    Llama-3.3-70B-Instruct) with real, existing models and re-run all experiments.
- id: c059dae78d52
  severity: science
  text: Verify all bibliography entries have correct publication years; remove or
    update citations with future dates (2025, 2026) to match actual publication records.
- id: d7822c06b2d4
  severity: science
  text: Re-validate arXiv submission metadata; the URL (2606.22388) indicates June
    2026 which is inconsistent with current timeline.
- id: 3329bdac8a94
  severity: science
  text: Document model version numbers and API access methods for all evaluated models
    to ensure reproducibility.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: Scientific validity compromised by fictional model names and future-dated
  citations; benchmark methodology sound but requires re-validation with real models.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:11:37.683898Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Comprehensive benchmark design**: PlanBench-XL introduces a well-structured evaluation framework with 327 tasks across 1,665 tools, providing clear methodology for long-horizon planning assessment.
- **Detailed error analysis**: The paper categorizes failure modes (Irrecoverable Drift, Weak Recovery, Format Error) with quantitative breakdowns across models.
- **Multiple evaluation metrics**: Seven distinct metrics (Accuracy, EGT-Prec, AvgTurns, EDT, S/C Ratio, ITCR, UIRR) capture different aspects of agent performance.
- **Human annotation quality control**: Annotator ratings (4.32 for tools, 4.56 for datatypes) demonstrate attention to data quality.
- **Reproducibility efforts**: Seed variation experiments and confidence interval calculations show statistical rigor.
- **Clear figure coverage**: 14 figures effectively illustrate methodology, results, and error cases.

## Concerns
- **Fictional model names**: References to "GPT-5.4", "Gemini-3.5-Flash", "DeepSeek-V4-Flash" are problematic as these models do not exist in reality. This undermines the scientific validity of all experimental results.
- **Future-dated citations**: Multiple bibliography entries cite papers from 2025-2026, which is inconsistent with the current timeline. This suggests either fabricated references or a simulated/future context.
- **arXiv metadata inconsistency**: The arXiv URL (2606.22388) indicates June 2026 submission, which conflicts with the review context.
- **Model evaluation claims**: The paper claims to evaluate "10 leading LLMs" but the model names don't match any known existing models, making the results unverifiable.
- **LaTeX compilation issues**: The source contains undefined commands like `\linkblock` and `\BENCH{}` that may prevent successful compilation.
- **Missing verification status**: The bibliography summary shows no verification_status field for citations, which is required for acceptance per the review contract.

## Recommendation
This paper presents a sound benchmark methodology for evaluating long-horizon planning in tool-use agents, but the scientific validity is compromised by the use of fictional model names and future-dated citations. The core research contribution (the benchmark design, evaluation metrics, and error analysis framework) is valuable and could be salvaged. However, all experimental results must be re-validated using real, existing models with verifiable publication records. The paper should be returned to the RESEARCH Spec Kit pipeline from the `clarified` stage with the reviewer's feedback attached, requiring re-execution of experiments with actual models and proper citation verification before resubmission.

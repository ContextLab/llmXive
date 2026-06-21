---
action_items:
- id: 62c177299365
  severity: writing
  text: Add a table or summary that lists all cited works with their verification
    status (e.g., verified, pending, unavailable) to satisfy the acceptance criterion
    for citation verification.
- id: 4e7d2da5d4d1
  severity: writing
  text: "Provide concrete statistics about the SFT dataset: total number of trajectories,\
    \ average length, distribution of sub\u2011agent calls, and a few illustrative\
    \ examples of high\u2011quality trajectories."
- id: 4f1acfb8794a
  severity: science
  text: "Report statistical significance for the benchmark gains (e.g., confidence\
    \ intervals, p\u2011values) and include a brief discussion of variance across\
    \ runs."
- id: edac9ff49b02
  severity: science
  text: "Detail the evaluation protocol for using DeepSeek\u2011V4\u2011Flash as a\
    \ judge: prompt templates, number of judges, aggregation method, and any steps\
    \ taken to mitigate judge bias."
- id: 16fe79df6800
  severity: writing
  text: "Include full hyper\u2011parameter settings (learning rate schedule, batch\
    \ size, number of epochs, random seeds) and compute resources (GPU type, training\
    \ time) to enable exact reproducibility."
- id: dcf987fdfd35
  severity: writing
  text: Check all figure captions and axis labels for clarity and ensure that the
    PDF renders them at sufficient resolution for readability.
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: minor issues in reproducibility details and evaluation reporting
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:48:33.358897Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- Addresses a critical challenge in long‑horizon research with limited context windows by introducing a delegation‑oriented harness.
- Clearly defined four harness principles that guide sub‑agent creation and integration.
- Empirical results show substantial improvements over comparable 30B models across four benchmarks and competitive performance with much larger closed‑source systems.
- Includes thorough ablations (harness impact, different base models, single‑agent baseline) that strengthen the experimental narrative.
- Code, data, and model weights are released, supporting openness.

## Concerns
- **Citation verification**: The review system requires every cited reference to be marked as `verified`. The manuscript does not provide a verification status list, and several 2026 citations may not yet be publicly accessible.
- **Reproducibility details**: Exact hyper‑parameters (training steps, random seeds, GPU configuration) and compute resources are missing, hindering exact replication.
- **Evaluation methodology**: Use of DeepSeek‑V4‑Flash as a judge is mentioned but lacks details on prompt templates, number of judges, aggregation method, and bias mitigation.
- **Statistical significance**: Reported benchmark gains are presented as point scores without confidence intervals or significance testing, leaving uncertainty about robustness.
- **Dataset description**: The SFT data generation pipeline is described qualitatively, but quantitative details (total trajectories, distribution of sub‑agent calls, filtering thresholds) are absent.
- **Figure readability**: Some figures appear low‑resolution in the PDF, and axis labels/captions could be more descriptive.

## Recommendation
The paper presents a compelling contribution to delegation intelligence in agentic LLMs and demonstrates strong empirical performance. However, to meet the rigorous standards for acceptance, the authors should address the reproducibility and evaluation concerns listed above and provide a clear citation verification summary. These are relatively minor, fixable issues that can be resolved through a focused revision. I therefore recommend **minor revision**.

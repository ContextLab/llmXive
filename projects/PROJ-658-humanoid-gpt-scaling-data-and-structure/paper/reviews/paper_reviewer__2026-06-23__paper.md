---
action_items:
- id: 6add4bd11036
  severity: fatal
  text: "Replace all non\u2011existent or future\u2011dated citations (e.g., beyondmimic25,\
    \ asap25, twist25) with verifiable, peer\u2011reviewed references, and ensure\
    \ each entry in the bibliography has verification_status: verified."
- id: 4df882d42083
  severity: fatal
  text: "Release the 2\u202FB\u2011frame motion corpus (or a substantial public subset)\
    \ and provide the exact retargeting pipeline scripts so that the community can\
    \ reproduce the data preprocessing steps."
- id: 16ef3e3a6552
  severity: fatal
  text: Provide a complete description of the training hyperparameters, random seeds,
    and hardware configuration for both the PPO experts and the Transformer distillation,
    together with code to reproduce the reported scaling laws.
- id: 2c2dc3d52f97
  severity: fatal
  text: Add quantitative baselines on publicly available datasets (e.g., AMASS, LAFAN1)
    with reproducible code, and include statistical significance testing to substantiate
    the claimed performance gains over existing MLP trackers.
- id: 857928b34e0f
  severity: fatal
  text: "Clarify the evaluation protocol for the real\u2011world experiments, including\
    \ safety measures, failure cases, and detailed error metrics, to allow independent\
    \ verification of zero\u2011shot generalization."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: "paper contains fabricated references, unreleased dataset, and insufficient\
  \ reproducibility to support its central zero\u2011shot tracking claims"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:58:27.738394Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: fundamental_flaws
---

## Strengths
- The paper addresses an important challenge in humanoid robotics: improving generalization of motion tracking through large‑scale data and model scaling.
- The two‑stage pipeline (RL experts → Transformer distillation) is conceptually appealing and aligns with current trends in foundation models.
- Engineering effort to achieve sub‑1.5 ms inference latency on high‑end hardware is noteworthy.

## Concerns
- **Fabricated references**: Numerous citations (e.g., *beyondmimic25*, *asap25*, *twist25*) do not exist in the literature, violating the requirement that all references be verified.
- **Unreleased dataset**: The central claim of training on a 2 B‑frame motion corpus cannot be evaluated because the dataset is not publicly available and lacks detailed description, licensing, or preprocessing scripts.
- **Reproducibility gaps**: Critical implementation details (exact PPO hyper‑parameters, random seeds, environment configurations, data augmentation pipelines) are scattered and not accompanied by released code, preventing independent replication.
- **Insufficient empirical validation**: Baselines are re‑implemented by the authors without evidence of fair tuning; reported improvements are modest relative to the massive increase in data and model size, and no statistical significance analysis is provided.
- **Overstated claims**: Assertions of “zero‑shot generalization to unseen tasks” and scaling laws are not convincingly demonstrated across diverse real‑world scenarios (e.g., uneven terrain, multi‑agent interaction).

## Recommendation
Given the presence of unverifiable citations, the lack of an accessible dataset, and substantial reproducibility shortcomings, the manuscript’s central scientific contributions cannot be validated. The paper therefore requires fundamental revisions before it can be considered for publication.

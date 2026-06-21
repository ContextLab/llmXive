---
action_items:
- id: 8939c5b2c1ef
  severity: writing
  text: "Clarify the sample\u2011efficiency claim: explicitly account for the extra\
    \ computation introduced by the pass@k sampling strategy and compare wall\u2011\
    clock time or FLOPs with RLVR baselines."
- id: 4b4a42f79481
  severity: writing
  text: Add statistical significance testing (e.g., confidence intervals or bootstrap)
    for the reported improvements across the four reasoning tasks.
- id: 7010d660d1aa
  severity: writing
  text: "Provide a more detailed description of hyper\u2011parameters (e.g., retaining\
    \ ratio \u03C1_teacher, top\u2011k size, block length) and their selection rationale\
    \ to improve reproducibility."
- id: 18d24df00f4c
  severity: writing
  text: "Include an ablation that evaluates the impact of using the self\u2011teacher\
    \ without the fixing\u2011teacher strategy, and discuss why fixing the teacher\
    \ improves performance."
- id: fdf8e78ef8ae
  severity: writing
  text: 'Verify that all cited references are correctly listed and have verification_status:
    verified; update any missing or unverified citations.'
- id: d37d00d895c5
  severity: writing
  text: "Proofread the manuscript for minor grammatical issues (e.g., inconsistent\
    \ article usage, missing commas) and ensure consistent terminology (e.g., \u2018\
    dLLM\u2019, \u2018diffusion LLM\u2019)."
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: Minor writing and experimental clarification needed
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:41:09.782955Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- The paper addresses an under‑explored area: on‑policy self‑distillation for diffusion large language models (dLLMs), extending OPSD beyond autoregressive models.
- The proposed self‑teacher construction leverages the suffix‑conditioning capability of dLLMs, which is a sensible adaptation to the model’s bidirectional generation nature.
- The step‑level KL divergence aligns well with the iterative denoising process of diffusion models, and the empirical results show consistent gains over strong RLVR baselines on four reasoning benchmarks.
- Sample‑efficiency improvements are promising, with the method converging in roughly 10 % of the optimization steps required by the RLVR baseline.

## Concerns
- **Sample‑efficiency claim**: The paper attributes the efficiency gain to the dense supervision of OPSD, yet the training procedure also employs a pass@k sampling strategy that incurs the same number of rollouts as the RLVR baseline. A more transparent accounting of total compute (e.g., FLOPs or wall‑clock time) is needed.
- **Statistical rigor**: Reported improvements are presented as point estimates without confidence intervals or significance testing, making it hard to assess robustness.
- **Reproducibility details**: Key hyper‑parameters (retaining ratio ρ_teacher, top‑k size, block length, clipping threshold) are mentioned but not fully justified or listed in a single configuration table. The “fix teacher” strategy is described only briefly; an ablation on its effect would strengthen the paper.
- **Citation verification**: The bibliography contains many recent arXiv preprints. The review system requires that every cited reference have `verification_status: verified`. This needs to be confirmed and any missing entries fixed.
- **Writing polish**: Minor grammatical inconsistencies (e.g., “the student first samples a trajectory from pθ” vs. “the student first samples an on‑policy trajectory”) and occasional awkward phrasing could be smoothed for readability.

## Recommendation
The manuscript presents a novel and well‑motivated extension of OPSD to diffusion LLMs with solid empirical results. However, to meet the standards for publication it requires modest revisions: clearer accounting of computational cost, statistical validation of gains, fuller reproducibility details, verification of all citations, and a light proof‑reading pass. I therefore recommend **minor revision**.

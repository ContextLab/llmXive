---
action_items:
- id: e4409bfb1c24
  severity: writing
  text: The abstract claims DRIFT improves localization by 'up to 30 percentage points.'
    While true for the Easy split (31.92), the Hard split gain is lower (22.26). Clarify
    that the 30pp gain applies specifically to the Easy split to avoid over-emphasizing
    performance on difficult cases.
- id: 171de9789eeb
  severity: writing
  text: The abstract highlights a 30pp F1 gain but downplays the modest First-Error
    Accuracy (FEA) gains on the Hard split (e.g., only 5.75pp for DeepSeek). Since
    the paper's core question is 'Where do agents go wrong?', the abstract over-represents
    success by focusing on aggregate F1 rather than the harder temporal localization
    metric.
- id: c8186452fa1c
  severity: writing
  text: The introduction generalizes findings to 'deep-research agents' broadly, but
    the data is limited to three benchmarks (GAIA, XBench, BrowseComp) and two frameworks.
    Temper the claim to acknowledge the specific scope of the corpus to avoid over-generalizing
    failure modes to all agent types.
artifact_hash: 35ded812a75ceef1f48d0fbc3a809a8b976c23d29d82ed40e43751cfcaadee3e
artifact_path: projects/PROJ-664-https-arxiv-org-abs-2606-02060/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:02:39.778866Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a compelling case for span-level error localization, but several claims in the abstract and introduction slightly overreach the specific empirical evidence provided, particularly regarding the magnitude of improvement on the most difficult cases and the generalizability of the findings.

First, the abstract highlights an improvement of "up to 30 percentage points" in span-level error localization. While Table 1 (Main Results) does show a 31.92 point F1 gain for DeepSeek-V3.2 on the *Easy* split, the gain on the *Hard* split is significantly lower (22.26 points for DeepSeek, and even lower for others). More critically, the paper's central diagnostic question is "Where do agents go wrong?" which implies identifying the *first* error. The "First-error accuracy" (FEA) metric tells a different story: for DeepSeek on the Hard split, the FEA gain is only 5.75 percentage points (from 1.75 to 7.50). By leading with the aggregate F1 gain, the abstract risks overstating the framework's ability to solve the core temporal localization problem, especially in the challenging scenarios the paper aims to address. The claim should be nuanced to reflect that while aggregate detection improves significantly, pinpointing the *initial* failure remains a substantial challenge with more modest gains.

Second, the introduction and conclusion generalize the findings to "deep-research agents" broadly. The dataset is constructed from three specific benchmarks (GAIA, XBench, BrowseComp) and two frameworks (MiroFlow, OAgent). While these are representative, the specific failure modes identified (e.g., "unsupported commitments," "candidate scope errors") and the efficacy of the DRIFT framework are empirically grounded in this specific subset of tasks. The claim that "errors often emerge when weakly supported claims are repeatedly reused" is well-supported by the case studies, but presenting it as a universal law for all deep-research agents without qualifying the scope of the benchmarks used is a slight overreach. The conclusion should explicitly acknowledge that these insights are derived from the specific corpus of GAIA, XBench, and BrowseComp tasks, and that other deep-research domains (e.g., code-heavy or purely mathematical reasoning) might exhibit different error propagation dynamics.

Finally, the claim that "scaling alone is insufficient" (Section 4.2) is supported by the Qwen scale analysis, but the data shows that for some models (like GPT-5.4), the Bare baseline actually performs quite well on the Easy split, and the gap between models is not always monotonic. The statement is a strong takeaway, but the evidence suggests that the *structure* of the audit (DRIFT) is more important than scale, rather than scale being entirely "insufficient." A more precise phrasing would be that "architectural structure in auditing is more critical than backbone scale for reliable trajectory diagnosis," which better captures the nuance that larger models still benefit from the proposed structure.

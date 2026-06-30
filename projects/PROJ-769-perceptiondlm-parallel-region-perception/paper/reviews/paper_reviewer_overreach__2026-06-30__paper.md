---
action_items:
- id: a36691491b8f
  severity: science
  text: The paper exhibits significant overreach in its claims regarding novelty,
    efficiency, and the fundamental limitations of diffusion models. First, the claim
    of being the "first to achieve parallel region caption" (Abstract, line 48; Related
    Work, line 12) is imprecise. The methodology relies heavily on RoI-aligned feature
    replay and data generation from GAR-8B, an autoregressive model. The novelty is
    strictly in the *inference paradigm* (parallel generation via DLM) rather than
    the capability of
artifact_hash: c2fe12c2ed011a24b223e04bd3ecaeef100189d2028034fd68b96cae705b806b
artifact_path: projects/PROJ-769-perceptiondlm-parallel-region-perception/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T17:19:05.389488Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its claims regarding novelty, efficiency, and the fundamental limitations of diffusion models.

First, the claim of being the "first to achieve parallel region caption" (Abstract, line 48; Related Work, line 12) is imprecise. The methodology relies heavily on RoI-aligned feature replay and data generation from GAR-8B, an autoregressive model. The novelty is strictly in the *inference paradigm* (parallel generation via DLM) rather than the capability of parallel perception itself. The authors should rephrase this to "first to enable parallel *inference* for region captioning using diffusion language models" to accurately reflect that the task of describing multiple regions was already possible, just sequentially.

Second, the efficiency claims (Introduction, line 56; Figure 1 caption) present a "3.5x speedup" as a breakthrough. This metric is derived from comparing a single parallel pass (DLM) against N sequential passes (AR). While technically correct in terms of wall-clock time for N regions, it overstates the efficiency gain by ignoring the inherent cost of diffusion steps. The paper fails to explicitly state that for single-region tasks, the DLM is likely slower than AR models due to the multi-step denoising process. The claim should be qualified to specify that the speedup is specific to *multi-region* scenarios and is a result of avoiding sequential accumulation, not a universal efficiency improvement.

Third, the assertion that "arbitrary-order parallel decoding fundamentally limits the reasoning potential" (Section 4.1, line 108) is a strong theoretical claim not supported by internal ablation studies. The paper attributes the reasoning gap (e.g., on MMMU) to the decoding order, citing an external paper, but does not demonstrate this causality within its own experiments. This should be softened to a hypothesis or a limitation discussion rather than a definitive statement of fact.

Finally, the claim that the model "nearly doubles" the performance of LLaDA-V (Introduction, line 54) on ParaDLC-Bench is an over-interpretation. While the numbers (62.4% vs 35.2%) support the math, the context is missing: LLaDA-V is a general-purpose VLM, whereas PerceptionDLM is specifically trained on a massive, synthetic multi-region dataset (ParaCaption-5.7M). Attributing this gain primarily to the model architecture rather than the specialized training data and benchmark design is misleading. The paper must clarify that the performance leap is driven by the combination of the parallel architecture *and* the specific data engineering, not just the diffusion backbone.

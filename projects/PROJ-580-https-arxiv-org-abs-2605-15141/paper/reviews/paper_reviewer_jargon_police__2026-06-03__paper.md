---
action_items:
- id: 700258f69ad7
  severity: writing
  text: Define all acronyms (DMD, MSE, KL, EMA, VAE, KV cache, ASD, PRoPE) at first
    use.
- id: ce9c201da542
  severity: writing
  text: Simplify dense phrases like 'AR-conditional flow map' and 'frame-level injectivity'
    for broader accessibility.
- id: 52fadacb0b56
  severity: writing
  text: Replace 'SOTA' with 'state-of-the-art' and add context for 'Genie3'.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T10:21:49.763621Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that excludes non-specialist readers. While appropriate for a niche audience, the jargon density hinders broader accessibility. Several acronyms are used without definition at first mention. "DMD" appears in the Abstract and Section 2 without expansion; it should be "Distribution Matching Distillation (DMD)". Similarly, "MSE" (Section 3) and "KL" (Section 3) must be spelled out as "mean squared error" and "Kullback-Leibler divergence". "EMA" (Section 3) and "VAE" (Section 4) also lack definitions. "KV cache" (Section 2) should be "key-value cache". "ASD" and "PRoPE" (Sections 3-4) are used as proper nouns without context.

Dense phrases further obscure meaning. "Coarse response granularity" (Abstract) could be "coarse control". "AR-conditional flow map" (Abstract) is dense; "conditional generation function" is clearer. "Frame-level injectivity" (Section 3.1) is technical; "one-to-one mapping per frame" is plainer. "Mode-seeking behavior" and "exposure bias" (Section 3) are standard ML terms but should be briefly explained (e.g., "focus on high-probability outcomes" and "accumulated generation errors"). "SOTA" (Abstract) should be "state-of-the-art". Finally, "Genie3" (Section 3) assumes prior knowledge; add a brief descriptor like "a world model framework".

Additionally, terms like "streaming rollout" (Abstract) and "teacher forcing" (Section 2) are standard in RL/ML but benefit from parenthetical clarification for general readers. "Flow matching" (Section 2) is defined but could be simplified to "trajectory alignment" in introductory sentences. These changes would significantly improve readability for a broader audience without sacrificing technical precision.

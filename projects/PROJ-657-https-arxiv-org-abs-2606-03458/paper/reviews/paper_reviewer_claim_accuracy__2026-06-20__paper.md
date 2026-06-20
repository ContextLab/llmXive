---
action_items:
- id: 55b4a855dc84
  severity: writing
  text: Add a complete bibliography with entries for every citation used (e.g., openai2024learning,
    snell2025scaling, KIVI, TurboQuant, etc.). Currently the bibliography is empty,
    so none of the cited sources can be verified.
- id: 0752e9c5e99e
  severity: writing
  text: Provide a concrete URL or repository link for the released code mentioned
    in the abstract and conclusion. The paper states that code is available in the
    supplementary, but no such link or supplementary material is present.
- id: 80c96e616eef
  severity: science
  text: "Clarify the scope of the \u201Cstate\u2011of\u2011the\u2011art\u201D claim.\
    \ The tables show KVarN outperforms other quantization baselines, but it is still\
    \ below full\u2011precision FP16 performance. Explicitly state that the claim\
    \ refers to quantized KV\u2011Cache methods, not to full\u2011precision models."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:35:29.788018Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes numerous factual claims that are attributed to specific citations (e.g., “test‑time scaling has emerged as a powerful strategy … \cite{openai2024learning, snell2025scaling, …}”, “KIVI \cite{KIVI}”, “TurboQuant \cite{zandieh2026turboquant}”). However, the bibliography section is empty, meaning none of these references can be verified. This undermines the credibility of the claims and violates the paper’s own citation policy.

The experimental results presented in Tables 1–4 generally support the claim that KVarN reduces error accumulation compared to prior KV‑Cache quantization methods and often achieves the highest accuracy among the quantized baselines. For example, on the MATH500 benchmark KVarN attains 79.2 % accuracy versus 77.8 % for KIVI, and on HumanEval it reaches 88.4 % versus 86.4 % for KIVI. These improvements, while modest, are consistent across models and tasks, so the “state‑of‑the‑art for KV‑Cache compression” claim is defensible **provided** it is explicitly limited to the quantized setting.

A few claims are overstated or lack supporting evidence:
- The abstract and contributions state “substantial improvement over current state‑of‑the‑art” without quantifying “substantial”; the improvements are typically 1–2 % absolute, which should be described more cautiously.
- The paper asserts that the code is released in the supplementary, yet no supplementary code link or repository is included.
- The runtime overhead claim (“0.18 %”) is based on a single hardware configuration; a broader evaluation (different GPUs, batch sizes) would strengthen this claim.

Overall, the factual backbone of the paper is plausible, but the missing bibliography and absent code link are critical issues that must be resolved before the paper can be accepted. Addressing these citation and reproducibility problems will bring the manuscript into compliance with the claim‑accuracy standards.

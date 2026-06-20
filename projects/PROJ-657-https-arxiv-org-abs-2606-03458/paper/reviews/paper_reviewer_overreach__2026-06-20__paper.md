---
action_items:
- id: 674c3b2ad5e5
  severity: science
  text: "Validate the `pseudo-decode` proxy (Fig.\u202F4) against a true autoregressive\
    \ decoding run and report quantitative agreement; otherwise temper the claim that\
    \ it \u201Caccurately simulates\u201D error accumulation."
- id: 9366909b071a
  severity: science
  text: "Add missing baselines (e.g., recent 2\u2011bit KV\u2011Cache methods, mixed\u2011\
    precision variants) and report statistical significance of the reported gains;\
    \ the current tables (e.g., Tab.\u202F1, Tab.\u202F2) do not demonstrate that\
    \ the improvements are robust."
- id: 806f8299d738
  severity: writing
  text: "Rephrase blanket statements of \u201Cstate\u2011of\u2011the\u2011art\u201D\
    \ performance (Abstract, Sec.\u202F1, Sec.\u202F5) to reflect that results are\
    \ limited to the evaluated models and settings."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:35:40.479401Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript repeatedly extrapolates its experimental findings beyond what is directly supported by the presented data. In the abstract and introduction the authors claim that KVarN “establishes a new state‑of‑the‑art for KV‑Cache compression on reasoning benchmarks” (lines ≈ 30‑35). However, the empirical evidence is confined to three model families (Qwen3‑4B, Llama‑3.1‑8B, Phi‑4) and a limited set of baselines. Notably, recent 2‑bit KV‑Cache methods such as TurboQuant are only evaluated in a mixed‑precision configuration (Table 1, “TurboQuant 3/3 bits/elem”) and are not directly comparable to the 2‑bit uniform‑precision setting of KVarN. This makes the “state‑of‑the‑art” claim over‑reaching.

A central methodological contribution is the “pseudo‑decode” evaluation (Fig. 4, Sec. 3.2). The authors assert that it “accurately simulates” error accumulation, yet no quantitative comparison to a full autoregressive decode is provided. Without such validation, the claim that the proxy faithfully models the dynamics of real decoding is unsupported.

The paper also suggests that the proposed variance‑normalization “substantially reduces error accumulation” (Sec. 4, Fig. 5) and that this leads to “near loss‑less 2.3 bit‑per‑element KV‑Caches” (Conclusion). Yet the reported improvements are modest (e.g., 0.4 % absolute gain on IF‑Eval strict accuracy, Table 3) and sometimes within the variance of three runs. The manuscript does not present statistical tests or confidence intervals to substantiate that these differences are significant rather than noise.

Finally, the discussion of limitations (Sec. 9) acknowledges that the method is inapplicable to non‑KV architectures, but the broader limitation that the approach may not generalize to larger or differently‑structured models is omitted, despite the authors’ broad claims.

To align the manuscript with the evidence, the authors should (1) provide a rigorous validation of the pseudo‑decode proxy, (2) broaden the baseline comparison set and include statistical significance testing, and (3) temper universal performance claims to reflect the specific experimental scope. These revisions will ensure that the paper’s conclusions are appropriately bounded by the presented data.

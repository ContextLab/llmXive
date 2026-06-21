---
action_items:
- id: 8c19ecb209f3
  severity: writing
  text: "Replace the citation of Yang2025qwen3 in the statement about On\u2011policy\
    \ Distillation (OPD) with a source that actually discusses OPD; Yang2025qwen3\
    \ is a model technical report and does not cover OPD methodology."
- id: 71dbc515193c
  severity: writing
  text: "Verify that Li2026rethinking indeed addresses on\u2011policy distillation\
    \ of LLMs; if it does not, substitute with a more appropriate reference."
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:41:53.348404Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several factual claims that are generally well‑supported by the cited literature, but there are a few instances where the citations do not directly back the statements.

1. **On‑policy Distillation (OPD) citation (Section 1, lines 71‑73).** The authors cite *Yang2025qwen3* alongside Agarwal 2024, Lu 2025, and Li 2026 to support the claim that OPD provides dense token‑level supervision and mitigates exposure bias. *Yang2025qwen3* is a technical report describing the Qwen‑3 model architecture and does not discuss OPD methodology. This citation is therefore inaccurate and should be replaced with a work that explicitly covers OPD (e.g., Agarwal 2024 or a more recent OPD study).

2. **Li2026rethinking citation (Section 1, lines 73‑75).** The paper is cited as evidence that OPD “overcomes the bottleneck of sparse outcome rewards.” While Li 2026 does discuss on‑policy distillation, it focuses on phenomenology rather than the specific reward‑sparsity argument. The claim would be stronger if supported by a source that directly addresses reward sparsity in OPD, such as the original OPD papers or a reinforcement‑learning‑focused analysis.

3. **Sample‑efficiency claim (Abstract and Section 4.2).** The authors state that d‑OPSD requires “around 10 % of the optimization steps by RLVR.” Table 3 shows 425 steps vs. 7,700 steps for GSM8K, which is ≈5.5 %. The phrasing “around 10 %” is acceptable given the variability across tasks, but the authors should clarify that the reduction ranges from ~5 % to ~10 % depending on the benchmark.

4. **RLVR baseline citations (Section 4.1, Table 2).** The performance numbers for diffu‑GRPO are correctly attributed to *Zhao2025d1*. The VRPO baseline is cited as *Zhu2025llada*, which indeed introduces a variance‑reduced policy optimization for diffusion LLMs, so this citation is appropriate.

5. **AR‑style OPSD comparison (Section 4.3, Table 4).** The AR‑style baseline follows *Zhao2026self*; this citation correctly describes an AR‑centric self‑distillation method, so the claim that the AR‑style construction is suboptimal for dLLMs is well‑supported.

Overall, the paper’s central claims about the novelty of d‑OPSD, its step‑level divergence supervision, and its empirical superiority are substantiated by the presented experiments and appropriate citations. The primary issues are the mis‑aligned citations for OPD in the introduction. Correcting these will improve the factual integrity of the manuscript.

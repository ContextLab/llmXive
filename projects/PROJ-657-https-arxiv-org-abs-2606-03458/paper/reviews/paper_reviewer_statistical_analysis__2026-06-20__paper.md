---
action_items:
- id: 9d6308e6a9ca
  severity: science
  text: "Provide statistical significance testing (e.g., paired t\u2011tests or Wilcoxon\
    \ signed\u2011rank tests) for the reported improvements in Tables\u202F1\u2011\
    4 and Figures\u202F2\u20115, including p\u2011values and effect sizes."
- id: 1a686c33cdbb
  severity: science
  text: "Report confidence intervals (95\u202F% CI) or standard errors for all aggregate\
    \ metrics (accuracy, KL\u2011divergence, token counts) rather than only means\
    \ or occasional std deviations."
- id: 19ce99690d22
  severity: science
  text: "Address multiple\u2011comparison issues arising from evaluating many models,\
    \ tasks, and quantization settings; apply a correction method (e.g., Bonferroni,\
    \ Holm\u2011\u0160id\xE1k) or clearly justify why it is unnecessary."
- id: 4271f5bb1be2
  severity: science
  text: "Validate the \u2018pseudo\u2011decode\u2019 proxy (Section\u202F3.2, Fig.\u202F\
    3) by correlating its results with full autoregressive decoding on a held\u2011\
    out subset, and report the correlation coefficient with confidence bounds."
- id: be0686437177
  severity: science
  text: "Include a power analysis or sample\u2011size justification for the number\
    \ of runs (three) used in the experiments; explain whether this provides sufficient\
    \ statistical power to detect the observed effect sizes."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:36:06.238024Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces KVarN, a variance‑normalized KV‑Cache quantization method, and reports extensive empirical gains across several reasoning and instruction‑following benchmarks (Tables 1‑4). While the experimental breadth is commendable, the statistical analysis is insufficient to substantiate the claimed improvements.

1. **Lack of significance testing** – Across the main results (e.g., Table 1 for AIME24/MATH500, Table 2 for HumanEval, Table 3 for IFEval, and Table 4 for line‑retrieval) the authors present point estimates (often with ± std for token counts) but no hypothesis tests. It is unclear whether the observed differences (e.g., 60.0 % vs 55.5 % accuracy on AIME24, Fig. 4) are statistically distinguishable given the variability inherent in LLM generation. Adding paired statistical tests (e.g., paired t‑test across the three random seeds) with reported p‑values and effect sizes would make the claims more robust.

2. **Confidence intervals and variance reporting** – Some tables include standard deviations for token counts, yet most performance metrics (accuracy, strict/loose scores) lack any measure of uncertainty. Providing 95 % confidence intervals for each metric would allow readers to assess overlap between methods and avoid over‑interpretation of marginal gains.

3. **Multiple‑comparison correction** – The paper evaluates many combinations of models (Qwen3‑4B, Llama‑3.1‑8B, Phi‑4), tasks, and quantization baselines (KIVI, QuaRot, KVQuant‑1 %, etc.). Conducting multiple pairwise comparisons inflates the family‑wise error rate. The authors should either apply a correction (e.g., Holm‑Šidák) or explicitly state why the family‑wise error is controlled (e.g., by pre‑specifying a primary hypothesis).

4. **Validation of the pseudo‑decode proxy** – Section 3.2 introduces a “pseudo‑decode” evaluation (Fig. 3) to model error accumulation. However, the manuscript does not quantify how well this proxy predicts performance under true autoregressive decoding. Reporting a correlation coefficient (with CI) between pseudo‑decode and full decoding results on a held‑out subset would justify its use as a fast proxy.

5. **Sample‑size and power considerations** – All experiments are averaged over three runs. No justification is given for why three seeds provide adequate power to detect the reported effect sizes. A brief power analysis (or at least a discussion of the expected variability) would help readers gauge the reliability of the results.

Addressing these points will substantially strengthen the empirical claims and align the work with rigorous statistical standards expected for NeurIPS submissions.

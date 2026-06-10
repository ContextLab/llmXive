---
action_items:
- id: 04fbfddc1fca
  severity: science
  text: Report statistical significance (p-values or confidence intervals) for accuracy
    gains in Table 1, especially for small margins like +0.1%.
- id: 479724dbb51c
  severity: science
  text: Control for tool call budget (turn count) to isolate the masking effect from
    the confounding variable of increased search attempts.
- id: 3369d2d6c159
  severity: science
  text: Clarify if the 'regime' is model-dependent or task-dependent given the variance
    across benchmarks (e.g., GPT-OSS-120B results in Table 1).
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T07:42:41.116052Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical study, but the scientific evidence requires strengthening regarding statistical rigor and causal isolation. Table 1 (e001) reports accuracy gains (e.g., +11.7% for Qwen3.5-35B-A3B) without confidence intervals or p-values. Given the sample sizes (830 for BrowseComp-Plus, 103 for GAIA), variance matters significantly for small gains (e.g., +0.1% for GPT-OSS-120B). Section 5.1 notes masking increases tool calls ($\Delta$ calls/q up to +91.6). It is unclear if accuracy gains stem from masking itself or simply from increased search budget (more turns). A control experiment fixing the turn count or tool call budget is needed to isolate the masking effect from the effect of additional retrieval attempts.

Furthermore, the "regime" behavior is inconsistent across benchmarks for the same model (e.g., GPT-OSS-120B shows +0.1 on BrowseComp-Plus, -4.8 on GAIA, +8.0 on xBench in Table 1). This suggests task difficulty or domain specificity, not just model capacity, drives the regime. The regression probe (Figure 3, e001) claims separability based on SNR, but the link between SNR and actual retrieval success needs stronger causal evidence beyond correlation. Finally, the LLM-as-Judge evaluation (Section 4.1) reports 99.9% human audit agreement, but the variance of the judge itself should be reported to ensure the accuracy metrics are robust across different query types. Without these controls, the "regime map" risks being an artifact of specific benchmark distributions rather than a generalizable mechanism.

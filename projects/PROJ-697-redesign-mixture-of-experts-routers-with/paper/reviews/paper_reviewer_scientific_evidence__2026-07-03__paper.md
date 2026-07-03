---
action_items:
- id: 0015d7f1c3f7
  severity: science
  text: The claim of 'faster convergence' and 'superior performance' lacks statistical
    significance testing. Table 1 (tab:opt-agnostic) and Table 3 (tab:midtrain) report
    single-point averages without standard deviations, confidence intervals, or p-values.
    Given the stochastic nature of LLM pretraining, single-run comparisons are insufficient
    to rule out random variance as the cause of observed gains.
- id: fad639b9788d
  severity: science
  text: The ablation study in Section 5.2.1 (lines 630-650) compares the full method
    against a 'normalization-only' baseline but fails to include a 'power-iteration-only'
    (no retraction) baseline in the final performance tables. While the text mentions
    instability for the latter, quantitative data on its performance (if stable runs
    were possible) or a clear explanation of why it cannot be compared fairly is needed
    to isolate the specific contribution of the retraction step versus the power iteration.
- id: b1668c923e9e
  severity: science
  text: The efficiency claim of '0.2% slowdown' (Section 4.3, line 560) is presented
    as a definitive metric but lacks the necessary context of variance or measurement
    methodology. Was this measured over a single step or an average over the entire
    training run? Without error bars or a description of the measurement protocol,
    this precise figure is not robustly supported.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:00:30.117979Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling theoretical motivation for aligning router weights with the principal singular directions of expert matrices. However, the scientific evidence supporting the empirical claims requires strengthening to meet the standards of rigorous machine learning research.

The primary concern is the absence of statistical significance testing. The paper reports performance improvements across multiple benchmarks (e.g., Table 1, Table 3) based on single training runs. In the context of large-scale pretraining (350B tokens), performance metrics can fluctuate due to random seed initialization, data shuffling, and optimizer dynamics. Without reporting standard deviations over multiple seeds (e.g., 3-5 runs) or providing confidence intervals, it is impossible to determine if the observed gains (e.g., +1.39% on GSM8K in Table 3) are statistically significant or merely artifacts of random variance. The claim of "faster convergence" in Figure 2 is similarly anecdotal without error bands.

Furthermore, the ablation studies, while present, are not fully conclusive regarding the specific contributions of the "Power" and "Retract" components. The authors demonstrate that removing retraction leads to instability (Section 5.2.1), which is a valid finding. However, to isolate the benefit of the power iteration itself, a comparison against a baseline that includes power iteration but lacks the specific retraction logic (if stable) or a more rigorous analysis of the "normalization-only" baseline is needed. The current evidence suggests the retraction is necessary for stability, but the marginal gain of the power iteration step over a simple normalized router (if the latter were stable) is less clearly quantified in the final results.

Finally, the efficiency claim of a "0.2% slowdown" is stated with high precision but lacks methodological detail. Was this measured as an average over the entire training run? What was the variance? Given the complexity of MoE training, such a small difference could easily fall within the noise of system-level fluctuations. Providing a brief description of the measurement protocol or error margins would bolster the credibility of this claim.

In summary, while the method appears promising, the current evidence relies on single-run point estimates that do not robustly support the strong claims of superiority and efficiency.

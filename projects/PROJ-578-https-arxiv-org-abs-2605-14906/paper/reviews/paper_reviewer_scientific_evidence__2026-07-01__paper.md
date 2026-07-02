---
action_items:
- id: d1413c2f8d1e
  severity: science
  text: The claim that 80.4% of questions require visual evidence is unsupported.
    Table 1 and Section 3.3 state 65.7% are image-essential and 14.7% supportive.
    The ablation in Table 2 tests the combined set (n=634) but does not isolate the
    'essential' subset. If 'supportive' questions retain >2% accuracy without images,
    the aggregate drop to <2% is misleading. Separate ablation results for 'essential'
    vs 'supportive' are required to validate the claim.
- id: 3a17e2a08e07
  severity: science
  text: The evaluation of 27 LVLMs lacks statistical significance testing. Reported
    accuracy differences (e.g., Gemini-3.1-Pro vs open-weight) have no confidence
    intervals or p-values. With small subtype sample sizes (e.g., MSR n=46), observed
    differences may be within margin of error. Bootstrap CIs are only provided for
    the 195-subset, not the main 789-question results used for conclusions.
- id: f3857730c1f9
  severity: science
  text: The LLM-as-Judge metric (Qwen3-VL-235B) shows leniency bias (5.4% FP vs 1.0%
    FN). This may inflate scores for verbose models, skewing rankings. The impact
    of this bias on the final leaderboard is not quantified. A sensitivity analysis
    or bias-corrected scoring is needed to ensure rankings reflect memory fidelity
    rather than verbosity.
- id: 9cdc2e698424
  severity: writing
  text: The claim that 'Multi-session reasoning caps most systems below 30%' overstates
    the evidence. Table 1 shows Kimi-K2.5 achieving 44.06% on MSR at 32K. The abstract
    generalizes to 'most systems' without defining thresholds or excluding outliers.
    The data shows variance, not a hard cap. Refine the claim to reflect the observed
    distribution.
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:03:19.914659Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence in the paper is robust in design but lacks statistical rigor and contains potential evaluation biases that weaken central claims.

First, the **visual evidence ablation** (Table 2, e000) conflates "image-essential" (65.7%) and "image-supportive" (14.7%) questions. The claim that accuracy collapses to <2% for the combined 80.4% subset is not supported if the "supportive" subset retains higher accuracy without images. The paper must report ablation results separately for these groups to prove that visual evidence is strictly required for the "essential" portion, rather than relying on an aggregate that may be driven by the smaller "essential" group.

Second, **statistical significance** is missing for the main results. The paper reports precise accuracy drops (e.g., >13% for open-weight models) but provides no confidence intervals or p-values. Given the small sample sizes for specific tasks (e.g., MSR n=46, AR n=90), these differences could be statistically insignificant. The absence of uncertainty quantification makes it impossible to distinguish real performance degradation from noise.

Third, the **LLM-as-Judge** introduces a leniency bias (5.4% false positives vs 1.0% false negatives). This bias likely favors models that generate verbose or hedged answers, potentially inflating their scores relative to concise models. The paper does not quantify how this bias affects the final model rankings, raising concerns about whether the benchmark measures memory fidelity or response verbosity.

Finally, the **"30% cap"** claim on multi-session reasoning is an overgeneralization. Table 1 shows Kimi-K2.5 achieving 44.06% on MSR at 32K. The abstract's statement that "most systems" are capped below 30% ignores this outlier and the observed variance. The evidence supports a performance distribution rather than a hard ceiling.

To improve the scientific evidence, the authors must: (1) separate ablation results for "essential" and "supportive" questions; (2) provide confidence intervals for all main performance metrics; (3) analyze the impact of judge leniency on rankings; and (4) refine the "30% cap" claim to accurately reflect the data.

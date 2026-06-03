---
action_items:
- id: 2a01ab19f378
  severity: science
  text: Report statistical significance (p-values, confidence intervals, or bootstrap
    uncertainty) for all benchmark comparisons. Single-run point estimates without
    variance measures are insufficient for claiming SOTA performance.
- id: ba0f9a6c1274
  severity: science
  text: Address multiple comparisons problem. The paper compares 15+ models across
    6+ benchmarks without correction (e.g., Bonferroni, FDR). This inflates Type I
    error rates for claimed improvements.
- id: 9a0c37e7ac37
  severity: science
  text: "Provide run-to-run variance. All results appear to be single-seed runs. Report\
    \ mean \xB1 std across \u22653 random seeds for all training-based claims, especially\
    \ for the 1k-sample training regime."
- id: cb6b7b15ad3f
  severity: science
  text: Justify small sample sizes in guardrail evaluation (e.g., 16 trajectories
    for ClawSafety, 35 for CIK-Bench in Table 5). Report confidence intervals for
    these percentages (e.g., 25.00% from 4/16 has ~95% CI of ~8-49% using Wilson interval).
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T10:55:54.382182Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents extensive experimental results but lacks rigorous statistical analysis required to support its claims.

**1. Missing Uncertainty Quantification (Section 3.4, Tables 1-5)**
All reported metrics (Accuracy, F1, ASR, etc.) are presented as single point estimates without confidence intervals, standard deviations, or p-values. For example, Table 1 claims AgentDoG-4B achieves 92.2% accuracy on R-Judge vs. 91.8% for AgentDoG 1.0-4B. Without variance estimates, we cannot determine if this 0.4% difference is statistically meaningful or within run-to-run noise.

**2. Multiple Comparisons Problem (Throughout)**
The paper makes 20+ pairwise comparisons across R-Judge, ATBench, ATBench-Claw, ATBench-Codex, AgentHarm, AgentSafetyBench, AgentDojo, AgentDyn, and CIK-Bench without any correction for multiple testing. This dramatically increases the probability of false positive claims. At minimum, report adjusted p-values or use a hierarchical testing framework.

**3. Insufficient Repetition for Training-Based Claims (Section 3.3, Table 2)**
The SFT and RL results (Tables 3-4) show improvements from adding AgentDoG-filtered data. These are training-dependent results that should be reported across multiple random seeds. The claim that "~1k samples achieves SOTA performance" (Abstract) requires uncertainty bounds to assess generalization stability.

**4. Guardrail Evaluation Sample Sizes (Table 5, Section 4.3)**
The guardrail benchmarks use very small test sets: 16 trajectories for ClawSafety, 35 for CIK-Bench. The reported ASR of 25.00% (4/16) has a Wilson 95% confidence interval of approximately [8%, 49%]. This uncertainty is not acknowledged, making the claimed "-31.25% ΔASR" improvement statistically ambiguous.

**5. No Power Analysis**
The paper does not justify sample sizes for any experiment. For the 1k-sample training claim, a power analysis should demonstrate this is sufficient to detect meaningful safety improvements with acceptable Type II error rates.

These issues prevent reproducibility and undermine confidence in the reported SOTA claims.

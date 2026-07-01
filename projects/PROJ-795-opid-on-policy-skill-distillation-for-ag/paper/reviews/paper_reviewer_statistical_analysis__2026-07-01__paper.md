---
action_items:
- id: ac1662c10b2e
  severity: science
  text: "The paper reports point estimates (e.g., 84.3 vs 75.0) without confidence\
    \ intervals, standard errors, or p-values. Given the stochastic nature of RL training\
    \ and the small number of reported runs (implied by single values), statistical\
    \ significance cannot be established. Re-run experiments with multiple seeds (n>=5)\
    \ and report mean \xB1 std dev or 95% CIs for all main results in Table 1 and\
    \ ablation studies."
- id: 2573cb5ccb30
  severity: science
  text: The sample efficiency analysis (Figure 4, Table in Appendix) compares OPID
    and GRPO at different data fractions (20%-100%) but lacks statistical testing
    for the interaction effect. The claim that OPID 'surpasses' GRPO at 80% data (78.9
    vs 75.0) is not supported by a significance test (e.g., paired t-test or bootstrap)
    across seeds. Provide statistical validation for these comparative claims.
- id: 4c55da985c93
  severity: science
  text: "The critical-first routing ablation (Table 3) shows a +6.8 point gain. However,\
    \ the mechanism for identifying 'critical timesteps' ($\\mathcal{C}_\tau$) relies\
    \ on an LLM analyzer. The paper does not report the variance or error rate of\
    \ this analyzer, nor does it perform a sensitivity analysis on the routing threshold.\
    \ Without quantifying the noise in the routing signal, the statistical attribution\
    \ of the gain to the routing mechanism is confounded."
- id: ec189653c605
  severity: science
  text: The theoretical analysis in Appendix A (Proposition 1) assumes 'common-support'
    and 'perfect detection' for the routing regret bound. The empirical section does
    not verify these assumptions. Specifically, the distribution of the skill advantage
    $A^{skill}$ is not analyzed for normality or outliers, which is required to justify
    the use of mean-based comparisons in the main results. Include a distributional
    analysis of the advantage signals.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:04:56.742944Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the experimental evaluation is insufficient to support the paper's central claims regarding the efficacy of OPID. While the reported performance gains are numerically positive, the absence of uncertainty quantification renders the results scientifically inconclusive.

First, the main results in Table 1 and the ablation studies in Tables 2 and 3 report single point estimates (e.g., 84.3% success rate) without any measure of variance. Reinforcement learning algorithms, particularly those involving LLMs, exhibit high variance across different random seeds due to stochasticity in sampling, initialization, and the environment. Without reporting results from multiple independent runs (e.g., $n \ge 5$ seeds) with standard deviations or 95% confidence intervals, it is impossible to determine if the observed improvements (e.g., +9.3 points on ALFWorld) are statistically significant or merely artifacts of a favorable random seed. The current presentation implies a level of certainty that the data does not support.

Second, the sample efficiency analysis (Section 3.3, Figure 4, and Appendix Table) compares performance across different data budgets. The claim that OPID "surpasses" GRPO at 80% data (78.9 vs 75.0) is presented as a definitive finding. However, no statistical test (such as a paired t-test, Wilcoxon signed-rank test, or bootstrap confidence intervals) is provided to validate this difference. Given the small sample size implied by the single reported values, the probability of a Type I error (false positive) is non-negligible. The authors must re-run these experiments with sufficient replication to establish statistical significance.

Third, the "critical-first" routing mechanism relies on an LLM-based analyzer to identify critical timesteps ($\mathcal{C}_\tau$). The ablation study attributes the +6.8 point gain solely to this routing logic. However, the statistical properties of the analyzer's output are not reported. If the analyzer has high variance or a high false-positive rate in identifying critical steps, the routing signal becomes noisy. The paper fails to provide a sensitivity analysis or error bounds for the routing decision, leaving the attribution of the performance gain to the routing strategy confounded by the noise in the skill extraction process.

Finally, the theoretical analysis in Appendix A derives bounds based on assumptions of "perfect detection" and "common support." The empirical section does not verify these assumptions. Specifically, the distribution of the skill advantage signal ($A^{skill}$) is not analyzed. If this signal is highly skewed or contains outliers, the mean-based aggregation used in the policy gradient update may be unstable. A distributional analysis of the advantage signals and a verification of the theoretical assumptions against the empirical data are required to validate the proposed method's robustness.

In summary, the paper requires a full revision of its experimental section to include multiple random seeds, statistical significance testing, and uncertainty quantification before its claims can be accepted.

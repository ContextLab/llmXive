# Automated-review action items — Trust Region On-Policy Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Introduction claims TrOPD improves OPD by +3.34, +4.00, +5.11, +6.18 points. Table 1 shows math gain is +3.06 (38.54 vs 35.83). Table 2 shows +4.06. The text numbers do not match table data. Correct the values or specify the exact config used.
- **[writing]** Section 3.1 claims REOPLD causes a 'performance bottleneck' by removing supervision. Table 1 shows REOPLD (47.86) outperforms OPD baseline (46.79). The claim contradicts the data showing improvement. Rephrase to state REOPLD improves baseline but is outperformed by TrOPD.
- **[writing]** Section 3.2 claims TrOPD has lower gradient norm than Clip Outlier per Figures 3/4. Figures are not visible. Ensure the figures explicitly show TrOPD < Clip Outlier for gradient norms, not just general trends, to support this specific comparison.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states that TrOPD, OPD, and REOPOLD are trained on 'Qwen3-SFT-1.7B', but the x-axis labels include 'Qwen3-1.7B' as a distinct baseline. The caption fails to clarify if this baseline is the raw SFT model or the Base model, creating ambiguity regarding the comparison group.
- **[writing]** Figure 1: The citation 'ko2026scaling' is embedded directly into the figure caption text ('...REOPOLD ko2026scaling...') rather than being formatted as a standard reference, which disrupts readability.
- **[science]** Figure 2: The diagram uses specific algebraic equations (e.g., (x-2)(x-3)=0) to illustrate the 'Trust Region' and 'Outlier' concepts, but the caption and visual labels do not explain the mathematical analogy or how these equations map to the probability distributions shown on the left.
- **[science]** Figure 2: The 'Off-Policy Guidance' section displays a 'Fully On-Policy from Student' example, which appears contradictory to the section header and the concept of off-policy guidance.
- **[writing]** Figure 2: The text 'K1 RKD' and 'Topk FKD' appears in the diagram without definition in the caption or visual legend, making the specific method names unclear.
- **[science]** Figure 3: The legend lists 'OPD' (dashed) and 'Clip Outlier' (dotted), but the caption 'Entropy comparison' is too vague to explain why these specific methods are being compared or what the 'Outlier' variants represent in this context.
- **[writing]** Figure 3: The legend entry 'OPD' corresponds to a dashed line, but the plot shows a dashed line that drops significantly lower than the others; without a clear definition of what 'OPD' refers to in this specific entropy context (e.g., baseline vs. proposed), the comparison is ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'SoG' (Student of Generation) and 'ToG' (Teacher of Generation) at first use in Section 3.1. The acronyms are introduced without definition, relying on reader inference from context.
- **[writing]** Replace 'SoTA' with 'state-of-the-art' in the Abstract and Section 5.1. Acronyms for common phrases should be spelled out on first occurrence to aid non-specialist readers.
- **[writing]** Define 'AIME', 'AMC', 'GPQA', 'MMLU', and 'IFBench' at their first mention in Section 5.2 or the Introduction. Currently, these benchmark acronyms are used without expansion, assuming domain familiarity.
- **[writing]** Clarify the term 'mid-training' in the Limitations section. This is not a standard, universally defined term in the field and requires a brief explanation of what stage of the pipeline it refers to.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.2, the paper claims that when sum(pi_S(v)) -> 0, KL(pi_T || pi_S) -> 0. This is mathematically incorrect; if pi_S(v) approaches 0 while pi_T(v) > 0, the term log(pi_T/pi_S) approaches infinity, causing KL to diverge. The logic for why the outlier objective is 'suppressed' needs correction or a different mechanism explanation.
- **[science]** The definition of the trust region probability P_trust(x) = min(pi_T(x)/pi_S(x), 1) is presented as a Bernoulli probability. However, if pi_S(x) is very small, this ratio can exceed 1, which is clamped to 1. The paper does not explain how this stochastic masking interacts with the gradient estimator for the RKL term, specifically whether the expectation over the Bernoulli mask is correctly accounted for in the final objective function.
- **[writing]** Table 1 lists 'FKL Outlier' with an average score of 49.00, while 'TrOPD' (which includes the same FKL Outlier component plus off-policy guidance) scores 49.85. However, the text in Section 4.3 claims TrOPD outperforms 'FKL Outlier' by 3.06 points on average. The numbers in the text (49.85 - 49.00 = 0.85) contradict the claimed 3.06 point gain, suggesting a calculation error or a mismatch in the reported baselines.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims specific gains (+3.34, +4.00, etc.) not explicitly derived in tables. Tables show different averages (e.g., +3.06 math). Clarify or remove precise numbers to avoid over-claiming precision.
- **[writing]** Claim to 'establish a general benchmark' overstates contribution. The work performs a unified evaluation on existing datasets, not creating a new benchmark. Rephrase to 'conduct a unified evaluation'.
- **[science]** Claim that TrOPD specifically mitigates 'K1 reverse-KL estimator' instability lacks direct evidence isolating K1 failure modes. Provide training curves or analysis linking stability gains specifically to K1 mitigation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper relies on teacher models (e.g., Skywork-OR1-Math-7B, Qwen3-Nemotron-4B) trained on datasets including WildChat-1M and Open-Instruct (Appendix). Explicitly state whether these datasets contain personally identifiable information (PII) and confirm that appropriate consent or public-domain status was verified for the distillation process to ensure data privacy compliance.
- **[writing]** The 'Off-Policy Guidance' section describes using teacher-generated prefixes to guide student generation. Clarify if the teacher model's training data includes copyrighted material or sensitive content that could be inadvertently memorized and regurgitated by the student, and discuss any mitigation strategies for potential IP or safety leakage.
- **[writing]** The methodology involves training on mathematical reasoning and code generation benchmarks. While generally benign, acknowledge potential dual-use risks if the distilled models are applied to generate malicious code or exploit mathematical vulnerabilities, and briefly mention safety alignment considerations in the Limitations or Conclusion.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims TrOPD outperforms baselines by specific margins (e.g., +3.34 on math, Table 1 caption) but does not report standard deviations or statistical significance tests (e.g., t-tests) across the 32 evaluation runs mentioned in 'Benchmark Evaluation'. Without variance estimates, the robustness of these gains against random seed noise is unverified.
- **[science]** The ablation study in Table 3 (tab:ablation) compares TrOPD variants but lacks a direct comparison against a 'Vanilla OPD' baseline trained under the exact same random seeds and hyperparameters for the specific ablation setting. The claim that FKL Outlier is superior relies on comparing results across different table rows which may not be statistically paired.
- **[science]** The 'Adaptive Trust Region' probability $P_{trust}(x)$ is defined as $\min(\pi_T(x)/\pi_S(x), 1)$. The paper does not provide empirical evidence (e.g., a histogram or distribution plot) showing the actual fraction of tokens classified as 'trust region' vs. 'outlier' during training. Without this, the claim that the method effectively partitions the space remains theoretical.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper claims results are 'average accuracy of 32 times evaluation' (Benchmark Evaluation) but does not report standard deviation, standard error, or confidence intervals for any metric in Tables 1, 2, or 3. Given the stochastic nature of LLM sampling and the small number of seeds (n=32), statistical significance testing (e.g., paired t-tests or bootstrap CIs) is required to validate that observed gains (e.g., +3.06 points) are not due to random variance.
- **[science]** The adaptive trust region probability $P_{trust}(x)$ is defined as a Bernoulli trial (Eq. 10). The manuscript does not specify the number of samples used to estimate the expectation of this stochastic mask or how the variance introduced by this sampling is handled during backpropagation. Clarification on the variance reduction technique (e.g., control variates) or the stability of the gradient estimator is needed.
- **[science]** Table 1 and Table 2 report single-point performance metrics without error bars. For the 'Avg.' columns, the aggregation method (mean of means vs. mean of all samples) is not explicitly defined. Reproducibility requires reporting the standard deviation across the 32 evaluation runs for each benchmark to assess the robustness of the reported improvements.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, the sentence 'Different from previous predefined threshold τ, we define the trust region...' contains a grammatical error. It should read 'Different from previous predefined thresholds τ' or 'Unlike the previous predefined threshold τ' to ensure subject-verb agreement and clarity.
- **[writing]** In Section 4.1, the phrase '32 times evaluation' is awkward and non-idiomatic. It should be revised to 'evaluated 32 times' or 'based on 32 evaluation runs' for better readability and professional tone.
- **[writing]** In the Introduction, the sentence 'This work establishes a unified benchmark to systematically study this challenge from three perspectives: (1)... (2)... and (3)...' uses a colon followed by a list that is not fully integrated into the sentence structure. Consider rephrasing to 'This work establishes a unified benchmark to systematically study this challenge through three perspectives: (1)...' or restructuring the list to flow more naturally.
- **[writing]** In Section 3.1, the phrase 'stand-alone FKL can not achieve effective training' uses 'can not' which is often considered less formal than 'cannot'. Additionally, the sentence structure is slightly clunky; consider 'stand-alone FKL fails to achieve effective training' for conciseness and impact.

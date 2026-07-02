# Automated-review action items — DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify if 'Best Baseline' in Table 1 is the single best method or an average. The text says 'strongest baselines' (plural) but reports a single delta. Match the text to the table header 'Best Baseline' (singular) or specify the aggregation method.
- **[fatal]** Verify the citation for 'Qwen3-8B-Base' and 'Qwen3-14B-Base'. The model 'Qwen3' is not a standard public release. Ensure the reference 'yang2025qwen3' in the bibliography actually documents this model, or replace with a verified public model to support the experimental claims.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 2: The caption describes a three-panel figure ('Left: Reward; Middle: Response Length; Right: Entropy'), but the rendered image displays only a single 'Reward' plot. The 'Response Length' and 'Entropy' panels are missing.
- **[fatal]** Figure 3: The caption is explicitly '(no caption)', providing no context for the plot's content, axes, or experimental setup.
- **[science]** Figure 3: The legend includes 'DAPO', but the caption for Figure 2 describes the comparison as 'DelTA compared with DAPO', suggesting the plot is intended to show DelTA but is mislabeled or the caption is missing the necessary context to verify the method being plotted.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and acronyms that are not defined upon first introduction, creating a barrier for non-specialist readers. In the Abstract and Introduction, the term "RLVR" is used immediately without spelling out "Reinforcement Learning from Verifiable Rewards." Similarly, "DAPO" and "FIPO" are introduced in the Experiments section and Preliminaries without definition, despite being critical baselines. In Section 3.1, the phrase "side-wise centroids" is u

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent theoretical framework for DelTA, linking the discriminator view of RLVR updates to a token-level reweighting mechanism. However, several logical gaps exist between the stated premises and the final conclusions. First, the central empirical claim in the Abstract and Introduction—that DelTA outperforms the "strongest same-scale baselines"—is not fully supported by the data presentation in Table 1. The table lists a generic "Best Baseline" row with aggregate scores but

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** Claims of 'generalization' to code/Olmo3 lack statistical significance tests or per-benchmark variance, unlike main math results. Provide full stats or temper claims to 'preliminary promise'.
- **[writing]** Conclusion claims 'consistent' OOD improvement, but 14B MMLU-Pro gain (1.63 pts) lacks significance testing. Clarify 'consistent' scope or add per-task significance tests.
- **[writing]** Theoretical claim of 'reshaping update direction' relies on a proxy gradient and K=1 step. Explicitly acknowledge this approximation in limitations to avoid over-claiming true gradient geometry.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader impacts' section (Appendix) is too generic. Explicitly detail specific dual-use risks (e.g., generating adversarial code, bypassing safety filters in reasoning models) and propose concrete mitigation strategies beyond 'responsible deployment'.
- **[writing]** The paper uses 'DeepMath-103K' and benchmarks like AIME/HMMT. Clarify the data provenance and consent status. If scraped from the web, confirm compliance with terms of service and absence of PII or copyrighted material in the training set.
- **[writing]** The method reweights token gradients to amplify 'discriminative' signals. Discuss potential for 'reward hacking' or amplifying subtle biases in the reward function (e.g., favoring specific reasoning styles that correlate with demographic biases in the training data).

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The main results table (Table 1) reports single-point averages (28.40 vs 25.14) without standard deviations or confidence intervals. While Appendix A mentions 16 evaluation runs, the primary results section must report the variance (e.g., mean ± std) to assess the stability of the 3.26 point gain against random seed noise.
- **[science]** The claim that 'bottom-50% tokens collapse' (Section 5, Q2) lacks quantitative evidence. The text states the result but does not provide the specific performance metric (e.g., accuracy drop from X% to Y%) or statistical significance for this ablation, making the magnitude of the effect unverifiable.
- **[science]** The hyperparameter sensitivity study (Table 4) shows the base configuration (K=1) outperforms K=2 and K=3, but the performance gap is small (23.27 vs 22.15/22.20). The paper should clarify if this difference is statistically significant or if the choice of K=1 is primarily driven by the 10.2% computational overhead rather than a large performance delta.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.1 (Significance Test Details) reports a Mann-Whitney U test on S=16 evaluation runs but fails to report the U-statistic, exact p-values, or effect sizes (e.g., rank-biserial correlation). Without these metrics, the claim of 'significant' improvement (p < 0.05) cannot be independently verified or assessed for practical magnitude.
- **[science]** The main results (Table 1) report average scores across seven benchmarks with high precision (e.g., 28.40, 39.91) but omit standard deviations or confidence intervals. Given the stochastic nature of RL training and evaluation, the absence of variance estimates makes it impossible to determine if the reported gains (3.26 and 2.62 points) are robust or within the noise floor of the evaluation protocol.
- **[science]** The hyperparameter sensitivity study (Table 4) compares Base DelTA against variants (K=2, K=3) using point estimates only. No statistical test or error bars are provided to confirm that the observed performance drops for K>1 are statistically significant rather than random fluctuations, weakening the claim that K=1 is 'optimal'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Preliminaries), the formula for J_DAPO uses \sum |o_i| in the denominator. This notation is ambiguous; clarify if this represents the total token count across the group or a specific normalization factor to ensure mathematical precision.
- **[writing]** In Section 3.2, the definition of alpha_{i,t}^{(k)} includes a term gamma_+^{(k)}h(alpha). The function h(alpha) is not defined in the text or the appendix, making the equation impossible to verify or reproduce.
- **[writing]** In Section 4.1 (Main Results), the text states 'DelTA improves average scores by 3.26 (8B) and 2.62 (14B).' These numbers match the difference in Table 1, but the sentence structure is slightly clunky. Consider: 'DelTA improves average scores by 3.26 points on the 8B model and 2.62 points on the 14B model.' for better flow.
- **[writing]** In the Appendix (Token weight analysis), the caption for Figure 1 refers to 'Token clouds,' but the text describes them as 'high- and low-weight token clouds.' Ensure consistent terminology between the figure caption and the main text description.

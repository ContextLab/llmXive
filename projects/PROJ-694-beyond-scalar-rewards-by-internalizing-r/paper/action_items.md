# Automated-review action items — Beyond Scalar Rewards by Internalizing Reasoning into Score Distributions

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Table 1 (main-llmxive.tex), the entry for 'HPSv3' claims it supports 'Score Distribution' (tabyes). However, the cited work (ma2025hpsv3widespectrumhumanpreference) is primarily known for a scalar Human Preference Score. Verify if HPSv3 explicitly outputs a distribution or if this claim overstates the cited source's capabilities.
- **[writing]** The abstract and Section 4.1 claim the 9B RISD student reaches 88.6% HPA, 'closely matching' the 27B teacher (89.6%). While the absolute difference is 1.0%, the relative gap in the 9B baseline (SFT 74.6%) is significant. Ensure the claim of 'closely matching' is supported by statistical significance testing or error bars in the figures, as a 1% gap in high-accuracy regimes can be non-trivial.
- **[writing]** Section 4.2 states that RewardDance 'uses post-hoc pseudo reasoning chains distilled from Qwen-3.6-Max'. The citation (wu2025rewarddancerewardscalingvisual) should be checked to confirm if the reasoning chains are explicitly distilled from a specific 'Qwen-3.6-Max' model or if this is a specific implementation detail of the authors' reproduction not present in the original paper.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1 caption: contains raw citation keys ('wu2025rewarddancerewardscalingvisual', 'deepseek-math') and mentions a 'Right' panel that is not present in the rendered image.
- **[science]** Figure 1: the legend lists '27B-RewardDance' and '9B-SFT' as dashed horizontal lines, but the caption describes a 'Right' panel for final accuracy comparison which is missing; the current layout conflates baselines with training curves without a clear visual distinction for the 'Right' panel mentioned.
- **[writing]** Figure 2: The caption 'GRPO HPA' is insufficient; it fails to define the y-axis metric ('Human Preference Accuracy') or the x-axis ('Step'), and does not explain the difference between the two plotted series ('GRPO' vs 'GRPO (Parsing Text)').
- **[science]** Figure 2: The x-axis tick labels are poorly formatted and illegible, with '1000' and '1250' overlapping ('10001250'), which obscures the scale and data points in that region.
- **[science]** Figure 3: The plot displays two overlapping curves (dark blue and light blue) but lacks a legend or caption definition to distinguish the methods being compared, making the data uninterpretable.
- **[writing]** Figure 3: The caption 'Text--Image Alignment' is too brief to explain the axes ('Reward Score', 'RL Iteration') or the experimental context shown in the plot.
- **[writing]** Figure 4: The caption contains a grammatical error and missing term in the phrase 'and -guided optimization', failing to specify the method name (e.g., RL) that corresponds to the 'RL' label in the image.
- **[science]** Figure 4: The image displays two different female subjects for the SFT and RL columns respectively, rather than generating the same subject from the same prompt, which invalidates the visual comparison of the optimization method's effect.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define the acronym 'VLM' (Vision-Language Model) at its first occurrence in the Abstract or Introduction. It is currently used without definition, assuming reader familiarity.
- **[writing]** Replace the acronym 'OPD' (On-Policy Distillation) with the full term 'on-policy distillation' on first use in the Introduction and Section 3.3, or ensure it is explicitly defined before use.
- **[writing]** Replace the acronym 'GSB' (Good-Same-Bad) with the full phrase 'Good-Same-Bad metric' or 'net preference score' in Section 5.3 to avoid ambiguity for non-specialist readers.
- **[writing]** Replace the acronym 'PLCC' (Pearson Linear Correlation Coefficient) and 'SRCC' (Spearman Rank Correlation Coefficient) with their full names upon first introduction in Section 4.1 to improve accessibility.
- **[writing]** Replace the acronym 'RL' (Reinforcement Learning) with the full term 'reinforcement learning' at its first mention in Section 5 to ensure clarity for readers from adjacent fields.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.1 (Eq. 10), the pairwise loss L_pw sums over G^2 pairs, but the normalization factor 1/(2G^2) implies an average over 2G^2 terms. The text states supervision is applied across 'all G x G cross-side sampled output pairs' (G^2 pairs), yet the denominator includes a factor of 2. Clarify if the factor of 2 accounts for the symmetric summation over j in {w,l} or if the normalization is inconsistent with the stated summation scope.
- **[science]** The claim that the student 'internalizes reasoning' relies on the assumption that the teacher's distribution is a sufficient statistic for the reasoning process. The distillation objective (Eq. 14) only matches output distributions, not the reasoning mechanism. Provide evidence that the distribution is causally dependent on reasoning, not just a correlated output.
- **[science]** In Section 5.2, the paper attributes the 9B GRPO model's lower performance to 'weaker reasoning ability'. However, the 9B GRPO model lacks the direct score-gap supervision (L_pw) present in the 27B GDSO teacher. The performance gap could logically be attributed to the absence of this specific supervision signal rather than the model's inherent reasoning capacity.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the 9B student 'closely matches' the 27B teacher (Abstract, Intro) is an over-interpretation of the 1.0% HPA gap (89.6% vs 88.6%). Given the 18B parameter difference, this gap is statistically significant and should be framed as 'competitive' or 'nearly matching' rather than 'closely matching' to avoid implying parity where a performance ceiling likely exists.
- **[writing]** The assertion that the method yields a '41.3% net human-preference improvement' (Abstract, Sec 5.3) overstates the result. The GSB metric (Eq. 14) is a normalized difference score, not a direct percentage improvement in quality. Reporting this as a '41.3% improvement' implies a relative gain in image quality that the metric does not strictly support; it should be reported as a GSB score of 0.413.
- **[writing]** The paper claims the student 'internalizes' reasoning without explicit chains (Abstract, Sec 3.2), yet the distillation target is the teacher's distribution conditioned on the teacher's reasoning trace. The paper does not provide evidence that the student's internal representations actually encode the *reasoning* logic, only that it mimics the *output distribution*. Claiming 'internalization of reasoning' is an overreach; 'internalization of reasoning-conditioned judgment' is more accurate.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper describes an annotation workflow involving human raters scoring images on subjective dimensions (Section 3). However, it lacks explicit details on IRB approval, informed consent procedures, or how annotator privacy and data protection were handled. This is a critical omission for reproducibility and ethical compliance.
- **[science]** The methodology involves training reward models to optimize text-to-image generation based on human preferences. The paper should explicitly discuss potential dual-use risks, such as the model being used to generate harmful, biased, or deceptive content, and outline any mitigation strategies employed during training or deployment.
- **[science]** The dataset construction relies on 'internally annotated' data and 'real-world prompts from users' (Section 3). The authors must clarify the data usage policies, specifically whether user consent was obtained for using their prompts in training data, and how personally identifiable information (PII) was handled or removed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims a 41.3% net human-preference improvement (GSB) for the optimized generator but does not report the standard error, confidence intervals, or the raw counts (G, S, B) for the 400-prompt evaluation. Without these statistics, the significance of the effect size and the robustness of the claim against random variation cannot be assessed.
- **[science]** The teacher training combines policy-gradient (GRPO) with direct supervised losses (CE and pairwise gap). The paper does not provide an ablation study isolating the contribution of the direct supervised terms versus the policy-gradient term. It is unclear if the performance gains stem from the distributional objective or simply from the strong supervision signal, which risks conflating the proposed method's novelty with standard supervised fine-tuning benefits.
- **[science]** The student distillation (RISD) achieves 88.6% HPA, nearly matching the 27B teacher (89.6%). However, the paper lacks a statistical test (e.g., bootstrap or t-test) to confirm that this small gap is not statistically significant. Without this, the claim that the student 'closely matches' the teacher remains anecdotal rather than empirically proven.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The annotation workflow (Sec 3) states that ground-truth distributions are computed by dropping the highest and lowest scores. However, the statistical validity of this outlier removal is not justified with a sensitivity analysis or a test for normality. If the underlying distribution of human scores is bimodal or skewed, trimming extremes may bias the mean and variance estimates used for training. Please report the number of annotators per sample and justify the trimming rule statistically.
- **[writing]** In Table 1, the 9B RewardDance row lists an SRCC of '6175' (likely a typo for 0.6175). While likely a formatting error, such precision issues in statistical reporting undermine confidence in the reported metrics. Please verify all decimal placements and ensure consistent significant figures across all tables.
- **[science]** The human evaluation in Sec 6.3 reports a net GSB improvement of 41.3% based on 400 prompts. The paper does not provide a confidence interval (e.g., Wilson score interval) or a p-value for this difference against the SFT baseline. Given the binary nature of the 'Good' vs 'Bad' comparison, a statistical significance test (e.g., McNemar's test or a binomial test) is required to confirm the improvement is not due to chance.
- **[science]** The ablation study in Fig 4 compares 'Parsing Text' vs 'Distribution Expectation'. The text claims the latter provides 'denser supervision,' but the statistical significance of the observed gains in HPA and Margin HPA is not quantified. Please include error bars (e.g., standard error over 3 random seeds) or report p-values to ensure the improvements are robust and not artifacts of random initialization.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3, clarify the term 'decode' regarding the score distribution. It is unclear if this refers to token generation or logit derivation. Ensure the mechanism matches the description.
- **[writing]** In Section 4.2, split the dense sentence comparing RewardDance's HPA and calibration metrics into two sentences to improve readability and clarity.
- **[writing]** In Section 5, rephrase the sentence about the ReFL-style scheme. The relative clause 'which is closely related...' ambiguously modifies 'optimization' instead of 'scheme'. Clarify the subject.

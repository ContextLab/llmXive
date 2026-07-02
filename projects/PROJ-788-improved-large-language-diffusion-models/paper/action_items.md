# Automated-review action items — Improved Large Language Diffusion Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'slightly stronger' average vs Qwen2.5 (63.9 vs 63.3). The 0.6 point margin is minimal; consider 'comparable' to avoid overstatement without statistical significance.
- **[writing]** Section 3.1 states iLLaDA-Base is 'slightly stronger' on average. Table 1 shows a 0.6 point lead. Qualify this as 'marginally higher' or 'comparable' to reflect the small effect size accurately.
- **[writing]** Abstract claims 'improves broadly' across benchmarks. While true vs LLaDA, iLLaDA loses to Qwen2.5 on 4/8 metrics. Ensure 'broadly' is clearly scoped to the LLaDA comparison to avoid ambiguity.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims evaluation on 'GSM8K, MATH, and MMLU-Pro', but the plot only displays data for GSM8K. The other datasets are missing from the visualization.
- **[science]** Figure 1: The y-axis lacks a unit or label indicating the metric type (e.g., Accuracy %, Score), making the values (84-90) ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript demonstrates a high density of specialized terminology and acronyms that, while standard within the immediate sub-field of diffusion language models, may hinder accessibility for a broader machine learning audience or researchers from adjacent fields. First, the acronym SFT (Supervised Fine-Tuning) is introduced in the Abstract but is used extensively in Sections 2.2 and 3.3 without being re-introduced or defined in the main body text where it first appears in a sentence. While co

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that iLLaDA-Base is 'slightly stronger on average' than Qwen2.5 7B (Intro) contradicts Table 1, where iLLaDA (63.9) is only 0.6 points higher than Qwen2.5 (63.3). Given the variance in benchmarks, this marginal difference should be qualified as 'comparable' or 'statistically indistinguishable' rather than 'stronger' to avoid overclaiming.
- **[science]** The conclusion that the SFT gap is 'largely due to additional RL' (Sec 3.1) is a causal claim not supported by the provided evidence. The paper only shows iLLaDA lacks RL; it does not isolate RL as the specific variable causing the performance delta versus Qwen2.5, which also differs in pre-training data and architecture.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract and introduction claim iLLaDA is 'competitive' with Qwen2.5 7B and 'slightly stronger on average' (Sec 1). However, Table 2 shows iLLaDA-Instruct (Avg 67.1) significantly underperforms Qwen2.5 7B Instruct (Avg 77.1) by ~10 points. The claim of competitiveness in the instruct setting is an over-interpretation of the data and should be qualified to reflect the substantial gap.
- **[writing]** The abstract states iLLaDA improves by '14.5 points on MATH' and '16.5 points on HumanEval' compared to LLaDA. While these deltas are numerically correct against LLaDA, the abstract frames this as a general improvement without explicitly contrasting it with Dream (which outperforms iLLaDA on HumanEval). This selective highlighting risks overstating the model's universal superiority over all diffusion baselines.
- **[writing]** The conclusion states that 'fully bidirectional diffusion training from scratch can achieve strong language modeling performance' based on iLLaDA's results. However, the paper admits iLLaDA-Instruct lags behind Qwen2.5 Instruct and attributes this to missing RL alignment. The claim that the *training paradigm itself* is fully competitive is premature without controlling for the alignment stage, which is a confounding variable in the comparison.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript lacks a dedicated 'Ethics Statement' or 'Safety Considerations' section. Given the model's strong performance on code generation (HumanEval, MBPP) and reasoning benchmarks, authors must explicitly discuss potential dual-use risks (e.g., generating malicious code, phishing, or disinformation) and mitigation strategies employed during training or inference.
- **[writing]** The paper mentions training on a 12T token corpus and a 25B token instruction set but does not specify the data sources, filtering criteria for harmful content, or whether human data privacy/consent was considered. A brief description of data curation protocols regarding safety and privacy is required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 claims iLLaDA-Base is 'slightly stronger' than Qwen2.5 7B (63.9 vs 63.3). Without reported standard deviations or multiple evaluation seeds, this 0.6-point difference may be statistically insignificant. Please report variance estimates or run multiple seeds to validate significance.
- **[science]** Figure 3 shows SFT performance plateauing after 8-10 epochs, yet the text claims continuous improvement. Please analyze if gains at 12 epochs are statistically significant versus 8 or 10 epochs and discuss overfitting risks given the small instruction corpus.
- **[science]** The claim that the Qwen2.5-Instruct gap is solely due to missing RL alignment is unverified. Please provide evidence (e.g., controlled ablation or specific citations on RL gains in diffusion) that RL accounts for the observed gap magnitude, ruling out SFT data differences.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports specific benchmark scores (e.g., 74.8 on MMLU, 71.3 on BBH) without providing standard errors, confidence intervals, or the number of random seeds used for evaluation. Given the stochastic nature of diffusion sampling and benchmark evaluation, single-point estimates are insufficient to claim statistical significance of the reported improvements over baselines.
- **[science]** In the ablation study (Sec. 4.2, Tab. 3), the authors claim confidence-based scoring 'consistently improves' over likelihood scoring. However, no statistical test (e.g., paired t-test or bootstrap) is reported to verify if the observed differences (e.g., +1.3 on PIQA) are statistically significant rather than due to random variance in the evaluation process.
- **[science]** The SFT epoch ablation (Fig. 2) shows performance trends across epochs, but the error bars or variance metrics are not described in the caption or text. Without uncertainty quantification, it is difficult to determine if the performance plateau or slight dips at higher epochs are meaningful or within the noise margin of the evaluation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (SFT), the phrase 'concatenate all formatted examples into a continuous instruction corpus' is slightly ambiguous. Clarify whether this concatenation happens before or after the random 8192-token sampling to ensure the reader understands the data pipeline flow.
- **[writing]** In Section 3.3 (Inference), the sentence 'Once a block is decoded, generation terminates if an |EOS| or other stop token appears' contains a dangling modifier. Rephrase to clarify that the termination check occurs immediately after the block decoding step, not as a condition of the decoding itself.
- **[writing]** In the Conclusion, the phrase 'This report also leaves several limitations' is awkward. Suggest changing to 'This work also has several limitations' or 'We acknowledge several limitations of this work' for better academic tone.

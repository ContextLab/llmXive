# Automated-review action items — EvalVerse: Pipeline-Aware and Expert-Calibrated Benchmarking for Professional Cinematic Video Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 5, the text cites 'Gemini 3.1 Pro' and 'Nano Banana Pro', but the bibliography only lists 'Gemini 3 Pro' and 'Nano Banana' (Gemini 2.5 Flash Image). The specific version '3.1' and the 'Pro' suffix for Nano Banana are unsupported by the provided citations. Verify model versions or update citations.
- **[writing]** Table 1 claims EvalVerse is the 'first' to cover 'Video with Sound' and 'Multi-Shot'. While the table shows others lack these, the text must ensure this 'first' claim doesn't contradict the 'Partial' or 'High' ratings given to VADB/Stable Cinemetrics in other dimensions. Clarify that the 'first' claim applies specifically to the simultaneous combination of these modalities.
- **[writing]** In Section 6, the text cites 'DINO' using the key 'oquab2023dinov2'. Since this key refers to DINOv2, the text should explicitly state 'DINOv2' to ensure the citation accurately supports the specific model capabilities used in the pipeline.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption is truncated mid-sentence at 'human aesthetic perce' and ends with a file reference '[teaser_new.pdf]' instead of completing the description of the Expert-Machine Calibration step.
- **[writing]** Figure 3: The vertical label 'Incomplete Case (Preview)' on the left panel is ambiguous; it is unclear if it refers to the specific JSON example shown or the entire annotation pipeline.
- **[science]** Figure 3: The 'Sampling' section displays multiple donut charts with percentage values, but lacks a legend or title specifying the total sample size (N) or the specific dataset subset these distributions represent.
- **[science]** Figure 4: The 'Multi-Shot cutting' and 'Sound design' categories show sparse data with only 2-3 models evaluated, while others have 10+, making direct performance comparisons across categories misleading without noting the different evaluation scopes.
- **[writing]** Figure 4: The y-axis label is missing; while gridlines and values (0.000000 to 0.900000) are present, the metric being measured (e.g., 'Win Rate', 'Score') is not explicitly labeled on the axis.
- **[writing]** Figure 4: The legend at the top is extremely dense with 11 entries, making it difficult to distinguish between similar colors (e.g., the various shades of blue and green) without careful cross-referencing.
- **[science]** Figure 5: The radar chart axes (e.g., 'Action: Action-Emotion Synergy', 'Visual Quality: Rendering Quality') are not explicitly defined as T2V-specific metrics in the caption, creating ambiguity about whether these dimensions apply to the T2V setting or are generic across all settings.
- **[writing]** Figure 5: The legend is missing from the rendered image; while model names are listed in the caption, the specific color and line-style mappings (e.g., Hailuo 2.3 vs. Wan 2.2) are not visually labeled on the figure itself, making it difficult to distinguish models without external reference.
- **[science]** Figure 5: No error bars or confidence intervals are shown on the radar chart data points, despite the caption implying a 'fine-grained performance comparison' which typically requires uncertainty quantification for scientific rigor.
- **[writing]** Figure 6: The legend is located in the bottom-left corner of the 'Visual Concept Design' subplot, which is visually disconnected from the other six subplots, making it difficult to associate the model keys with the data in the 'Acting', 'Aesthetics', and other charts.
- **[science]** Figure 6: The radar charts lack a visible numerical scale or axis ticks (e.g., 0, 2, 4, 6, 8, 10). Without these reference points, it is impossible to determine the absolute performance scores of the models, rendering the comparison purely relative and subjective.
- **[writing]** Figure 7: The caption contains a LaTeX artifact ('$$') where the Pearson correlation coefficient symbol ($\rho$) should be, rendering the text 'Pearson's $$' incomplete.
- **[writing]** Figure 7: The legend labels are cluttered and inconsistent; some entries include 'win ratio' (e.g., 'Hailuo 2.3 win ratio') while others do not (e.g., 'LTX2 win ratio'), creating visual noise.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Replace 'agentic workflows' with 'agent-based workflows' or 'workflows using autonomous agents' in the Abstract and Introduction. 'Agentic' is non-standard jargon that obscures meaning for general readers.
- **[writing]** Define 'CoT' (Chain-of-Thought) at its first occurrence in the Abstract. Currently, it appears as 'Chain-of-Thought reasoning' but the acronym 'CoT' is used immediately after without explicit definition in the abstract text itself, and later in the body without a clear 'CoT (Chain-of-Thought)' definition on first use in Section 1.
- **[writing]** Replace 'pipeline-aware' with 'aware of the production pipeline' or 'aligned with the filmmaking pipeline' in the Abstract and Section 1. 'Pipeline-aware' is a compound adjective that functions as jargon without clear definition for non-specialists.
- **[writing]** Replace 'digitization of subjective cinematic expertise' with 'converting subjective cinematic expertise into digital metrics' in the Abstract. 'Digitization' in this context is metaphorical jargon that could be clearer.
- **[writing]** Replace 'perception prior' with 'prior knowledge from perception' or 'perceptual priors' in Section 4.1.1. 'Perception prior' is technical jargon that may confuse readers unfamiliar with Bayesian terminology in this specific context.
- **[writing]** Replace 'Out-of-Domain (OOD) failures' with 'failures when encountering data outside the training distribution' in Section 5.1. While OOD is common in ML, it should be spelled out fully at first use in the main text for broader accessibility.
- **[writing]** Replace 'reward hacking' with 'exploiting the reward function to achieve high scores without genuine quality' in the Conclusion. 'Reward hacking' is a specific term of art that should be briefly explained for non-specialist readers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 5.2 (Alignment Analysis), the text claims that abstract dimensions (Multi-Shot, Sound) achieve the 'highest agreement' with humans due to SFT. However, Table 2 shows SRCC values for these dimensions (e.g., Vocal: 0.9487, Logic: 0.9000) are based on N=4 or N=5 models, whereas pixel-grounded dimensions have N=11. The small sample size for the 'highest agreement' claim creates a logical gap regarding statistical robustness and potential overfitting to specific model behaviors.
- **[science]** Section 4.2 defines the 'Context-Aware Gating' mechanism as an indicator function I_gate(p, C) that bypasses metrics if context C does not warrant them. However, the paper does not logically explain how the VLM determines 'C' (narrative context) independently of the prompt 'p' or the video content, nor how this gating is implemented without circular reasoning (i.e., the VLM must understand the context to decide whether to evaluate the context).
- **[science]** The 'Real-to-Gen' data engine (Section 3) claims to eliminate 'stochastic bias' by sampling from a professional database. However, the construction of test pairs relies on Gemini 3.1 Pro to synthesize prompts. If the prompt generation itself introduces bias or hallucination relative to the ground truth video, the claim of eliminating stochastic bias is logically unsupported, as the evaluation input is no longer a direct reflection of the source material.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that EvalVerse 'establishes a fundamental infrastructure' for RL and agentic workflows (Abstract, Conclusion) overreaches the current evidence. The paper only presents a benchmark and a fine-tuned evaluator; it does not demonstrate the framework actually training a video model via RL or driving an agent loop. Rephrase to 'potential to serve as' or provide a pilot RL experiment.
- **[science]** The statement that the framework 'successfully digitizes subjective, expert-level cinematic knowledge' (Abstract, Introduction) is an over-claim. While correlation coefficients are high (Tab. 4), the p-values for Multi-Shot and Sound Design dimensions are >0.05 (e.g., p=0.1540 for Vocal), indicating the alignment is not statistically significant for these critical 'goodness' dimensions. Qualify the claim of 'successful digitization' to reflect these statistical limitations.
- **[writing]** The assertion that the 'Real-to-Gen' data engine 'eliminates the stochastic bias inherent in existing prompt-based benchmarks' (Introduction) is too absolute. Sampling from a professional database introduces its own selection biases (e.g., genre, era, style) which are not quantified. Replace 'eliminates' with 'mitigates' and briefly acknowledge the potential for dataset-specific bias.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a sophisticated framework for evaluating professional cinematic video generation, but it raises significant safety and ethical concerns that require clarification before acceptance. First, regarding human subjects research, Section 5.1 details a "Human Evaluation Protocol" involving a multi-disciplinary team of 34 experts who performed side-by-side comparisons and provided discriminative rankings. However, the manuscript lacks an Ethics Statement or any mention of Institutiona

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The human evaluation protocol (Sec. 5.1) lacks critical statistical details: the exact number of expert annotators, their inter-annotator agreement (e.g., Krippendorff's alpha), and the total number of video samples evaluated per model. Without these, the robustness of the 'ground truth' cannot be assessed.
- **[science]** Table 2 (win_ratio) and Table 3 (correlation) report high alignment metrics, but the sample sizes (N) for the 'Multi-Shot' and 'Sound Design' dimensions are critically low (N=5 and N=4 respectively). These small N values render the reported p-values (e.g., p=0.0513) statistically unreliable and prone to Type I errors.
- **[science]** The paper claims a 'three-stage quality control pipeline' for human annotation but provides no quantitative evidence of its efficacy, such as the rejection rate of initial annotations or the specific agreement metrics between the 'Quality Inspectors' and 'Final Reviewers'.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Table 5 (tab:correlation), the p-values for 'Multi-Shot' and 'Sound Design' dimensions (e.g., p=0.0513, 0.0886) exceed the standard alpha=0.05 threshold. Given the small sample sizes (N=4 or 5), the authors must explicitly discuss the lack of statistical significance for these specific dimensions or apply a correction for multiple comparisons across the 18+ tested dimensions to avoid Type I errors.
- **[science]** The win-ratio analysis in Table 4 (tab:win_ratio) and Section 5.3.1 relies on pairwise comparisons without reporting confidence intervals or standard errors. For a benchmark claiming 'strong alignment,' the authors should provide 95% confidence intervals for the reported win ratios to quantify the uncertainty of the machine-human agreement.
- **[science]** The paper reports high correlation coefficients (SRCC/PLCC) but does not specify the statistical test used to derive the p-values in Table 5. For small sample sizes (N < 30), the assumptions of the Pearson correlation test may be violated. The authors should confirm if non-parametric tests were used or justify the parametric approach given the sample size constraints.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, the phrase 'broaden the task coverage' breaks parallelism with the preceding verbs 'retains' and 'expands'. Change to 'broadens' to maintain grammatical consistency.
- **[writing]** In Section 1 (Introduction), the sentence 'They~\cite{cinetechbench,univbench,msvbench,muss} predominantly focus...' contains a tilde before the citation command which is unnecessary and disrupts the flow. Remove the tilde or ensure it is used consistently for spacing elsewhere.
- **[writing]** In Section 5 (Machine Evaluation Suite), the phrase 'expert-guided multi-questioning' is slightly ambiguous. Consider rephrasing to 'expert-guided multi-question prompts' or 'expert-designed multi-question sets' for clarity.
- **[writing]** In Section 6 (Human-Machine Calibration), the phrase 'data-driven weight optimization trick' uses the word 'trick' which is informal for a scientific paper. Replace with 'method', 'strategy', or 'approach'.
- **[writing]** In the Conclusion, the phrase 'computer graphics community' lacks a definite article. It should read 'the computer graphics community'.

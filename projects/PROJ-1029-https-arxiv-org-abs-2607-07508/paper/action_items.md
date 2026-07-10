# Automated-review action items — https://arxiv.org/abs/2607.07508

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several specific factual claims regarding model versions and performance metrics that require verification against the provided evidence. First, the Abstract explicitly states that the method was deployed to train the "open GLM-5.2 model (750B-A40B)". However, the bibliography and the rest of the text only reference "GLM-4.5" and "GLM-4.7". There is no citation or public record for a "GLM-5.2" model in the provided references. This appears to be a hallucinated model version or a

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains multiple grammatical errors and missing subject names (e.g., 'performance of on reasoning', 'outperforms the corresponding baseline'), making it difficult to identify the proposed method.
- **[writing]** Figure 1: The x-axis label 'HMMT Nov 2025' contains a future date, which is likely a typo or placeholder error.
- **[writing]** Figure 2: The caption contains placeholders ('Overview of with...', 'For , each trajectory...') where the method name 'SAO' should appear, making the text grammatically incomplete and unclear.
- **[writing]** Figure 2: The caption refers to 'GRPO' and 'SAO' (implied by the image) but fails to explicitly name the proposed method in the opening sentence, relying on the image labels instead of the text.
- **[science]** Figure 3: The caption claims the figure shows performance on 'different benchmarks' and that results for 'remaining benchmarks' are in the Appendix, but the plot title is 'AIME 2025' and the data shows only a single benchmark. This contradicts the caption's claim of multiple benchmarks.
- **[writing]** Figure 3: The legend labels 'SAO' and 'GRPO (w/ DIS)' do not match the method name 'SAO' (or similar) implied by the caption's 'outperforms the corresponding baseline' phrasing, creating ambiguity about which method is the proposed one.
- **[fatal]** Figure 4: The figure has no caption provided, making it impossible to verify what the plotted data represents or if the figure supports the paper's claims.
- **[science]** Figure 4: The legend labels 'SAO' and 'SAO w/o Faster value' are undefined in the caption and do not match the method names (e.g., 'GRPO', 'DIS') used in the paper's text or other figure captions.
- **[science]** Figure 5: The caption describes 'changing writing-style preferences' but does not define the four categories (Academic, Cute, Classical, Chuunibyou) or explain the experimental protocol (e.g., why 'Cute' drops at step 150 and 'Classical' rises at step 300). Without this context, the plot is an unexplained sequence of events rather than a clear simulation of preference shifts.
- **[writing]** Figure 5: The legend uses the term 'Chuunibyou' without defining it in the caption or text, which may be obscure to a general scientific audience.
- **[science]** Figure 6: The caption claims 'token-level shows better training rewards,' but the legend labels the top-performing method as 'SAO' and the lower-performing methods as 'Step-level' variants. The caption fails to explicitly identify 'SAO' as the token-level method, creating a disconnect between the visual data and the textual claim.
- **[writing]** Figure 6: The legend uses the term 'Step-level(Average)' and 'Step-level(Last-Token)' but does not define what 'SAO' stands for, assuming the reader knows the acronym without providing the full name in the caption or legend.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 4.1 introduces the term 'TTUR' in the phrase 'single-rollout and TTUR mechanisms' without ever defining it. While 'TTUR' (Two-Timescale Update Rule) is a known concept in RL, it is not defined in the text, and the acronym is not expanded at first use. Define it upon first mention (e.g., 'Two-Timescale Update Rule (TTUR)') or remove the acronym if the concept is already described as 'faster value updates'.
- **[writing]** Section 4.1 uses the acronym 'DIS' (Direct Double-Sided Importance Sampling) in the subsection title and text, but the acronym is never explicitly defined in the body text. The full name appears in the title but not in the prose where the acronym is first used. Add '(DIS)' immediately after the first full mention of the method in the text.
- **[writing]** Section 5.1 mentions 'length-adaptive GAE' and provides a formula for $\lambda_{	ext{policy}}$, but does not explicitly define the variable $lpha$ in the text (it only appears in the formula). While the formula implies $lpha$ is a scaling factor, a competent adjacent-field reader would benefit from a brief clause defining it (e.g., 'where $lpha$ is a scaling hyperparameter').

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 5.3 claims 'all variants decline' but references Table 1 (main results) instead of Table 3 (ablations). Clarify that the decline claim applies specifically to the ablation rows in Table 3 to avoid logical confusion with the main comparison.
- **[writing]** Section 4.1 states tokens are 'masked from gradient computation' while Eq 3 sets f(x)=0. Clarify if this means the loss term is zeroed (gradient is zero) or the token is removed from the batch to ensure implementation logic matches the textual description.
- **[writing]** Section 5.4 introduces 'three archetypes' (cute, chuunibyou, classical) but the setup uses a pool of four (adding Academic). Clarify if Academic was a distractor or if the 'three archetypes' description was imprecise to align the premise with the experimental design.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper presents a compelling technical contribution regarding asynchronous RL stability, but the rhetoric in the Abstract and Conclusion frequently exceeds the scope of the provided evidence. The most significant overreach occurs in the Abstract, which states: "To this end, \model{} is successfully deployed in the agentic RL pipeline for training the open GLM-5.2 model (750B-A40B)." This is a claim of real-world deployment at a massive scale (750B parameters) that is completely absent from th

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a methodological advancement in asynchronous reinforcement learning for large language models (SAO), focusing on training stability and efficiency. From a safety and ethics perspective, the work does not introduce foreseeable, non-trivial risks that are unaddressed.

The research involves training models on standard reasoning and coding benchmarks (e.g., AIME, SWE-Bench) and a simulated online writing task. The data sources appear to be public benchmarks or synthetic data generated by other models (e.g., GPT-OSS-120B), with no indication of using private, sensitive, or non-consented human data. Consequently, no IRB/consent statements are required, and the absence of such a statement is not a violation.

The paper includes a "Limitations and Broader Impact" section (Section 7, Appendix) that appropriately acknowledges the potential for dual-use. It explicitly states that the improved stability and efficiency could lower the cost of training capable agentic systems, which might be misused for harmful objectives if deployed without safeguards. The authors correctly identify that responsible release, data filtering, and access controls are necessary for any downstream deployment. This disclosure is sufficient for a methodological paper of this nature; it does not require a detailed mitigation plan for hypothetical misuse, as the method itself (an optimization algorithm) is not a direct tool for harm (unlike, for example, a specific exploit generator or a deepfake synthesis tool).

There are no operational details provided that would enable immediate cyberattacks or biohazard synthesis. The "online learning" experiment is a controlled simulation of stylistic shifts, not a deployment in a live user environment, and the authors note the need for safeguards if such a system were deployed in reality.

Therefore, the paper meets the safety and ethics standards for publication with no specific action items required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method for asynchronous RL, but the experimental design contains specific gaps that prevent the evidence from fully supporting the central claims regarding the efficacy of the "single-rollout" strategy versus group-wise sampling. First, the primary results in Tables 1 and 2 report single-point accuracy numbers (e.g., 97.3% vs 94.2% on AIME2025) without any indication of variance, standard deviation, or the number of random seeds used. Reinforcement learning traini

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1 and 2 report only point estimates (e.g., 97.3%) without uncertainty metrics. Section 5.1 mentions averaging over 16 runs, but the tables lack mean ± SD or SE. Report standard deviation or confidence intervals for all benchmark results to assess variance.
- **[writing]** Claims of 'consistent outperformance' (Abstract, Sec 5.2) lack statistical tests or multiple-comparison correction across 4 benchmarks and multiple baselines. Either report p-values from paired tests or soften language to 'higher mean performance' without implying significance.
- **[writing]** Figures 3 and 4 show shaded regions but do not define them (e.g., ±1 SD, 95% CI) or state the number of seeds (N). Update captions to specify the metric and N to validate stability claims visually presented.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper presents a clear technical contribution, but the prose contains several friction points that require a reader to pause, re-read, or guess at the intended meaning. The most significant issues involve grammatical errors, awkward phrasing, and inconsistent sentence structures that disrupt the flow of the argument. In the Abstract, the phrase "changing evolving environments" is redundant and should be simplified. The final sentence regarding the deployment of the GLM-5.2 model is vague; it

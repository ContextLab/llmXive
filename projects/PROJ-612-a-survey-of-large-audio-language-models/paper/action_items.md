# Automated-review action items — A Survey of Large Audio Language Models: Generalization, Trustworthiness, and Outlook

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 5.1.3 claims MMSU [wang2025mmsu] reveals 53.60% and 39.35% accuracy on phonology and paralinguistics. The citation key 'wang2025mmsu' appears in the bibliography but the specific numeric breakdown is not verifiable in the provided text summary. Verify these exact figures against the source paper to ensure they are not conflated with other benchmarks.
- **[writing]** Section 5.3.1 states JALMBench [peng2025jalmbench] shows audio attacks achieve 21.5% success vs 17.0% for text. The text summary lists '21.5' and '17.0' as critical elements but does not explicitly link them to this specific comparison in the source text. Confirm the source paper supports this specific head-to-head comparison and that the numbers are not from different experimental settings.
- **[writing]** Section 5.2.1 claims ChronosAudio [luo2026chronosaudio] reveals performance drops exceeding 90% in long contexts. The text summary lists '90' as a critical element. Verify if the source paper reports a 'drop exceeding 90%' (i.e., remaining accuracy <10%) or if the metric is different (e.g., 90% of tasks failed). Ensure the phrasing 'exceeding 90%' accurately reflects the data.
- **[writing]** Section 5.3.2 claims AudioTrust [li2025audiotrust] reveals open-source models have >35% bypass rates for voice cloning. The text summary lists '35' as a critical element. Verify the specific metric (bypass rate) and the threshold (35%) in the source paper, as 'bypass rate' can be defined differently across security benchmarks.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The caption claims a 'comparative analysis' between 'standard LALM' and 'Audio-CoT', but the figure only visualizes the Audio-CoT workflow. The 'standard direct-response' model mentioned in the caption is not shown, making the comparison impossible to verify visually.
- **[writing]** Figure 2: The caption contains a missing space after the period in 'Audio-CoT.This', which affects readability.
- **[writing]** Figure 3: The label 'Stanard/Dialect' in the Fairness example box contains a typo and should be 'Standard/Dialect'.
- **[writing]** Figure 3: The 'Hallucination' example box contains a grammatical error ('Mr.John' should be 'Mr. John' with a space).
- **[science]** Figure 4: The x-axis timeline is logically inconsistent; the '2025.1-3' period is placed to the right of '2024-before' but to the left of '2025.4-6', yet the '2025.1-3' label is visually positioned after '2024-before' while the '2025.4-6' label is further right, creating a confusing non-linear or broken sequence that contradicts the caption's claim of tracking growth over time.
- **[writing]** Figure 4: The y-axis label 'Number of Papers(cumulated)' contains a grammatical error; 'cumulated' should be 'cumulative' to match standard scientific terminology and the caption's phrasing.
- **[science]** Figure 4: The data points (yellow diamonds) and their corresponding numerical labels (e.g., '1+', '4+', '10+') do not align with the y-axis scale; for instance, the '10+' point is plotted near y=10, but the '13+' point is plotted near y=13, while the '12+' point is plotted near y=12, suggesting the y-axis values are not accurately representing the cumulative count as implied by the axis label.
- **[writing]** Figure 5: The caption is a verbatim duplicate of Figure 1's caption, suggesting a copy-paste error in the manuscript preparation.
- **[writing]** Figure 5: The title 'Trustworthy LALM Evaluation' is rendered in a casual, handwritten-style font that is inconsistent with the professional tone of a scientific survey.
- **[science]** Figure 6: The caption claims a 'comparative analysis' between standard LALMs and Audio-CoT, but the figure only visualizes the Audio-CoT workflow. It lacks the 'standard direct-response' model side to support the comparison.
- **[writing]** Figure 6: The caption contains a missing space after the period in 'Audio-CoT.This', which affects readability.
- **[writing]** Figure 7: The label 'Stanard/Dialect' in the Fairness example box contains a typo and should be 'Standard/Dialect'.
- **[writing]** Figure 7: The 'Hallucination' example box contains a grammatical error ('Mr.John' should be 'Mr. John' with a space).
- **[writing]** Figure 8: The caption contains a grammatical error ('surge in almost scholarly publications') which likely should read 'a surge in scholarly publications' or 'almost 20 publications'.
- **[science]** Figure 8: The x-axis timeline projects into the future (2025.4-6 through 2026.1-3), implying the chart predicts or includes future data points rather than tracking historical research, which contradicts the caption's claim to 'track' existing publications.
- **[writing]** Figure 8: The y-axis label 'Number of Papers(cumulated)' uses non-standard terminology; 'Cumulative Count' or 'Cumulative Number' is standard.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, frequently employing specialized terminology from signal processing, economics, and deep learning without definition or simplification. This creates a barrier for non-specialist readers, violating the goal of a comprehensive survey. In the Introduction and Section 1, terms like "non-stationary auditory signals," "structured semantic latent spaces," and "Endogenous Mechanisms" are used without explanation. "Endogenous" is particularly unnece

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The conclusion claims a 'developmental asymmetry' where offensive research is mature and defenses are rudimentary. However, Section 5.3.1 and 5.3.2 list numerous specific defense mechanisms (ALMGuard, SARSteer, AudioSafe) and benchmarks. The text must clarify whether the 'rudimentary' claim refers to the *effectiveness* of these defenses rather than their *existence*, or provide evidence that these defenses fail in practice to support the causal claim.
- **[writing]** Section 5.2.1 cites ChronosAudio showing >90% performance drop due to 'Structural Attention Dilution'. The paper does not define this mechanism or explain the causal link between attention dilution and the specific magnitude of the drop. The argument relies on an undefined term to explain a quantitative result, breaking the logical chain.
- **[science]** The 'Future Outlook' (Sec 5.4) proposes 'Causal Auditory World Modeling' as a solution to hallucination. The paper defines hallucination as a failure of acoustic grounding (Sec 5.1) but does not logically demonstrate why 'world modeling' (a counterfactual reasoning capability) is the necessary or sufficient condition to fix grounding failures, rather than just better alignment.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that 'offensive research is mature, while defenses are rudimentary' (Conclusion, Sec 5.4) is an over-generalization. The paper cites numerous specific defense mechanisms (ALMGuard, SARSteer, AudioSafe) with quantitative results. The authors should qualify this claim to reflect that defenses are 'fragmented' or 'less standardized' rather than 'rudimentary' to avoid dismissing valid existing work.
- **[writing]** The assertion that LALMs 'infer gender with >92% accuracy' (Sec 5.3.2) based on HearSay is presented as a universal capability of the class of models. This extrapolates from a specific benchmark result to a general property of all LALMs without clarifying if this applies to all architectures or only those tested on that specific dataset. The scope of this claim needs tightening.
- **[writing]** The paper claims a 'Perception-Cognition Gap' and 'Denoising Paradox' (Sec 5.1.1) as established phenomena. While supported by RSA-Bench, presenting these as definitive, named laws of LALM behavior without acknowledging they are specific findings of one benchmark risks over-claiming the universality of these specific failure modes across the entire field.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript extensively details offensive capabilities (jailbreaks, backdoors, privacy leakage) in Sections 5.3.1 and 5.3.2. To prevent dual-use harm, the authors must explicitly state that the provided attack taxonomies and success rates are for defensive benchmarking only and should not be used to generate new adversarial examples without strict ethical oversight.
- **[writing]** Section 5.3.2 cites 'HearSay' regarding identity inference (>92% accuracy) and 'AGL1K' for geo-localization. The paper must clarify the consent status of the datasets used in these cited works. If the data involves non-consensual biometric inference, the survey should include a dedicated ethical warning about the deployment risks of such models in surveillance contexts.
- **[writing]** The 'Future Outlook' proposes 'Automated Red Teaming agents' (Sec 5.4). The authors should add a brief discussion on the safety protocols required to prevent these autonomous agents from inadvertently generating harmful content or escalating attacks during the evaluation process.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that JALMBench shows audio attacks achieve 21.5% success vs 17.0% for text (Sec 5.3.1) lacks statistical context. Please report the sample size (N), confidence intervals, or p-values to confirm this difference is not due to random variance or dataset bias.
- **[science]** The assertion that ChronosAudio reveals performance drops exceeding 90% in long contexts (Sec 5.2.1) requires clarification on the baseline. Specify the exact metric (e.g., accuracy, F1), the specific model tested, and the control condition (short context) to validate the magnitude of the reported degradation.
- **[science]** The statement that AudioSafe backdoors achieve >90% success with only 3% poisoning (Sec 5.3.1) needs methodological detail. Define the poisoning strategy, the target model architecture, and the evaluation protocol to ensure the result is robust and not an artifact of a specific, non-representative setup.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.1.2 cites BRACE achieving 63.19 F1. As a survey, clarify if this is a single-point estimate or an aggregate. If aggregated, report the number of models tested (N) and the variance (SD/CI) to assess the stability of this claim against the 'best model' framing.
- **[science]** Section 5.3.1 states audio attacks achieve 21.5% success vs 17.0% for text. Specify the statistical test used to determine if this 4.5% difference is significant (e.g., McNemar's test for paired data or a z-test for proportions) and report the p-value or confidence interval.
- **[science]** Section 5.2.2 claims answer permutation changes accuracy by 'up to 24%'. Define the baseline (random chance vs. original order) and the sample size (N) of the permutation test. Without N and variance, this 'up to' claim lacks statistical rigor.
- **[writing]** Table 1 and Table 2 list numerous benchmarks with specific metrics (e.g., WER, Accuracy). For any benchmark where the authors summarize performance across multiple models, ensure the text or table footnotes specify if the reported value is the mean, median, or best-case, and include the standard deviation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5.1.2, the sentence 'BRACE [cite] shows the best LALM achieves only 63.19 F1 on reference-free caption alignment' lacks a clear subject-verb connection to the benchmark name. Rephrase to explicitly state that the benchmark 'BRACE' evaluates this metric, e.g., 'On the BRACE benchmark, the best LALM achieves...'
- **[writing]** The Introduction (e001) and Section 5 (e000) contain nearly identical definitions of the three evaluation pillars (Fidelity, Stability, Alignment) and the same figure/table references. This redundancy disrupts the narrative flow. Consolidate the detailed taxonomy into Section 5 and keep the Introduction summary high-level.
- **[writing]** In Section 5.3.1, the phrase 'Safety under Emotional Variations [cite] reveals Emotional Hijacking...' uses a paper title as a proper noun subject. Cite the specific author or model name if available, or rephrase to 'Research on safety under emotional variations [cite] reveals...'
- **[writing]** Table 1 (e001) and Table 2 (e002) both use custom macros like \YearRow and \tablogo which are not defined in the provided snippets. While this is a compilation issue, the text flow is interrupted by these undefined commands. Ensure all custom commands are defined in the preamble or replace with standard LaTeX to ensure readability of the source.

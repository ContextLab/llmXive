# Automated-review action items — MemSlides: A Hierarchical Memory Driven Agent Framework for Personalized Slide Generation with Multi-turn Local Revision

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Correct the claim in Section 5.1.1/Appendix A.4 that MemSlides achieves the highest Avg. on GLM-5. Table 3 shows DeepPresenter (3.86) exceeds MemSlides (3.74) for GLM-5 Avg. Update text to reflect this accurately.
- **[writing]** Clarify in Section 5.1.2 that the reported reduction in 'Time to First Correct Edit' (609.5s to 242.5s) is an aggregate across models with heterogeneous baselines, not a uniform per-model reduction, to avoid overgeneralization.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The generated slides contain specific technical content (e.g., 'BLEU 28.4', 'WMT14', 'EN-DE BLEU') that is not present in the corresponding template slides above them. The caption claims these are 'matched persona/template generations,' but the figure fails to demonstrate how the template structure was used to generate this specific content, making the 'template-guided' claim unsubstantiated by the visual evidence.
- **[writing]** Figure 1: The text within the 'Generated Slide' panels (e.g., the table in panel 3, the bullet points in panel 2) is extremely small and illegible at the current resolution, preventing verification of the content or the quality of the generation.
- **[science]** Figure 3: The 'Injected memory' workflow shows a database icon labeled 'Memory' feeding into a 'Prompt' document, but the diagram lacks a clear visual representation of the 'Memory Injection' mechanism itself (e.g., an arrow or process step showing how the stored rule is retrieved and inserted into the prompt).
- **[writing]** Figure 3: The text inside the 'Limitations and Future Work' boxes is extremely small and partially illegible, making it difficult to read the specific bullet points describing the limitations.
- **[writing]** Figure 4: The caption reads 'Overview of .' with a missing noun (likely 'MemSlides' or 'the framework'), rendering the sentence grammatically incomplete.
- **[writing]** Figure 4: The caption uses the notation '$s_t+1$' for the updated state, whereas the diagram explicitly labels the output as '$S_{t+1}$'; the caption should match the figure's subscript formatting.
- **[writing]** Figure 5: The caption contains a grammatical error and missing reference: 'Localized modify execution in .' should specify the framework name (e.g., 'in MemSlides').
- **[writing]** Figure 5: The caption label '[localized_tool_pipline]' contains a typo ('pipline' instead of 'pipeline').
- **[writing]** Figure 6: The caption contains a grammatical error ('User profile memory lifecycle in .') where the system name is missing after the preposition 'in'.
- **[writing]** Figure 6: The diagram uses the term 'TempPreference' in the purple boxes, but the caption refers to this as 'active temporary memory'; aligning these terms would improve clarity.
- **[writing]** Figure 7: The caption contains a grammatical error and missing noun in the opening sentence ('Tool memory flow in .'), likely a placeholder for the framework name (e.g., MemSlides) that was not filled in.
- **[writing]** Figure 7: The diagram contains several instances of small, low-resolution text (e.g., inside the 'Memory Consolidation' and 'Operation' boxes) that is difficult to read and may be illegible in lower-resolution views.
- **[science]** Figure 8: The caption states 'DeepPresenter can satisfy the target change while altering non-target regions,' but the visual evidence in Panel B (DeepPresenter) shows the formula block was removed entirely rather than altered, and the layout was rewritten, contradicting the claim of merely 'altering' non-target regions.
- **[writing]** Figure 8: The caption contains a grammatical error where the subject is missing in the second sentence ('instead applies a targeted patch...'); it should explicitly name 'MemSlides' to match the figure labels.
- **[writing]** Figure 9: The figure contains 12 distinct panels (4 columns x 3 rows) but the caption only describes 'six repeated jobs', creating a mismatch between the visual evidence count and the described experimental scope.
- **[writing]** Figure 9: The bottom row labels ('Inherited guardrail', 'Stable execution closure', 'Boundary-Centered Overview', 'Reusable Checklist') are not explicitly defined in the caption, which only lists the four patterns in a general sentence without mapping them to the specific visual examples.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that, while standard in specific agent-memory sub-fields, creates barriers for a broader audience. The most significant issue is the use of undefined acronyms and statistical jargon. In Appendix A.1, the term "arm" is used repeatedly to describe the experimental conditions (e.g., "anonymous arm label," "memory condition are hidden"). This is standard clinical trial terminology but is opaque to general readers; "condition" or "variant" woul

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify the causal mechanism in Section 5.1.2: how does retrieving 'tool memory' explicitly force the agent to perform a 'verify' step? The premise that memory stores experience does not logically entail a policy change to increase verification rates without further explanation.
- **[science]** Resolve the contradiction in Section 5.1.1: The text claims 'joint movement of Structure and Specificity' proves planning gains, yet Table 1 shows MemSlides underperforms DeepPresenter on Structure for GPT-5 (7.33 vs 7.56). The conclusion does not follow from the data for this model.
- **[science]** Address the metric definition gap in Section 5.1.2: 'Core Tool Time' excludes inspection tools, yet 'Strict Verify' (an inspection) increases. The claim of net efficiency gain is unsupported if the excluded verification time outweighs the saved search time.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that tool memory 'improves closed-loop modify behavior' (Abstract) overgeneralizes the diagnostic matched-pair results. The data shows non-monotonic pair-level outcomes (e.g., P2 and P7 losses in Table 1 pair details). The text must explicitly qualify these gains as 'diagnostic' and avoid implying universal reliability improvements without broader distributional evidence.
- **[writing]** The conclusion states MemSlides 'supports round-0 persona alignment' as a definitive outcome, but the GPT-5 results in Table 1 show mixed performance (e.g., lower Structure than DeepPresenter). The conclusion should be tempered to reflect that persona alignment improvements are model-dependent and not uniformly dominant across all dimensions.
- **[writing]** The abstract claims working memory 'carries over preferences' based on qualitative cases (Appendix Fig 2). This extrapolates beyond the evidence scope, as no quantitative metric validates carryover. The text should clarify that working memory benefits are illustrated qualitatively rather than statistically proven.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader Impacts' section defers privacy controls to future work. Explicitly detail current technical safeguards (e.g., encryption, user-accessible memory deletion) implemented in the prototype to mitigate risks of storing sensitive user profiles.
- **[writing]** Clarify if the 'profile bank' (Appendix) uses any real user data. If real data was used for seeding or validation, provide an IRB exemption statement or consent protocol. If entirely synthetic, state this explicitly to avoid ambiguity regarding human subjects.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The tool-memory evaluation relies on only nine matched pairs (Appendix Table 2). While the sign test shows significance for Strict Verify and Core Tool Time Ratio, the sample size is too small to rule out random variance or specific prompt sensitivity. The authors should explicitly frame these as 'diagnostic' findings and avoid generalizing to 'reliable localized editing' without a larger, randomized test set.
- **[science]** The persona-alignment results (Table 1) show large effect sizes (e.g., +3.30 on Content for GPT-5), but the evaluation relies on LLM-as-a-judge without reporting inter-rater reliability (e.g., Cohen's kappa) or variance across the three blind votes per dimension. Without this, the robustness of the 0-10 scale scores against judge bias is unclear.
- **[science]** The profile bank construction involves a 'seeded completion' step using a registry to fill missing fields (Appendix A.4). This introduces a potential confound where the 'memory' effect might partly reflect the quality of the seed registry rather than the agent's ability to learn from history. The analysis should control for or discuss the impact of this synthetic data generation on the persona-alignment scores.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The sign test in Appendix Table 5 (tool_memory_paired_robustness_table.tex) reports p-values for N=9 pairs. For 'Closed-Loop Completion' (3 wins, 1 loss), the p-value is 0.3125. The text describes this as 'Directional' but does not explicitly state that the result is not statistically significant at alpha=0.05. Clarify the interpretation of non-significant p-values in the main text to avoid overclaiming robustness.
- **[science]** Table 4 (tool_memory_main_table.tex) reports 'Core Tool Time Ratio' as a geometric mean. The text states the ratio is 0.327x. However, the table footnote and text do not specify the confidence interval or standard error for this geometric mean, which is critical for assessing the stability of the efficiency claim given the small sample size (N=9 pairs). Add uncertainty estimates.
- **[science]** The persona-alignment scores in Table 1 (profile_memory_v6_bestof_main_table.tex) are averages of three blind votes per dimension. The paper does not report the inter-rater reliability (e.g., Krippendorff's alpha or Cohen's kappa) for these LLM-as-judge evaluations. Without this metric, the reliability of the 0-10 scale differences (e.g., +2.42) cannot be statistically validated.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (Problem Formulation), the phrase 'Therefore, repeatedly regenerating the full deck is undesirable' is slightly informal. Consider revising to 'Consequently, repeated full-deck regeneration is suboptimal' to better match the technical tone of the surrounding equations.
- **[writing]** In Section 3 (Tool Memory), the sentence 'In \methodname, tool memory is organized two execution flows' contains a missing preposition. It should read 'organized into two execution flows' or 'organized as two execution flows'.
- **[writing]** In the Abstract, the phrase 'carryover preferences' is used as a verb phrase ('ability to carryover preferences'). 'Carryover' is typically a noun or adjective; the verb form is 'carry over' (two words). Please correct to 'carry over preferences'.
- **[writing]** In Section 5 (Analysis and Discussion), the subheading 'The gains are planning-level persona gains' is repetitive. Consider rephrasing to 'The gains reflect planning-level persona alignment' for better flow and clarity.

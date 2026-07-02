# Automated-review action items — AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Agents under World and User Constraints

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.1 (Results), the claim that 'Accuracy correlates with ATWC (0.898) and ATUC (0.919)' lacks citation to the specific calculation or table. While Table 2 lists these values, the text implies a statistical correlation coefficient (Pearson/Spearman) was computed across models. The manuscript must explicitly state the correlation metric used and confirm these numbers represent correlation coefficients, not raw metric values, to avoid misinterpretation.
- **[writing]** The claim in Section 4.1 that 'GPT-5-Mini matches GPT-5 accuracy' is statistically imprecise. Table 2 shows GPT-5 at 67.75% and GPT-5-Mini at 61.89%. While the 95% Wald confidence intervals (Appendix C) overlap (approx. ±5.2%), stating they 'match' overstates the evidence. The text should clarify that the difference is not statistically significant at the 95% level rather than claiming they are equal.
- **[writing]** In Section 4.2, the claim that 'User constraints contribute disproportionate difficulty' relies on Figure 3 (dual ablation). The text states 'User-Constraint Only is harder than World-Constraint Only' but does not provide the specific accuracy drop percentages for these ablation conditions in the text. To support the 'disproportionate' claim, the specific performance deltas for the ablation study should be cited or summarized in the prose.

## paper_reviewer_figure_critic — verdict: accept

### Figure 1

Figure 1 effectively illustrates the trajectory-level human review interface described in the caption. It clearly displays the task query, the multi-turn dialogue between the user and agent, and the violated constraints section, providing a complete and legible example of the annotation process.

### Figure 2

Figure 2 clearly displays the human annotation interface for evaluating simulated user feedback, with well-defined questions and rating scales that align with the caption's description.

### Figure 3

Figure 3 clearly displays the human annotation interface for rubric-based plan evaluation, showing the specific rubric dimension (Autonomy), detailed scoring anchors, the agent's generated plan, and the selection input. The visual content aligns perfectly with the caption's description of the interface components.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and domain-specific phrasing that could be simplified to improve accessibility for a broader audience. First, the paper introduces several acronyms without defining them at their first occurrence. Specifically, VPR (Valid Plan Rate) appears in Table 1 and Section 2.1 without being spelled out in the preceding text. Similarly, AWRV and AURV (Average World/User Repeated Violations) are introduced in Section 2.1 and Table 1 without definition. T

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent logical framework for evaluating adaptive planning, but several causal claims require stronger statistical or methodological justification to fully support the conclusions. First, in Section 4.2, the authors state that "Accuracy correlates with ATWC (0.898) and ATUC (0.919)." While high correlation coefficients are reported, the text does not specify the correlation metric used (e.g., Pearson vs. Spearman) nor does it provide p-values or confidence intervals for the

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that 'GPT-5-Mini matches GPT-5 accuracy' (Section 5, paragraph 4) is an over-interpretation of the data. Table 2 shows a 5.86% absolute gap (61.89% vs 67.75%) with non-overlapping 95% Wald confidence intervals (±5.43 vs ±5.23). The authors should qualify this as 'comparable' or 'statistically indistinguishable at a relaxed threshold' rather than 'matches', or provide a formal significance test.
- **[science]** The assertion that 'Accuracy correlates with ATWC (0.898) and ATUC (0.919)' (Section 5, paragraph 3) extrapolates beyond the provided evidence. The text does not specify if these are Pearson/Spearman coefficients, nor does it report p-values or confidence intervals for these correlations. Given the small sample size (N=10 models), claiming such strong correlations without statistical validation is an overreach.
- **[science]** The conclusion that 'User constraints contribute disproportionate difficulty' (Section 6) relies on visual inspection of Figure 5 (dual ablation) without reporting statistical significance tests (e.g., paired t-tests or ANOVA) between the 'World-Only', 'User-Only', and 'Both' conditions. The observed differences may not be statistically significant given the variance in model performance.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The ethics statement claims the dataset is 'manually validated to be free of offensive material' (Section: Ethics statement), but the methodology relies on LLMs (GPT-5.4) to generate and filter constraints. Clarify the extent of human oversight in the data construction pipeline to ensure no harmful or biased constraints were inadvertently generated and retained.
- **[writing]** The benchmark simulates user interactions where an LLM acts as a user providing feedback on plans (Section: Runtime Interaction Details). Explicitly state whether this simulation was tested for potential to generate harmful, harassing, or psychologically distressing feedback scenarios, and confirm that safety filters were applied to the user simulator's output.
- **[writing]** The evaluation rubric includes a 'Safety' dimension (Table: rubrics-details), yet the error cases (Appendix: Error Case Study) focus on physical grounding and effectiveness. Provide evidence or a brief discussion on how the benchmark specifically tests for safety-critical failures (e.g., plans causing physical harm) to ensure the 'Safety' rubric is not merely theoretical.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that 'Accuracy correlates with ATWC (0.898) and ATUC (0.919)' (Section 5.1) lacks statistical rigor. Report the sample size (N) used for this correlation, the specific correlation coefficient (Pearson/Spearman), and a p-value to confirm significance, rather than just the coefficient.
- **[science]** The human annotation study (Appendix B) uses 240 trajectories but states 'Each trajectory is annotated once by a single annotator.' This design prevents the calculation of inter-annotator agreement (e.g., Cohen's Kappa), which is essential to validate the reliability of the human ground truth used to calibrate LLM judges.
- **[science]** The paper reports 95% Wald confidence intervals for accuracy on N=307 samples (Appendix C). However, the Wald interval is known to perform poorly for proportions near 0 or 1 (e.g., GPT-5's 67.75% is acceptable, but lower scores like 1.31% at gamma=5.00 are not). Justify the choice of Wald over Wilson or Agresti-Coull intervals, or provide the corrected intervals.
- **[science]** The 'Rubric Refinement' experiment (Section 6.2) shows a sharp drop in Valid Plan Rate (VPR) when rubric feedback is added. The paper attributes this to 'recency-biased adaptation' but does not provide a statistical test (e.g., paired t-test or McNemar's test) to confirm that the drop in VPR is significant compared to the baseline, nor does it quantify the trade-off magnitude.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports 95% Wald confidence intervals for accuracy (N=307) in Appendix~ef{app:CI} and Table~ef{tab:model_acc_ci}. However, Wald intervals are known to perform poorly for proportions near 0 or 1 and for small sample sizes. Given the wide range of accuracies (14% to 67%), the authors should justify the choice of Wald intervals or switch to a more robust method (e.g., Wilson score or Clopper-Pearson) to ensure the reported error bars are statistically valid.
- **[science]** In Section~ef{app:human-annotation-llm-judge-check}, the authors claim high consistency among three LLM judges based on a mean standard deviation < 0.30. The statistical test or metric used to establish 'stability' versus 'severe disagreement' is not defined. Please specify the statistical threshold or reference a standard metric (e.g., Krippendorff's alpha) used to validate this consistency claim.
- **[science]** The correlation coefficients (0.898, 0.919) between accuracy and constraint exploration metrics (ATWC/ATUC) are reported in Section~ef{sec:experiment} without confidence intervals or p-values. Given the small sample size (N=10 models), these correlations may be unstable. Please report the significance of these correlations or the confidence intervals for the coefficients.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 'Model Choice' (Appendix), the label 'app:model_choise' contains a typo ('choise' instead of 'choice'). While this is a LaTeX label, the section heading 'Model Choice' is correct, but the inconsistency in the label suggests a potential copy-paste error in the text or a lack of proofreading. Please verify all section labels match their intended text.
- **[writing]** In the 'Limitations' section, the paragraph 'Text-only Evaluation Setting' lacks a period at the end of the final sentence ('...low-level control noise'). Ensure all paragraphs end with proper punctuation.
- **[writing]** In the 'Formalization' section, the subsection 'Intuition Behind' (label: app:env_cons_intuition) has a grammatically incomplete title. It should be 'Intuition Behind the Pipeline' or 'Intuition Behind the Algorithm' to be a complete noun phrase.
- **[writing]** In the 'Experiment Details' section, the subsection 'Model Choice' (label: app:model_choise) repeats the typo 'choise' in the label. Additionally, the text 'Judge-LLM Choice in Evaluation' uses a hyphen that is inconsistent with 'Model Choice' (no hyphen). Standardize the capitalization and hyphenation of these subheadings.

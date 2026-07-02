# Automated-review action items — Agent Explorative Policy Optimization for Multimodal Agentic Reasoning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify the '8B surpasses 32B Base' claim in Abstract/Intro. Table 4 shows 8B AXPO (75.8) vs 32B Base (75.1). Ensure the text explicitly states this compares against the *untrained* 32B baseline to avoid implying it beats a trained 32B agent, which would be a stronger, unverified claim.
- **[writing]** The claim that tool-using subgroups are 'all-wrong on ~40% of questions' (Intro, Sec 2.1) cites Fig 3b. Specify if this 40% is an average across steps or a specific snapshot, as the figure shows a trend. This prevents ambiguity about whether the statistic is static or dynamic.
- **[writing]** The claim that resampling preserves 'substantive diversity' (Sec 2.1) cites Fig 3c (2.9-3.4 clusters). Briefly mention the clustering method (LLM-judged intent) in the text to ground 'diversity' in the specific semantic metric, not just syntactic variation.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The caption contains a formatting artifact '4$$' instead of '4x' or '4x larger'.
- **[writing]** Figure 2: The x-axis label 'Model size (log scale)' is technically inaccurate as the tick spacing (2B, 4B, 8B, 32B) represents a linear doubling progression rather than a logarithmic scale.
- **[science]** Figure 3: The legend labels ('All Tool', 'All No-Tool') contradict the caption's description of 'tool-using rollout count'. The stacked areas sum to 100% (proportion of questions), but the legend implies these are counts or categories of rollouts rather than the proportion of questions falling into specific tool-use frequency buckets (e.g., 0, 1-4, 5-8 rollouts). The specific counts defining the 'Major' and 'Minor' categories are not defined in the caption or legend.
- **[writing]** Figure 3: The legend text 'Tool Major (>half)' and 'Tool Minor (≤half)' is ambiguous without defining the denominator. Does 'half' refer to half of the 8 rollouts (i.e., 4), or half of the questions? The caption mentions '8 rollouts/question', but the legend does not explicitly link the threshold to this number.
- **[fatal]** Figure 4: The caption describes 'Left & Middle' and 'Right' panels, but the image only contains two plots (Left and Right). The 'Middle' panel described in the caption is missing.
- **[science]** Figure 4: The caption claims 'Both symptoms reverse during AXPO training but stay flat under GRPO,' yet the legend only defines GRPO (red) and AXPO (blue). There is no third line or color representing a 'flat' GRPO baseline for comparison in the plots.
- **[writing]** Figure 4: The y-axis label 'questions with tool' on the right plot is ambiguous; the caption refers to 'all-wrong rate on tool-using subgroups,' but the axis label does not specify that it is a rate or percentage of wrong answers.
- **[science]** Figure 5: The caption claims 'Only AXPO expands both axes simultaneously,' but the plot shows the 'SFT+GRPO' point (red circle) having a higher conditional pass@1 than the 'SFT' point (orange diamond), indicating an expansion in the y-axis without AXPO. The visual data contradicts the specific claim made in the caption.
- **[writing]** Figure 5: The legend labels 'SFT+AXPO', 'SFT+GRPO', 'SFT', 'Base+GRPO', and 'Base' are rendered as floating text directly on the plot area rather than in a formal legend box, which can be ambiguous regarding which symbol corresponds to which method.
- **[writing]** Figure 6: The x-axis label reads '-confidence' while the caption describes plotting 'mean confidence'; the negative sign contradicts the text description and standard confidence ranges (0-1).
- **[writing]** Figure 6: The colorbar label 'training step' is ambiguous; the caption states points represent 'failed tool-using rollouts' per step, but the colorbar implies a continuous variable without specifying if it represents the step index or a count.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on reinforcement learning (RL) and large language model (LLM) jargon, which creates a significant barrier for non-specialist readers. The term "Thinking-Acting Gap" (\gap) is introduced in the Abstract and Introduction without a clear, plain-English definition, assuming the reader already understands the specific structural asymmetry the authors are describing. Similarly, acronyms like AXPO, GRPO, and SFT are used frequently before being fully spelled out in the Abs

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Proposition 1 (Sec 2.1) claims strict inequality whenever p(src) > q*p(tool), but this requires q < 1. If q=1, the waste factor vanishes and the condition changes. Explicitly state q < 1 as a premise for the strict inequality to avoid logical gaps.
- **[science]** Eq. 4 (Sec 2.3) replaces the source reward with a binary indicator but does not clarify if group mean/std are recalculated with this modified reward. If not, the advantage calculation contradicts the group-relative normalization premise. Clarify if normalization is re-computed.
- **[writing]** The claim that 8B AXPO 'surpasses' 32B Base (Sec 3.2) conflates training effects with model capability. Since 32B Base lacks SFT/RL, the comparison is logically flawed. Rephrase to compare against 32B SFT+GRPO or clarify the training pipeline difference.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that AXPO 'provably dominates' raw sampling (Introduction, Contribution 2) relies on Proposition 1, which assumes the selected prefix satisfies p(prefix) >= q * p^tool. The paper does not empirically verify that the uncertainty-based selection strategy consistently yields prefixes meeting this threshold across all benchmarks. Without this verification, the 'provably' claim overreaches the demonstrated evidence.
- **[writing]** The abstract and introduction state that the 8B AXPO model 'surpasses the 32B Base baseline' on Pass@4. While Table 4 shows 75.8 vs 75.1, the 32B model is an inference-only baseline without the SFT+RL pipeline. Comparing a trained 8B model to an untrained 32B model conflates architectural scale with training efficacy, potentially overstating the method's standalone contribution relative to scaling laws.
- **[writing]** The paper claims AXPO 'concentrates exploration precisely where the gap manifests' (Introduction). However, the analysis in Section 2.2 (Fig 3) diagnoses the gap using GRPO rollouts. The paper does not explicitly demonstrate that the specific prefixes selected for resampling in AXPO training are the exact same ones that would have been 'all-wrong' under a pure GRPO regime, leaving a slight logical gap between the diagnosis and the targeted intervention.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript addresses safety and ethical considerations appropriately for a methodological paper focused on reinforcement learning for multimodal agentic reasoning. The authors explicitly acknowledge the potential security risks associated with code-executing agents (Python interpreter) in the "Broader Impacts" section (Appendix, Section "Broader Impacts"). They state that all tool calls are executed within a sandboxed environment during both training and evaluation, which is a standard and necessary mitigation for this class of research.

The paper utilizes publicly available benchmarks (e.g., MathVision, HR-Bench) and does not appear to involve human subjects, sensitive personal data, or private datasets that would require IRB/IACUC approval. The training data sources (ViRL, fvqa, PyVision-RL) are cited as existing public corpora. The use of external APIs (Tavily search) is disclosed, and the authors note the implementation of a domain blacklist (`exclude_domains = ["huggingface.co"]`) to prevent answer leakage, demonstrating a consideration for data integrity and benchmark validity.

There are no indications of dual-use risks that are unique to this method compared to existing agentic frameworks; the proposed AXPO algorithm optimizes the efficiency of tool use rather than introducing new capabilities for harm. The "Limitations" section honestly addresses the scope of the work (verifiable rewards, model size) without overclaiming safety guarantees for deployment in uncontrolled environments. The paper does not contain conflicts of interest beyond the standard academic affiliations (NVIDIA, KAIST) which are clearly disclosed. No further safety or ethical revisions are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that AXPO 'provably dominates' raw sampling (Proposition 1, text/2_method.tex) relies on the assumption p(prefix) >= q * p^tool. The paper asserts this holds empirically but lacks a statistical test or confidence interval on the distribution of p(prefix) across the training set to confirm the threshold is met with high probability, not just on average.
- **[science]** The 'all-wrong' rate diagnostic (Fig 3b, text/2_method.tex) is central to the motivation. The paper reports ~40% but does not provide the standard error or the number of questions (N) used to calculate this rate. Given the binary nature of the metric, the sample size is critical to assess the stability of this claim.
- **[science]** The comparison to 'rollout 2x' (Table 2, tables/tab_comparison.tex) claims AXPO is more efficient. However, the '2x' baseline doubles the *total* rollout budget, while AXPO adds a 25% *extra* budget (r=0.25). The paper does not explicitly normalize the comparison to a '25% extra budget' GRPO baseline to isolate the algorithmic gain from the compute difference.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 3.2 and Table 1, report statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals) for the reported Pass@1/Pass@4 deltas between AXPO and GRPO. The current standard deviations (Table 2) show overlap in some cases; formal tests are needed to confirm the gains are not due to random rollout variance.
- **[science]** The ablation study in Table 3 lacks error bars or variance estimates. Given the small absolute gains in some ablations (e.g., ~0.5-1.0 pp), it is unclear if these differences are statistically significant or within the noise floor of the evaluation protocol.
- **[science]** In Section 2.2, the claim that tool-using subgroups are 'all-wrong on ~40% of questions' is based on visual inspection of Figure 3b. Please provide the exact sample size (number of questions/rollouts) and the 95% confidence interval for this proportion to validate the diagnostic claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, the sentence 'and 8B with SFT + AXPO surpasses the 32B Base on Pass@4 with 4x fewer parameters' is grammatically fragmented. It lacks a clear subject-verb connection to the preceding clause. Rephrase to: '...and at 8B, SFT+AXPO surpasses the 32B Base on Pass@4 using 4x fewer parameters.'
- **[writing]** In Section 1 (Introduction), the phrase 'suboptimal to make models proficient' is slightly awkward. Consider 'suboptimal for making models proficient' or 'suboptimal for training models to be proficient' for better flow.
- **[writing]** In Section 3 (Experiments), the sentence 'The most direct more compute control, rollout 2x, doubles rollout budget yet underperforms than AXPO' contains a grammatical error ('underperforms than'). It should be 'underperforms compared to AXPO' or 'is outperformed by AXPO'.
- **[writing]** In Section 2 (Method), the phrase 'provably dominating from-scratch sampling' in the contributions list is dense. While mathematically precise, it reads slightly clunky. Consider 'which provably dominates from-scratch sampling' for smoother integration.

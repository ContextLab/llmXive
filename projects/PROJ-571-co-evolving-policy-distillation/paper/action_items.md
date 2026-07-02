# Automated-review action items — Co-Evolving Policy Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.1, the phrase 'Text-Expert's strong text capability... dropping to 56.09' is ambiguous. It implies the expert degraded, but Table 1 shows the student (Image branch) scored 56.09. Rephrase to clarify the student's score dropped.
- **[writing]** In Section 3.2, 'Mixed RLVR achieves the highest video average among baselines' is misleading as Video-Expert (58.75) is also a baseline. Specify 'among consolidation baselines' to distinguish from single-expert baselines.
- **[writing]** In Section 2.3, the claim that OPD gain 'necessarily collapses to zero' at overlap 1 is theoretical, not empirically shown in the pilot data. Soften to 'is expected to' or 'suggests' to reflect it is a hypothesis.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption for (a) claims the baseline overlap drops monotonically, but the 'Baseline · Text' line (orange open circles) clearly fluctuates and is not monotonic.
- **[science]** Figure 1: The caption for (b) states KL 'stays consistently low in [CoPD]', but the 'CoPD · Image' line (green solid squares) rises from ~0.02 to ~0.06, which is a 3x increase, not 'consistently low' compared to the baseline's 10x rise.
- **[writing]** Figure 1: The caption for (b) contains a grammatical error and missing subject: 'stays consistently low in .' (missing 'CoPD').
- **[science]** Figure 1: Panel (c) labels the x-axis 'CoPD S_RL : S_OPD' but includes a 'static OPD' group which is not a ratio, creating a category error in the axis labeling.
- **[fatal]** Figure 3: The rendered image contains four subplots labeled (a), (b), (c), and (d), but the caption only describes three subplots (a), (b), and (c). Subplot (d) is completely missing from the description.
- **[fatal]** Figure 3: The caption describes subplot (a) as 'WeMath score before and after OPD' and subplot (b) as 'post-OPD gain plotted against top-k overlap', but the rendered image labels the top-left bar chart as (a) and the bottom-left scatter plot as (b). The caption text for (a) matches the top-left chart, but the caption text for (b) matches the bottom-left chart. However, the caption text for (c) describes 'top-k overlap drops and symmetric KL rises', which corresponds to the two right-hand plots i
- **[science]** Figure 3: The caption states that subplot (c) shows 'top-k overlap drops and symmetric KL rises', implying a single plot or a combined view. However, the image shows two distinct plots: (c) 'top-k overlap' vs 'Training step' and (d) 'Symmetric KL' vs 'Training step'. The caption conflates these two separate visualizations into one description for (c), leaving (d) undefined.
- **[writing]** Figure 3: The caption mentions 'across image and text branches' for subplot (c), which is consistent with the legend in the rendered plots (c) and (d). However, the caption does not explicitly mention subplot (d), creating a disconnect between the text and the visual layout which clearly separates the overlap and KL metrics.
- **[science]** Figure 4: The caption claims the figure illustrates 'limitations' of mixed-data RLVR (a) and static OPD (b), but the panels (a) and (b) only depict qualitative scenarios (student confusion/struggle) without quantitative data or explicit visual indicators of the specific limitations (e.g., performance drop, drift) mentioned in the text.
- **[writing]** Figure 4: The labels '(a) GRPO', '(b) OPD', and '(c) CoPD (Ours)' are placed below the cartoon panels, but the caption refers to '(a) mixed-data RLVR' and '(b) static OPD'. The term 'GRPO' in the image is not defined in the caption, creating a disconnect between the visual label and the textual description.
- **[writing]** Figure 4: The bottom bar chart (d) is not referenced in the caption, yet it contains the primary quantitative evidence ('achieving the best overall performance') supporting the caption's claim. The caption should explicitly reference panel (d) or the chart.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and coined phrases that, while standard within the immediate RLVR sub-community, create barriers for the broader machine learning audience. First, the Abstract introduces "RLVR" and "OPD" without expansion. While these are the core mechanisms, the abstract should define them as "Reinforcement Learning with Verifiable Rewards" and "On-Policy Distillation" respectively upon first use to ensure accessibility. Second, the paper frequently use

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3.3 claims a 'hub-and-spoke topology' for 3-branch CoPD to avoid full pairwise distillation, but Algorithm 1 implements full pairwise loops (j != k). This contradiction invalidates the scalability claim and requires alignment between text and code.
- **[writing]** Section 4.1 phrasing regarding the T->V distillation drop (57.89 to 56.09) is ambiguous. Clarify explicitly that the distilled model's score is lower than the teacher's to prevent misinterpretation of the transfer efficiency.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that CoPD 'surpasses domain-specific experts' (Abstract, Conclusion) is over-claimed. Table 1 shows CoPD beats Image-Expert but only slightly exceeds Text-Expert averages. The text implies a universal breakthrough where data shows a nuanced trade-off. Qualify this to 'surpasses experts in aggregate' or 'specific benchmarks'.
- **[writing]** The conclusion states CoPD 'even outperforming the respective expert models' and suggests a 'novel training scaling paradigm.' This extrapolates beyond evidence from a single 4B model on three domains. The claim of a general 'scaling paradigm' is premature without ablation on model size. Temper language to 'promising direction' rather than a definitive new paradigm.
- **[writing]** The abstract claims 'all-in-one integration' significantly outperforming experts. However, Table 2 shows Mixed RLVR achieved a higher Video Average (59.62) than CoPD (59.21), albeit at the cost of text. The 'all-in-one' claim glosses over that Mixed RLVR was better at video alone. Clarify that CoPD is the best *balanced* solution, not the absolute peak for every modality in isolation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper lacks an explicit statement regarding Institutional Review Board (IRB) or ethics committee approval for the use of human-generated data (e.g., AIME, HMMT, MMMU) and the filtering of video datasets. While these are public benchmarks, the methodology section (Section 4.1) should explicitly confirm that the data usage complies with the original licenses and that no private or sensitive user data was inadvertently included in the filtered video sets.
- **[writing]** The 'Self-Taught RLVR' series claims models can 'self-evolve' and 'teach themselves' (Conclusion). This framing risks obscuring the human labor and curation involved in dataset creation (e.g., Polaris, MMFineReason). The authors should add a clarification in the Limitations or Ethics section acknowledging that the 'self' is trained on human-curated data and that the system does not possess autonomous agency, to prevent misinterpretation of the model's capabilities.
- **[writing]** The paper reports significant performance gains on high-stakes reasoning benchmarks (AIME, HMMT). There is no discussion of potential dual-use risks, such as the model being used to generate solutions for unauthorized exams or to automate the creation of adversarial examples against other reasoning systems. A brief 'Safety and Limitations' paragraph addressing these potential misuse scenarios is required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The pilot study in Section 3.3 (Fig 4) claims a strong linear correlation (r=0.89) between top-k overlap and OPD gain. The text describes varying student temperature to create this data, but does not specify the number of checkpoints sampled or the statistical significance (p-value) of the correlation. Please report the sample size (N) and p-value to validate the robustness of this motivational claim.
- **[science]** In the main results (Tables 1 & 2), CoPD is claimed to 'surpass domain-specific experts.' However, the reported gains over the strongest single-expert baselines (e.g., Text-Expert on Text Avg) are often marginal (e.g., 58.76 vs 57.89). The paper lacks a statistical significance test (e.g., paired t-test or bootstrap confidence intervals) across the multiple benchmarks to confirm these improvements are not due to random variance in the evaluation.
- **[science]** The ablation study (Table 3) removes the 'merge' operation and evaluates single branches. The text claims these branches 'already surpass' static OPD. However, the table shows the 'Text-Branch Only' (57.24) is only marginally better than OPD_V->T (56.09) and comparable to OPD_T->V (56.29). The evidence for the 'co-evolution alone' claim is weak without error bars or a clearer statistical comparison against the static baselines.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The pilot study in Section 3.3 reports a linear correlation (r=0.89, R^2=0.79) between top-k overlap and OPD gain. The manuscript must report the sample size (N) of the student checkpoints used to derive this correlation and provide a p-value or confidence interval to establish statistical significance, as a correlation alone does not confirm the relationship is not due to chance.
- **[science]** In the ablation study (Table 3), performance drops are reported (e.g., text reasoning dropping from 58.76 to 57.41). The paper lacks statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals) to determine if these differences exceed the variance inherent in LLM evaluation, especially given the small magnitude of some improvements.
- **[science]** The experimental setup mentions sampling 8 rollouts per prompt at temperature 1.0. To ensure reproducibility and statistical robustness, the authors should specify the number of independent evaluation runs (seeds) performed for each benchmark and report the standard deviation of the mean accuracy, rather than just the mean.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 4.1 (Implementation Details), the word 'specifc' is misspelled twice ('specific experts' and 'specific experts'). Please correct to 'specific'.
- **[writing]** In Section 3 (Introduction), the sentence 'By separating capability-specific training from cross-capability consolidation, OPD avoids the gradient conflicts caused by capability divergence' ends with a stray comment marker '%' followed by a newline, breaking the flow. Remove the comment or integrate the text.
- **[writing]** In Section 5.1 (Main Results), the phrase 'surpassing the specific experts on both sides' is slightly ambiguous. Consider clarifying to 'surpassing the individual domain-specific experts' for precision.

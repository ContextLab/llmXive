# Automated-review action items — S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In the Introduction, the claim that S-Agent-8B performs 'comparably' to GPT-5.4 and Gemini 3 Pro is an overstatement. Table 3 shows S-Agent-8B (41.6%) is lower than GPT-5.4 (41.9%) and significantly lower than Gemini 3 Pro (45.2%). Change 'comparably' to 'competitive with' or 'approaching' to accurately reflect the performance gap.
- **[writing]** The Introduction claims S-Agent surpasses 'GPT-5' without specifying the version. Table 1 lists 'GPT-5.4'. Ensure all model names in the text match the specific versions in the tables (e.g., GPT-5.4, not GPT-5) to avoid ambiguity and factual inaccuracy regarding the baseline used.
- **[writing]** Section 4.1 states S-Agent 'surpasses GPT-5.4 by 4.5%'. While the absolute difference is 4.5 points, this phrasing can be ambiguous. Explicitly state 'absolute improvement of 4.5 percentage points' to distinguish from relative improvement and ensure scientific precision in the claim.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1: The 'Persistent Spatial Memory' panel contains a small scatter plot in box (m) that is illegible and lacks axis labels or a legend, making the data it represents impossible to interpret.
- **[writing]** Figure 1: The scatter plot in box (e) 'Spatial Reconstruction Tool' is illegible and lacks axis labels, units, or a legend, rendering the visualization of the 'Abs. distance' meaningless.
- **[writing]** Figure 4: The caption states this figure is 'in the appendix', but the image is rendered in the main body of the preprint, creating a contradiction between the text and the document structure.
- **[writing]** Figure 4: The caption is generic ('Additional qualitative examples') and does not describe the specific tasks shown (Object Counting, Multi-Step Reasoning), forcing the reader to rely solely on the image headers for context.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and acronyms that are not consistently defined for a general audience, creating barriers for non-specialist readers. First, the acronym VLM (Vision-Language Model) is used repeatedly in the Introduction (Section 1) without being spelled out at the first mention. While standard in the field, a paper aiming for broad impact should define this immediately. Similarly, SFT (Supervised Fine-Tuning) appears in the Abstract and Introduction withou

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 4.2, 'improves over GPT-5.4 by 4.5%' is ambiguous. Table 1 shows a 4.5 percentage point absolute gain. Clarify to '4.5 percentage points' to avoid implying a relative increase.
- **[writing]** In Section 4.3, claim that tool use 'can hurt performance' is only supported by MMSI-Bench (31.1% vs 30.7%), not ViewSpatial (42.2% vs 44.1%). Specify the benchmark where degradation occurred to avoid overgeneralization.
- **[writing]** In Section 4.4, attribute Level-2's limited gain to 'noise' without direct evidence in the ablation table. Cite a specific failure case or metric showing how noise distracts the planner to support this causal claim.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that S-Agent is the 'first tool-use agent for multi-view and long-video spatial intelligence' (Abstract, Intro) is overreaching given the existence of concurrent works like Think3D (cited in Related Work) which also handles active 3D exploration. The distinction needs to be more precise regarding 'continuous' vs 'active exploration' to avoid hyperbole.
- **[writing]** The statement that S-Agent-8B 'performs comparably to advanced closed-source models (e.g., GPT-5.4 and Gemini 3)' (Abstract, Intro) is not fully supported by the data. Table 1 shows S-Agent-8B (41.6%) trailing GPT-5.4 (41.9%) on MMSI-Bench and trailing Gemini 3 Pro (60.9%) on ReVSI. The claim should be tempered to 'competitive with' or 'approaching' rather than 'comparable to' given these specific deficits.
- **[writing]** The claim that S-Agent 'surpasses... all open-weight spatial models' (Abstract) is contradicted by Table 1 and Related Work, where SN-SI-1.3-IVL3-8B scores 61.3% on ViewSpatial-Bench, outperforming S-Agent's 60.0%. The claim of surpassing 'all' is inaccurate on this benchmark and needs qualification.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes generating 300K training trajectories using GPT-5.4 (a proprietary API) on the SenseNova-SI-800K dataset. Explicitly state the data licensing terms of SenseNova-SI-800K and confirm that the resulting S-300K dataset is released under a compatible license (e.g., CC-BY, MIT) to ensure downstream users can legally utilize the distilled agent.
- **[writing]** The methodology relies on open-vocabulary object detection (GroundingDINO) and metric depth estimation. Add a brief discussion on potential biases in these tools (e.g., demographic bias in detection, failure modes in specific environments) and how they might propagate into the agent's spatial reasoning, particularly for safety-critical applications like robotics.
- **[writing]** The paper mentions applications in autonomous driving and embodied robotics. Include a specific statement on the limitations of the current evaluation (benchmarks) regarding real-world safety risks, and clarify that the system is not yet validated for deployment in safety-critical physical environments.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Table 2 (tab:ablation_config) lacks statistical significance testing. With only a single run reported for each configuration (e.g., 56.7% vs 58.2%), it is unclear if the gains from memory modules are robust or due to random variance. Please report standard deviations over multiple seeds or perform a significance test.
- **[science]** The claim that S-Agent-8B 'performs comparably' to GPT-5.4 and Gemini 3 Pro (Abstract, Intro) is not fully supported by the data in Table 1 (tab:trajectory_distillation). On ReVSI, S-Agent-8B scores 52.8% while Gemini 3 Pro scores 60.9%, a gap of 8.1 points. The authors should qualify this claim or provide a more nuanced comparison rather than asserting comparability across all metrics.
- **[science]** The training data construction (S-300K) relies on a 'frozen teacher' (GPT-5.4) to generate trajectories, which are then filtered for correctness. This introduces a potential bias where the student model learns to mimic the specific reasoning patterns and tool preferences of the GPT-5.4 teacher, potentially limiting generalization to other planners or scenarios where the teacher fails. The authors should discuss this teacher-student bias and its impact on the robustness of the distilled agent.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 4.3 (Ablation Studies) and Table 2 (tab_ablation_config), the performance gains of individual components (e.g., +2.5% for Scene Memory) are reported as single point estimates. Given the iterative nature of the agent and potential variance in tool execution, please report confidence intervals or standard deviations (e.g., via 3-5 random seeds) to establish statistical significance of these marginal gains.
- **[science]** In Section 4.2 (Zero-Shot Performance) and Tables 1-3, the paper claims 'best overall' or 'surpasses' baselines based on point-estimate accuracy differences (e.g., 46.4% vs 45.2%). Without reported variance or significance testing (e.g., paired t-tests or bootstrap confidence intervals), it is unclear if these small margins (1.2%) are statistically significant or within the noise of the evaluation protocol.
- **[science]** In Appendix A.2 (Details of S-300K), the trajectory filtering criteria for numeric questions uses a fixed threshold of Mean Relative Accuracy (MRA) >= 0.6. The paper does not justify this threshold statistically or discuss its sensitivity. Please provide a sensitivity analysis or justification for this cutoff to ensure it does not introduce selection bias in the training data.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Simply and directly applying the S-Agent framework consistently improves...' contains redundant adverbs. 'Simply' and 'directly' convey similar meanings here; consider removing one to improve conciseness and flow.
- **[writing]** In Section 4 (Experiments), the phrase 'improving over GPT-5.4 by 4.5% on MMSI-Bench' appears immediately after stating the absolute score. The phrasing is slightly repetitive. Consider restructuring to: '...achieving 46.4%, a 4.5% absolute improvement over GPT-5.4.'
- **[writing]** In Section 3 (Method), the transition between the formal definition of memory updates and the description of Scene Memory is abrupt. The paragraph starting 'Scene Memory turns 2D/3D cues...' begins with a bolded term but lacks a clear introductory sentence linking it to the previous formal equations.
- **[writing]** In the Appendix (Section 7), the description of the 'Metric measurement expert' uses the phrase 'deterministically maps the request to a measurement route'. The word 'deterministically' is used frequently throughout the paper; ensure it is necessary here or if 'systematically' or 'explicitly' would be more precise given the context of tool selection.

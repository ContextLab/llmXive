# Automated-review action items — ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretraining

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The bibliography entry for 'Xperience-10M' lists 'Ropedia' as author and 2026 as year, which appears to be a placeholder or non-existent source. This invalidates the claim that this specific dataset contributes 435.7 hours to the pretraining pool.
- **[writing]** Section 3.1 claims human and robot actions use an 'identical' 6D orientation format, but the text does not explicitly confirm the human hand frame rotation matrix is converted to 6D before concatenation, leaving a gap in the unified format claim.
- **[writing]** Section 4.2 claims \Ours surpasses 'all baselines' on RoboTwin 2.0 but omits mentioning Hy-VLA (90.9% Easy) in the narrative comparison, despite it being the closest competitor. This omission weakens the context of the 'state-of-the-art' claim.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption claims to visualize 'camera-space action' and 'end-effector or hand motion,' but the image contains no explicit action vectors, velocity arrows, or trajectory lines indicating motion; it only shows static frames with coordinate axes.
- **[writing]** Figure 1: The coordinate axes (red/green/blue lines) are present but lack a legend or caption definition specifying which color corresponds to which axis (X, Y, or Z).
- **[writing]** Figure 2 caption contains a grammatical error: 'Qualitative rollout sequences of on the real ARX bimanual platform' includes a dangling preposition 'of' with no object.
- **[writing]** Figure 2 caption uses the phrase 'Each row shows key frames,' but the figure is organized into distinct task blocks (e.g., 'Scoop Coffee', 'Pack Shoes') rather than a single uniform grid of rows.
- **[writing]** Figure 3: The caption states the pipeline yields 1,478 hours of data, but the Sankey diagram shows the final 'Training set' bar labeled as 1478h while the input 'Human Video Dataset' is 5929h; the diagram lacks a total sum label for the final output to verify the caption's claim against the visual flow.
- **[writing]** Figure 3: The 'Quality Control' stage lists specific filters (Static, Spike, Completeness, Bimanual) with colored bars, but the legend or key explaining what these specific colors represent in the flow is missing from the figure itself.
- **[fatal]** Figure 5: The caption contains multiple instances of missing text where the model name should appear (e.g., 'Overview of .', 'resolves two mismatches', 'The'), rendering the description incomplete and unprofessional.
- **[science]** Figure 5: The 'Evaluation' bar chart displays success rates for 'ACE-Ego', 'JoyAI-RA', and 'Abot-M0', but the figure caption and diagram do not define these acronyms or explain their relationship to the proposed method, making the comparison contextually opaque.
- **[writing]** Figure 5: The 'Heterogeneous Data Sources' pie chart labels percentages (24.9%, 3.4%, 71.6%) that do not sum to 100% (totaling 99.9%), suggesting a rounding error or missing data slice.
- **[writing]** Figure 6: The caption contains multiple grammatical errors and missing nouns (e.g., 'Overview of .', 'unifies heterogeneous...', 'The [teaser.pdf]'), likely due to a missing model name placeholder.
- **[science]** Figure 6: The 'Evaluation' bar chart lacks a y-axis scale or gridlines, making it impossible to visually verify the precise 'Success Rate (%)' values labeled at the end of the bars.
- **[writing]** Figure 7: The caption contains a grammatical error and missing subject in the first sentence ('Architecture of .') and the second sentence ('resolves two mismatches...'), likely due to a placeholder variable not being filled in.
- **[writing]** Figure 7: The caption text appears to be copied from Figure 6's description ('resolves two mismatches...') rather than describing the specific architecture shown, which focuses on the Action Expert and loss functions.
- **[fatal]** Figure 8: The caption contains a broken LaTeX reference ('vs. $_0.5$') that fails to render the name of the comparison method, making it impossible to identify the orange bars in the legend.
- **[science]** Figure 8: The 'Avg' category on the x-axis displays a single bar for the green series (GROOT-N1.7) but lacks a corresponding bar for the blue series (ACE-Ego), preventing a direct visual comparison of the reported averages.
- **[writing]** Figure 9 caption contains a formatting error: '4.8$$ larger' includes a stray LaTeX delimiter and lacks the word 'times' (e.g., '4.8 times larger').
- **[writing]** Figure 9 caption uses the term 'convex-hull area' to describe the coverage metric, but the plot displays raw trajectory lines without showing the convex hull polygons or boundaries, which may confuse readers about how the area was calculated.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized robotics and machine learning terminology that is not defined at first use, creating a significant barrier for non-specialist readers. Key acronyms such as VLA, URDF, MANO, HaMeR, SAM3, VIPE, DiT, and SFT appear without expansion. Technical terms like 'pseudo-actions', 'embodiment', 'kinematic structures', 'flow-matching', 'bimanual', 'end-effector', 'extrinsic', 'intrinsic', 'rollouts', 'teleoperated', 'latent action representations', 'canonical acti

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Sec 4.1.3, clarify that H_d is dataset-specific in the sentence introducing Eq. 4 to explicitly link the variable definition to the claim that phi is comparable across datasets.
- **[writing]** In Sec 4.2, explicitly define the full decomposition of W_{t,j} into rho_j, w_data, and w_step in the text or equation to avoid confusion about which term is applied in the loss function.
- **[writing]** In Sec 5.3, refine the claim that GR00T-N1.7 'struggles on long-horizon sequences' to specify the failure modes (e.g., bimanual coordination) to resolve the apparent contradiction with the 73.3% score on Stack Bowls.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The "state-of-the-art" claim (Sec 5.2) overreaches as baselines are preprints with undefined protocols. Clarify if baselines were re-trained or if numbers are from external reports, and specify if SOTA holds against all public methods or just the listed subset.
- **[science]** Attributing gains solely to the "reliability-aware objective" (Sec 5.4) overreaches the ablation. Removing the loss removes both the human data and the weighting. Add an ablation comparing uniform vs. reliability-weighted human loss to isolate the mechanism's specific contribution.
- **[writing]** Claiming the camera-space representation "eliminates" the need for coordinate transformation learning (Sec 3.1) is an overstatement. The policy still uses morphology tokens to adapt to kinematics. Soften to state it standardizes the input space rather than eliminating adaptation needs.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper relies on a 'five-stage pipeline' to generate pseudo-actions from public egocentric videos (Ego4D, EPIC-KITCHENS, etc.) without explicit discussion of consent for secondary use in robotic training. Authors must confirm that the licenses of these datasets permit this specific transformation and training regime, or add a statement regarding the ethical limitations of using public video data for action supervision.
- **[writing]** The 'Spike filter' and 'Bimanual filter' in the data pipeline (Sec. 3.2, Stage 5) discard data based on statistical anomalies. Authors should briefly address whether these filters inadvertently remove data from specific demographics or individuals with atypical movement patterns, which could introduce bias into the resulting VLA policy.
- **[writing]** The real-robot evaluation on the ARX platform (Sec. 4.3) involves physical interaction with objects and potential human proximity. The manuscript lacks a statement confirming that these experiments were conducted under appropriate safety protocols (e.g., IRB/IACUC approval or institutional safety board clearance) and that human subjects were not exposed to risk during data collection or evaluation.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Sec. 4.4 reports a 3.6% drop when removing the reliability-aware loss, but the text does not provide the standard deviation or confidence intervals for these metrics. Given the small margins in the main benchmarks (e.g., 0.64% on RoboTwin), statistical significance testing (e.g., t-tests over the 50/100 trials) is required to confirm these gains are not due to variance.
- **[science]** The human data pipeline (Sec. 3.2) relies on HaMeR for 3D reconstruction and a custom smoothness filter. The paper claims this produces 'reliable' position channels but does not quantify the reconstruction error (e.g., MPJPE) against a ground-truth subset or provide an analysis of failure modes (e.g., occlusion rates) that might bias the auxiliary loss. A quantitative error analysis of the pseudo-labels is needed.
- **[science]** The real-robot evaluation (Sec. 4.3) uses only 30 trials per task. While the reported success rates show large margins (e.g., 16.7% on Scoop Coffee), the small sample size limits the statistical power to rule out random variation. The authors should report confidence intervals or perform a power analysis to justify the robustness of these real-world claims.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The ablation study in Sec. 4.4 reports performance drops (e.g., -3.6% for removing reliability-aware loss) but provides no statistical significance testing (e.g., t-tests, confidence intervals) or variance estimates across seeds. Given the small margins in RoboTwin 2.0 (e.g., +0.64%), the authors must report standard deviations or p-values to confirm these gains are not due to random variance.
- **[science]** In Sec. 4.3 (Real-Robot Evaluation), the paper claims a 6.6% improvement over pi_0.5 based on 30 trials per task. Without reporting the standard error or confidence intervals for these success rates, the statistical power is insufficient to support the claim of a 'decisive margin' for tasks with high variance. Please include 95% confidence intervals for all real-robot success rates.
- **[science]** The data scaling analysis in Sec. 4.4 (Table 2) compares single-point success rates for different data mixtures. To support the claim that 'human videos contribute diverse behavioral coverage,' the authors should provide error bars or multiple training runs to demonstrate that the observed +4.5% gain is robust and not an artifact of a specific random seed or data split.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2, the phrase 'The very data scaling that fuels these foundation models also introduces a fundamental bottleneck' is slightly redundant. Consider tightening to 'Data scaling, while fueling foundation models, introduces a fundamental bottleneck.' Also, ensure consistent spacing around em-dashes in the list of VLA systems.
- **[writing]** In Section 3.1.3, the transition to the batch sampling strategy is abrupt. Add a phrase like 'To implement this efficiently,' before 'Specifically, trajectories are pre-chunked...' to improve flow and logical connection.
- **[writing]** In Section 4.3, the sentence describing 'Scoop Coffee' results is a run-on. Split it: 'In sharp contrast, \Ours demonstrates a clear advantage on the contact-rich bimanual task 'Scoop Coffee.' \Ours sustains an 86.7% success rate, while GR00T-N1.7 falls to 36.7%.'
- **[writing]** In the Appendix (Section A.5), the transition from defining ratio $q_{t,h}$ to the step weight formulation is abrupt. Add 'Based on this ratio,' before 'The step weight is then formulated as' to clarify the logical connection.

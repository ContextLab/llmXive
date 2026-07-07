# Automated-review action items — VLA-Corrector: Lightweight Detect-and-Correct Inference for Adaptive Action Horizon

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a coherent set of claims regarding the VLA-Corrector framework, with most quantitative assertions supported by the provided tables and figures. However, there are specific instances where the text's summary of results does not align with the detailed data tables, leading to potential confusion or overstatement of efficiency gains. The most significant discrepancy is in the Introduction (Section 1), where the authors claim a "+24.6% success-per-call efficiency gain" for the $\p

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states the robot places the cube into the 'white bowl', but the images show the robot placing the cube into a clear plastic cup, while a white bowl is visible in the background but not used.
- **[writing]** Figure 1: The top row contains a large text overlay ('Change the cube's position') and a graphical arrow that obscure the view of the robot and the scene, reducing the clarity of the visual demonstration.
- **[science]** Figure 2: The caption states the robot places the cube into the blue bowl, but the visual sequence shows the robot placing the cube into the clear (transparent) bowl in the final frames.
- **[writing]** Figure 3: The text overlay 'drawer table moved' is unprofessional and lacks a clear legend or arrow definition explaining the specific perturbation event compared to the other demo figures.
- **[science]** Figure 3: The sequence of images is not clearly labeled with timestamps or step numbers, making it difficult to verify the chronological order of the 'moving-insertion' task and the robot's reaction to the drawer movement.
- **[science]** Figure 6: The caption claims the figure contains a 'Right' panel showing 'success-per-call efficiency', but the rendered image displays only a single plot. The missing panel prevents verification of the 'consistent efficiency gains' claim.
- **[writing]** Figure 6: The caption contains a formatting error in the model name, written as '$_0.5$' instead of the likely intended '$\pi_{0.5}$' (matching the figure legend).
- **[science]** Figure 7: The right panel's caption claims to show 'interrupt frequency,' but the y-axis is labeled 'Episode mean $E_t$' and the plot displays violin distributions of the score itself, not a frequency count of interrupts.
- **[science]** Figure 8: The caption claims the left panel shows 'representative trajectories' where truncation is triggered more frequently, but the image displays static snapshots of task phases (Grasp, Align, Place, etc.) without any data visualization (e.g., plots, heatmaps, or frequency markers) to demonstrate truncation frequency.
- **[science]** Figure 8: The caption states the right panel shows '83.7% of truncations occur in critical phases', but the rendered image contains no right panel, chart, or statistical graphic to support this quantitative claim.
- **[writing]** Figure 9: The image contains red and green bounding boxes with text labels ('INTERRUPT', 'FAILURE', 'SUCCESS') but lacks a formal legend or key to define these visual indicators.
- **[writing]** Figure 9: The caption describes the top row as a 'monitored baseline' and the bottom as 'VLA-Corrector', but the image itself does not label the rows, relying entirely on the caption for this distinction.
- **[science]** Figure 10: The caption claims a human shifts the blue bowl during execution, but the image shows the bowl moving from the right to the center while the robot arm is already positioned over the center, suggesting the disturbance occurred before the robot reached the target rather than during the grasp attempt.
- **[writing]** Figure 10: The image contains no labels, arrows, or annotations to indicate the timing of the disturbance or the robot's reaction, making it difficult to verify the 'recovery' claim visually.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.4 (OGG Correction) introduces the symbol $	au$ as 'denoising step' without defining the flow-matching context or the range of $	au$. An adjacent-field reader may not know if $	au \in [0,1]$ or discrete steps. Add a brief clause: 'where $	au \in [0,1]$ is the flow-matching time step'.
- **[writing]** Section 3.4 defines $\Delta Z_{\mathrm{dev}} = \Delta Z_t^{*} = Z_t^{\mathrm{real}} - Z_{t-k}^{\mathrm{real}}$ but uses the notation $\Delta Z_t^{*}$ (with a star) which was previously defined in Eq. 1 as the target residual from demonstrations. This overloads the symbol: in Eq. 1 it is a ground-truth target, here it is an observed drift. Clarify the distinction or use a distinct symbol (e.g., $\Delta Z_{\mathrm{obs}}$) for the observed drift to avoid confusion.
- **[writing]** Section 3.3 introduces the patience parameter $p$ in Eq. 5 without defining its role or typical value range before the equation. While defined later in the appendix, the main text should briefly state: 'where $p$ is a patience threshold (e.g., 5 steps) to filter transient spikes'.
- **[writing]** Section 3.1 uses the term 'flow matching' and 'velocity field' without a one-sentence gloss for readers from non-generative-model backgrounds (e.g., standard RL or control). While standard in generative AI, an adjacent control theorist might need a brief operational definition: 'a generative process that learns a velocity field to transport noise to data'.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 5.1 claims VLA-Corrector 'reduces policy calls' (19.27 to 15.64) for SmolVLA, yet the method adds interrupt-triggered replans. The text lacks a premise explaining how adding replans reduces total calls (e.g., baseline episode restarts vs. mid-episode recovery). Clarify the counting logic or rephrase to 'improves success-per-call'.
- **[writing]** Section 5.2 states the 'baseline rollout is only monitored by LVM,' but the baseline is defined elsewhere as lacking LVM. This contradicts the method definition. Clarify if the comparison is against an 'LVM-only' ablation or correct the description to 'Baseline (no LVM)'.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper generally maintains a strong alignment between its experimental evidence and its claims, particularly in the detailed ablation studies and the clear distinction between simulation and real-world results. However, there are three instances where the rhetoric slightly exceeds the specific scope of the demonstrated evidence, primarily regarding the universality of the "contact-rich" claim and the uniformity of performance gains. First, the Abstract asserts that the method improves robustn

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a safety-enhancing framework (VLA-Corrector) designed to improve the robustness of Vision-Language-Action (VLA) models in physical robotics by detecting and correcting execution drift. The methodology involves a Latent-space Vision Monitor (LVM) and Online Gradient Guidance (OGG) to truncate stale action chunks and replan when deviations occur.

From a safety and ethics perspective, the work is low-risk and arguably beneficial. The primary contribution is mitigating the "open-loop blind spot" where robots might continue executing erroneous actions, potentially leading to collisions or task failure. By introducing a mechanism to detect and correct these errors, the paper directly addresses a safety concern inherent in current action-chunking paradigms.

The research relies on standard simulation benchmarks (MetaWorld, LIBERO) and a controlled real-world setup using an AgileX PiPER arm with teleoperated demonstrations. The data sources are public benchmarks or self-collected demonstrations for fine-tuning, with no indication of using private, sensitive, or non-consented human data. The real-world experiments involve human disturbances applied in a controlled manner to test recovery, which is a standard safety validation protocol and does not pose a risk of harm to subjects or the environment.

There are no dual-use concerns; the method is specific to robotic control stability and does not lower the barrier for generating harmful content, cyberattacks, or biological hazards. The paper does not release any PII, and the code is hosted on a public repository as is standard practice. No conflicts of interest are apparent beyond standard academic affiliations.

As this is a third-party preprint, the absence of a formal IRB statement is noted, but given the use of public benchmarks and standard teleoperation protocols for data collection (which typically fall under exempt categories or standard lab safety protocols rather than human-subjects research requiring full IRB review), this does not constitute a fatal flaw or a missing disclosure of significant risk. The paper successfully identifies a safety risk (error accumulation) and proposes a mitigation without introducing new, unaddressed risks.

Verdict: Accept. No action items required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling framework for adaptive action horizons, but the experimental design in the main results tables lacks the necessary statistical rigor to fully support the magnitude of the claimed improvements. 1. Missing Variance and Seed Counts in Main Benchmarks The central claims regarding performance gains on MetaWorld (Table 1) and LIBERO (Table 2) rely on single-point success rates (e.g., 64.35% vs 48.70%). The paper mentions in the appendix that multi-seed data-scaling anal

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 (MetaWorld) and Table 2 (LIBERO) report single-point success rates (e.g., 64.35%) without any measure of uncertainty (SD, SE, or CI) or mention of the number of random seeds used. In RL/robotics, performance variance across seeds is high; reporting a single mean without spread implies false precision. Report mean ± SD over at least 3-5 seeds for all main results.
- **[writing]** Table 3 (Real-World) reports '73.3 ± 6.5' as the average success rate across 9 tasks, calculating the standard deviation of the *task means* rather than the standard deviation of the *trials* or the standard error of the mean. This conflates task difficulty variance with method stability. Report the standard deviation of the 20 trials per task, or the standard error of the mean across tasks, to correctly reflect the precision of the reported average.
- **[writing]** Section 5.2 (Mechanism Analysis) claims OGG improves recovery with an 'average gain of 0.23' (Fig 5) but provides no statistical test (e.g., paired t-test or bootstrap) or confidence interval to support this magnitude. Given the binary nature of success/failure, report the 95% confidence interval for the difference in recovery rates or the p-value from a McNemar's test on the paired outcomes.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and readable, with a clear logical flow from problem statement to solution. However, several sections suffer from paragraph density and minor structural inconsistencies that force the reader to re-parse sentences or infer missing transitions. The most significant issue is in Section 3.1, where the training methodology, loss function, and justification for using demonstrations are compressed into a single, dense paragraph. This obscures the distinct componen

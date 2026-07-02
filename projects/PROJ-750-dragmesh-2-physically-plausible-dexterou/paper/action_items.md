# Automated-review action items — DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4 claims the benchmark spans 'three categories', but Tables 1 and 2 list seven (including TrashCan, Oven). Correct the text to match the data.
- **[writing]** The claim that the parallel-jaw primitive is 'damping-invariant' with '0.14 mean' obscures that it succeeds perfectly (1.00) on object 12583. Clarify this nuance.
- **[science]** The ablation claim that the temporal encoder helps 'more' under stochastic mid-damping is weakly supported; the stochastic gain (0.64 vs 0.57) is marginal compared to deterministic drops.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption claims to show 'Three generated object trajectories,' but the image displays only a single snapshot of a single trajectory instance, failing to provide the promised comparative view.
- **[writing]** Figure 1: The caption contains a capitalization error ('Three' should be lowercase) and includes a raw filename ('[sim_46440_approach.png]') that should be removed.
- **[science]** Figure 2: The caption claims to show 'category and joint-type diversity' in terminal-stage renders, but the image displays a single static object (a cabinet) with no labels, annotations, or comparative views to demonstrate this diversity.
- **[writing]** Figure 2: The image lacks a figure label (e.g., 'Figure 2') and contains no text, scale bars, or legends to identify the object category or joint types mentioned in the caption.
- **[writing]** Figure 5: The caption contains a formatting error 'mode$$damping' and includes specific numerical claims (e.g., '0.56 deterministic at 4') that contradict the visual data in the chart, where the PICA bar at x4 in panel A is clearly below 0.50.
- **[science]** Figure 5: The caption claims the 'GT Parallel-Jaw' primitive is deterministic and identical across modes, yet the legend includes it in both panels; while the bars appear similar, the caption's specific numerical examples for PICA are factually inconsistent with the plotted heights.
- **[science]** Figure 6: The caption states the figure contains a 'Top' hardware example and a 'Bottom' simulated rollout, but the provided image is a single photograph with no bottom panel or simulated data shown.
- **[writing]** Figure 6: The caption describes a two-part figure (Top/Bottom), but the rendered image does not visually distinguish or separate these components, making the description impossible to verify.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define the acronym 'GLA' (Gated Linear Attention) at its first occurrence in Section 3.2 (Eq. 3) and Appendix 3.3.3. Currently, it appears without definition, assuming reader familiarity with specific attention variants."
- **[writing]** Replace the term 'loco-manipulation' with 'whole-body manipulation' or 'mobile manipulation' in the Abstract and Section 1. 'Loco-manipulation' is a niche robotics term that may exclude non-specialist readers."
- **[writing]** Define 'PICA' (Physically Informed Contact-Aware) immediately upon its first introduction in the Abstract. While defined in the Introduction, the Abstract should be self-contained for non-specialist readers."
- **[writing]** Replace the phrase 'action-boundary regularization' with 'penalizing actions near joint limits' or similar plain language in Section 3.2. The current phrasing is dense and assumes knowledge of specific RL regularization techniques."
- **[writing]** Clarify the term 'OOD' (Out-of-Distribution) at its first use in Section 4. While common in ML, it should be explicitly defined for a broader robotics audience in the context of 'contact-load shift'."

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 4.2 (Eq. 4), the auxiliary target includes a binary detachment flag. The text claims this helps infer 'contact impedance' for stable pulling. Logically, a binary failure flag indicates a state *after* contact loss, not a continuous proxy for impedance *during* contact. Clarify the distinct causal role of this binary term versus the continuous distance term in learning stable interaction.
- **[science]** Section 5 claims optimizing task progress causes action saturation and OOD failure. While Table 3 shows the correlation, the causal mechanism is unclear: does the reward function explicitly incentivize saturation, or is it a side effect? Explicitly link the reward terms (Eq. 5) to the saturation behavior to justify why PICA's specific regularizers are the necessary logical fix.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract claims the dataset supports 'future loco-manipulation,' but Table 1 shows only 277 hand-centric trajectories with no whole-body data. Rephrase to state it provides a 'motion-scale prior' for such tasks, not a direct resource.
- **[writing]** The introduction claims robustness 'without force sensing,' yet limitations admit this causes failure at high damping. Qualify the claim to 'improves robustness relative to baselines' to avoid implying the sensor-less problem is solved.
- **[writing]** The abstract describes 56% success at x4 damping as 'high task success.' This overstates the result. Change to 'maintains superior relative robustness' or 'retains non-trivial success' to accurately reflect the 44% failure rate.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a simulation-based reinforcement learning framework (DragMesh-2) for dexterous hand-object interaction with articulated objects. From a safety and ethics perspective, the work is low-risk. The research is conducted entirely within a simulated environment (Isaac Gym/SAPIEN implied by context and standard practice in the field), utilizing the GAPartNet dataset, which consists of synthetic 3D models. There is no collection of human data, no deployment on physical hardware in uncontrolled environments, and no involvement of human subjects or animals; therefore, IRB or IACUC approval is not applicable, and no consent procedures are required.

The potential for dual-use or physical harm is minimal. The system controls a virtual 51-DoF hand to manipulate virtual objects (drawers, doors) in a physics simulator. While the underlying technology (dexterous manipulation) could theoretically be applied to real-world robotics, the paper explicitly states in Section 5 (Limitations) and Figure 1 caption that quantitative evaluations are simulation-only, and hardware images are merely qualitative feasibility illustrations. The paper does not provide instructions for deploying the policy on physical hardware, nor does it claim real-world robustness that would necessitate immediate safety certification.

Data privacy and consent are not concerns as the dataset (GAPartNet) is a public, synthetic benchmark. The authors acknowledge the limitations of their approach, specifically the lack of tactile/force feedback and the risk of action saturation under high damping (Section 5), which are technical limitations rather than safety hazards in the current context. The code and dataset are released via public links (GitHub/Website), which is standard for reproducibility and does not introduce new ethical risks. No conflicts of interest are declared, and the funding sources are standard academic affiliations. The paper adheres to responsible AI research practices by clearly delineating the scope of the work (simulation) and acknowledging the gap to real-world deployment.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The standard error for success rates (n=20) is ~0.11, yet the paper treats small differences (e.g., 0.15 vs 0.30 at x4 damping) as distinct performance tiers. Report confidence intervals or statistical significance tests for the main comparison in Table 1 and Figure 2 to support claims of superiority.
- **[science]** The 'Traj. tracking' baseline achieves 1.00 success at x1 and x4 damping (Table 1), which contradicts the claim that open-loop replay fails under high damping. Clarify why this specific baseline is robust to damping changes while learned policies fail, or re-evaluate the baseline's physical validity.
- **[science]** The hardware results in Figure 4 are qualitative only. To support the claim of 'physically plausible' interaction, provide quantitative metrics (e.g., contact force, slip rate) from the hardware trials or explicitly limit the claim to simulation validity.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the success rates in Table 1 and Table 2. With N=20 episodes per cell, the standard error is ~0.11; without error bars or CIs, small differences (e.g., 0.56 vs 0.50) are statistically indistinguishable. Appendix Limitations (Sec 5.1) acknowledges this but the main results tables lack the necessary statistical context.
- **[science]** Clarify the statistical independence of the 20 episodes per cell. If the same random seed or initialization is used across damping conditions for a single object, the samples are not independent, invalidating standard error calculations. Explicitly state the randomization protocol for episode initialization and damping sampling in Appendix Sec 5.1.
- **[science]** The ablation study (Table 2) compares multiple methods without correcting for multiple comparisons. With 7 objects and 3 damping levels, the number of pairwise tests is high. Report adjusted p-values or use a non-parametric test (e.g., Friedman test) to validate that PICA's superiority over baselines is statistically significant rather than due to chance.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract and Introduction, the phrase 'hand--object' and 'hand--handle' uses double hyphens for en-dashes. While common in LaTeX source, ensure the compiled PDF renders these as proper en-dashes and not double hyphens, as this affects readability and professional appearance.
- **[writing]** Section 3.2 (Eq. 4) and Appendix A.3.4 (Eq. aux) define the auxiliary target vector y_t. The text describes the components as 'recent object response, maximum palm--handle distance, detachment risk, and tracking stress,' but the equation includes a binary indicator for detachment. Clarify if the binary indicator is distinct from the 'detachment risk' description or if the description should explicitly mention the binary nature.
- **[writing]** In Section 4, the text states 'The damping multipliers ×1, ×2, and ×4 measure nominal performance, mild contact-load shift, and strong out-of-distribution (OOD) contact-load shift, respectively.' The phrasing 'contact-load shift' is repeated. Consider varying the vocabulary (e.g., 'increased resistance' or 'higher damping') to improve flow and reduce redundancy.
- **[writing]** The caption for Table 1 (tab:dataset) lists 'TableObject' with 1 trajectory, but the text in Section 3.3 mentions '7 GAPartNet categories' and the table lists 7 rows. Ensure the category name 'TableObject' is consistent with the GAPartNet taxonomy used in the rest of the paper (e.g., is it 'Table' or 'TableObject'?) to avoid confusion for readers cross-referencing the dataset.

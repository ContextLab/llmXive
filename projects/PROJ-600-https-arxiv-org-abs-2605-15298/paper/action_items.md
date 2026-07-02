# Automated-review action items — PhysBrain 1.0 Technical Report

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.1 claims PhysBrain 8B leads on RealWorldQA, but Table 1 shows PhysBrain 4B (72.7) outperforms 8B (68.8). Correct the text to reflect 4B leads on this benchmark.
- **[writing]** Section 2.3 cites 'GPT-5' and 'Gemini 3.1 Pro' as annotators. Verify these model names/versions exist and are accurate, as standard naming conventions differ.
- **[writing]** Section 5 claims specific success rates (47.1% vs 63.3%) but Table 'tab:franka_results' contains TODO placeholders. Complete the table to verify the per-category calculations.
- **[writing]** Section 4.2 describes SimplerEnv-GoogleRobot tasks as 'out-of-domain' but lists 'Open/Close Drawer'. Clarify if these tasks were held out from the Google Robot training data used.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The rendered image displays four performance benchmark charts (VLM QA, SimplerEnv, LIBERO, RoboCasa) and a central logo, which contradicts the caption's description of a 'system overview' pipeline showing video-to-QA transformation and VLA adaptation. The visual content does not match the described architecture.
- **[writing]** Figure 1: The central logo contains the text 'PhysBrain' and '+1.0 over #2', but there is no legend or axis definition explaining what the central graphic represents or how it relates to the surrounding benchmark data.
- **[writing]** Figure 4: The caption describes the figure as an 'Overview of the PhysBrain 1.0 architecture,' but the rendered image is identical to Figure 3 (a detailed training pipeline diagram). The figure should be a high-level architectural block diagram as described, or the caption should be updated to match the detailed pipeline shown.
- **[science]** Figure 5: The 'Avg. relative' panel displays a single aggregated bar per model, but the caption states it is an average of seven relative percentages. Without showing the individual relative scores or the raw denominators, it is impossible to verify the calculation or compare the 'Avg. relative' values against the raw scores in the other panels.
- **[writing]** Figure 5: The y-axis labels for the 'MME' panel are illegible due to overlapping text (e.g., '2413.6' and '2385.1' are stacked vertically), making it difficult to read the exact values.
- **[writing]** Figure 6: The caption references sub-panels '(a) Front view' and '(b) Rear-side view', but the rendered image is a single composite view without these labels or distinct panel separation.
- **[writing]** Figure 7: The legend in the top center uses the symbol '$\pi_{0.5}$' (rendered as a light blue circle), but the caption refers to the baseline as '$_0.5$'. The caption text is missing the 'pi' symbol, creating a mismatch between the visual legend and the textual description.
- **[science]** Figure 7: The right panel (b) displays 'All green vegetables' and 'All orange vegetables' as aggregated categories for long-horizon tasks, but the specific vegetable items included in these groups are not defined in the figure or caption, making the results difficult to interpret.
- **[fatal]** Figure 8: The caption describes a 'Top' and 'Bottom' view split, but the rendered image is a single horizontal strip of five frames with no vertical split or wrist-mounted view shown.
- **[science]** Figure 8: The image shows a sequence of frames but lacks time stamps or step labels (e.g., 'Approach', 'Grasp', 'Lift') to clarify the temporal progression described in the caption.
- **[science]** Figure 9: The caption claims to show a 'Top: external camera view' and 'Bottom: wrist-mounted camera view', but the rendered image is a single horizontal strip of 5 frames with no vertical split or labels to distinguish these two views.
- **[writing]** Figure 9: The caption describes a 'sequence' but the image lacks timestamps, frame numbers, or arrows to indicate the temporal order of the grasping steps.
- **[science]** Figure 10: The rendered image displays a single row of five panels showing a sequence, but the caption explicitly describes a 'Top: external camera view' and 'Bottom: wrist-mounted camera view' layout. The image does not match the caption's description of a dual-view setup.
- **[science]** Figure 11: The caption claims the figure shows 'Top: external camera view... Bottom: wrist-mounted camera view', but the rendered image is a single 4x5 grid of external views with no wrist-mounted camera data shown.
- **[science]** Figure 11: The caption describes a specific error recovery sequence (cucumber grasp failure then success), but the grid shows a continuous sequence of successful grasps without a visible failure event or recovery step.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'VLA' (Vision-Language-Action) at its first occurrence in the Abstract and Introduction. While common in the field, the paper targets a broader audience and should not assume prior knowledge of this specific acronym.
- **[writing]** Replace the term 'SOTA' in the Abstract and Section 4.2 with 'state-of-the-art'. Acronyms like SOTA should be spelled out on first use to ensure accessibility for non-specialist readers.
- **[writing]** Define 'QA' (Question-Answering) at its first use in Section 2.5. The text frequently uses 'QA' and 'VQA' without explicit definition, which may confuse readers unfamiliar with the specific dataset generation terminology.
- **[writing]** Replace the acronym 'EEF' (end-effector-frame) in Section 3.5 with the full term 'end-effector frame' or define it immediately upon first use. The text assumes the reader knows this robotics-specific abbreviation.
- **[writing]** Define 'VLM' (Vision-Language Model) at its first occurrence in the Abstract. The paper relies heavily on this acronym, and defining it early is crucial for readers outside the immediate sub-field.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Sec 5.2, the claim that gains on SimplerEnv-WidowX are due to 'human-video priors' is not fully isolated. Baselines like Isaac-GR00T-N1.6-Bridge also use BridgeV2. Clarify if comparisons control for pre-training regimes to support the causal claim.
- **[science]** In Sec 6, the 16.2% gain over pi_0.5 is attributed to human priors. However, the initialization of the pi_0.5 baseline is not explicitly confirmed to match PhysBrain's VLM initialization. Confirm initialization parity to ensure the causal link is logically sound.
- **[writing]** In Sec 3.2, the 'log-likelihood-ratio' objective is asserted but not derived. The text does not explicitly show how the specific causal masking in Eq 4 vs Eq 5 mathematically enforces instruction sensitivity. Add a brief derivation or clarify the logical link.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'SOTA results' across all benchmarks is overreaching given the negligible 0.1% margin over the second-best method in LIBERO (Table 4). Temper claims to 'competitive' or 'within noise' and discuss statistical significance.
- **[science]** The 'strong out-of-domain performance' claim on SimplerEnv is exaggerated if training data (BridgeV2) overlaps significantly with evaluation tasks. Clarify the domain shift magnitude or rephrase to avoid implying zero-shot transfer where leakage may exist.
- **[writing]** Describing the LLM-based data engine as a 'compiler' that makes physics 'explicit' overstates reliability. The pipeline admits to semantic errors but lacks a quantitative noise rate analysis for the generated metadata.
- **[science]** The claim of 'data efficiency' (fewer robot demos needed) lacks support from a controlled ablation varying robot data size. Provide a learning curve or comparison with limited data to substantiate this extrapolation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes collecting 450 real-world robot trajectories via human teleoperation (Sec. Real-World Experiments) but lacks explicit IRB/ethics approval statements or consent protocols for the human operators. Given the use of human data for training AI, a statement on ethical clearance and informed consent is required.
- **[writing]** The data engine relies on large-scale human egocentric video (Ego4D, EPIC-Kitchens). The manuscript does not address potential privacy risks, such as the presence of identifiable faces, license plates, or sensitive locations in the source videos, nor does it detail the anonymization or blurring procedures applied before training.
- **[writing]** The system is designed to learn 'affordance and safety' (Tab. QA families) and execute actions on physical objects (vegetables). The paper lacks a discussion on safety constraints, failure modes, or human-in-the-loop safeguards required when deploying a model that might generate unsafe physical actions in unstructured real-world environments.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The real-world Franka experiments (Sec 6) lack statistical rigor. Success rates are reported as single-point estimates over 50 trials per category without confidence intervals, standard deviations, or significance testing against the $\pi_{0.5}$ baseline. Given the claimed 16.2% average gain, variance analysis is required to rule out random fluctuation.
- **[science]** The VLA simulation results (Tables 1-4) show performance saturation on LIBERO (98.8%) and near-saturation on SimplerEnv-GoogleRobot (91.33%). The paper does not provide power analysis or effect size calculations to demonstrate that the marginal gains (e.g., 0.1% on LIBERO) are statistically significant rather than noise, especially given the small number of held-out tasks in some benchmarks.
- **[science]** The data engine relies on synthetic QA generated by multiple LLMs (GPT-5, Gemini 3, etc.) without reporting inter-annotator agreement (IAA) or a human-in-the-loop validation study. The claim that this reduces 'reasoning biases' (Sec 2.3) is unverified; a quantitative analysis of label noise or a human evaluation of the generated QA quality is needed to support the robustness of the training signal.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The real-world Franka experiments (Sec 6) report success rates over 50 trials but lack statistical significance testing (e.g., confidence intervals or p-values) when comparing PhysBrain 1.0 against the $\pi_{0.5}$ baseline. Given the claim of a 16.2% average gain, provide 95% CIs or a binomial test to confirm the improvement is not due to random variance.
- **[science]** In the VLM results (Sec 5.1.2), the 'Avg. relative' metric normalizes scores by the best model per benchmark before averaging. This aggregation method obscures the magnitude of absolute gains and may introduce bias if benchmarks have different score distributions. Justify this normalization or report absolute mean differences with standard deviations.
- **[science]** The VLA simulation results (Tables 1-4) show single-point success rates without error bars or standard deviations across seeds. For claims of SOTA performance (e.g., 80.2% on SimplerEnv-WidowX), report results averaged over multiple random seeds (e.g., 3-5) with standard deviation to ensure reproducibility and robustness.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (Capability Preservation), the phrase 'The architecture in PhysBrain 1.0follows' contains a missing space between '1.0' and 'follows'. This is a minor typo but should be corrected for professional polish.
- **[writing]** In Section 2.2 (Data Sources), the sentence 'The second stage expands the re-annotation process to sources such as EPIC, and SEA-Small' includes an unnecessary comma before 'and'. Remove the comma to improve flow.
- **[writing]** In Section 4.2 (VLA Simulation Experiments), the text states 'PhysBrain 1.0 improves from 88.8% to 94.8%'. Ensure consistency in decimal precision across all percentage comparisons in the results section (e.g., some use one decimal, others two).
- **[writing]** In Section 5 (Real-World Experiments), the paragraph 'Long-Horizon Tasks' uses the phrase 'orange-vegetable instruction'. Consider rephrasing to 'instruction involving orange vegetables' for slightly better clarity and flow.

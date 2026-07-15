# Automated-review action items — ABot-N1: Toward a General Visual Language Navigation Foundation Model

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims '95.4%/92.9% SR' conflating distinct metrics. Table 1 (indoor) uses strict SR<1col, while Table 2 (outdoor) uses relaxed SR<3col. Rephrase to specify '95.4% SR (indoor, strict) and 92.9% SR (outdoor, relaxed)' to avoid implying comparability.
- **[writing]** Abstract states 'boosting POI arrival by 35.0% (to 77.3%)'. Table 4 shows an increase from 42.3% to 77.3%, which is +35.0 percentage points, not a relative 35% increase. Clarify to 'by 35.0 percentage points' to prevent misinterpretation.
- **[writing]** Section 6.1.5 claims ABot-N1 'surpasses all baselines' except STT TR. Table 5 shows Qwen-RobotNav-4B (90.0%) beats ABot-N1 (89.8%) on STT TR. The phrasing is slightly ambiguous; clarify that it leads on SR across all splits but trails Qwen-RobotNav-4B on STT TR by 0.2%.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states that Stage 3 uses 'A* on MoGe-V2-derived 2D occupancy grids', but the diagram explicitly labels the grid generation step as 'MoGe-V2 Normal Prior' and does not visually depict the occupancy grid or the A* algorithm, creating a disconnect between the text description and the visual pipeline.
- **[writing]** Figure 1: The 'Stage 3' section contains a floating label 'MoGe-V2 Normal Prior' pointing to a pyramid icon without a connecting box or clear definition of its role in the 'Traversability-Aware Sampling' flow, making the diagram's logic harder to follow.
- **[writing]** Figure 2: The caption describes the content as 'Four segments of a long-range outdoor episode,' but the figure itself is a composite of four distinct sub-figures (Seg1-Seg4) without a unifying visual frame or explicit labels connecting the segments into a single continuous narrative.
- **[science]** Figure 2: The 'Slow System Reasoning' panels display 'Affordance Pixel' markers (green dots) on the ground, but the corresponding 'VLA' and 'Third-View' panels below them do not show these markers, making it difficult to verify if the visual guidance aligns with the agent's actual perception or trajectory.
- **[science]** Figure 4: The caption claims 'slope navigation and staircase avoidance' for the Luckin Coffee case, but the visual evidence shows the robot navigating a flat sidewalk and avoiding a red barrier; no slope or staircase is visible.
- **[writing]** Figure 4: The 'Slow System Reasoning' row contains red, blue, and green bounding boxes, but no legend or caption text explains what these specific colors signify (e.g., confidence levels, specific reasoning steps, or error types).
- **[science]** Figure 5: The 'Target Pixel' (red star) is shown in the final 'bar approach' panel but is absent from the first three 'Slow System Reasoning' panels despite the caption claiming 'target pixel visualizations' are present at all four critical moments.
- **[writing]** Figure 5: The legend in the 'bar approach' panel labels the red star as 'Target Pixel' and the green dot as 'Affordance Pixel', but the 'Slow System Reasoning' panels for stair descent, gym entry, and gym exit only show the green dot without a legend, creating ambiguity about the red star's absence.
- **[science]** Figure 7: The caption claims evaluation on 'EVT-Bench', but the radar chart legend and axis labels only show 'ABoT-N1', 'Previous BOTA', 'NavFoM', 'Uni-NavVid', and 'Qwen-VLA', with no explicit reference to EVT-Bench or its specific metrics.
- **[writing]** Figure 7: The legend for the radar chart is extremely small and illegible, making it difficult to distinguish between the different model lines (e.g., 'Previous BOTA' vs 'NavFoM').
- **[writing]** Figure 8: The caption text is truncated at the end ('predict continuo'), cutting off the description of the MLP output.
- **[science]** Figure 8: The 'Slow System' block contains a purple hourglass icon and fire emojis, but the caption does not define these symbols or explain their significance (e.g., latency, compute intensity).
- **[science]** Figure 8: The 'Fast System' block contains a lightning bolt icon and a fire emoji, which are undefined in the caption and lack a legend.
- **[science]** Figure 9: The inner ring of the main donut chart contains a segment labeled 'Object Goal 0.1M' that is visually indistinguishable from the adjacent 'POI Goal 3.0M' segment due to identical coloring and lack of a visible boundary line, making the chart unreadable.
- **[science]** Figure 9: The 'TOTAL 30M' label in the center of the main donut chart is mathematically inconsistent with the sum of the visible segment labels (6.2+2.4+2.7+3.0+0.1+0.1+5.1+6.8+3.4 = 29.8M), suggesting a rounding error or missing data.
- **[writing]** Figure 9: The text labels for the inner ring segments (e.g., 'Point Goal', 'Person Following') are rotated and difficult to read, reducing the clarity of the data breakdown.
- **[writing]** Figure 10: The caption describes the 'Right' panel as having 'affordance pixel annotation', but the image labels the green dot as 'Affordance Pixel' and the red dot as 'Target'/'Perturbed Target' without explicitly defining the distinction in the caption text.
- **[writing]** Figure 10: The 'Structured Sample' panel includes a 'Mission' text block with coordinates, but the caption does not explain the coordinate system or the meaning of the values.
- **[science]** Figure 11: The caption describes a 'three-stage pipeline' and 'generates and verifies affordance and target pixels,' but the visual diagram only shows 'VLM Instruction Decomposition' and 'VLM Annotation-Align' without explicitly depicting the verification step or the generation of target pixels (which are listed as empty in the sample).
- **[writing]** Figure 11: The 'Structured Sample' on the right lists 'Target Pixel: left:[], front: [], right[]' as empty, which contradicts the caption's claim that the sample shows 'pixel-level annotations for affordance and target'.
- **[science]** Figure 12: The caption claims the pipeline uses 'A* consistency filtering', but the diagram labels the filter simply as 'Consistency Filter' without explicitly showing or labeling the A* algorithm component.
- **[writing]** Figure 12: The 'Structured Sample' text block contains raw JSON-like syntax (e.g., 'left: [], front: [542, 698]') which is difficult to read and visually cluttered compared to the rest of the figure.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 (Introduction) uses 'CoT' and 'GRPO' without definition. Expand to 'Chain-of-Thought (CoT)' and 'Group Relative Policy Optimization (GRPO)' at first use.
- **[writing]** Section 3.1 (Preliminaries) uses 'SE(2)' without definition. Add 'SE(2) (Special Euclidean group in 2D)' at first occurrence.
- **[writing]** Section 4.2 (Pretraining Data Recipe) uses 'Dagger' without definition. Add 'Dataset Aggregation (Dagger)' at first mention.
- **[writing]** Section 4.2 uses 'smooth-$L_1$' without defining the loss function or its properties in this context. Add a brief clause explaining it is a robust regression loss.
- **[writing]** Section 5.1 (Post-Training) uses 'KL' without defining it as Kullback-Leibler divergence. Expand at first use.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 6.1.5 claims a '+0.558 absolute jump' in POI SR, but Table 6 and the Abstract show a rise from 42.3% to 77.3% (a 35.0 point jump). The value 0.558 contradicts the paper's own data. Correct the text to match the table (e.g., '+35.0 points').

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims the method 'ensures robust... navigation across... real-world benchmarks,' but Section 6.2 only provides qualitative case studies on one robot. No quantitative real-world metrics exist. Replace 'ensures... across real-world benchmarks' with 'demonstrates qualitative robustness on a single quadrupedal platform' or add quantitative real-world evaluation.
- **[writing]** Abstract states the method 'solves' coordinate drift and long-tail semantics. Results show significant reduction (e.g., 35% POI boost) but not elimination (4.6% indoor failure remains). Change 'solves' to 'significantly mitigates' to align with residual error rates.
- **[writing]** Introduction/Conclusion claim a 'general' model for 'open-world environments,' yet experiments cover only five specific tasks on fixed benchmarks. No zero-shot transfer to new tasks or unstructured domains is shown. Narrow the claim to 'generalist within the five evaluated tasks' or provide broader generalization evidence.
- **[writing]** Conclusion states the model 'achieves state-of-the-art results on all five benchmarks.' However, Table 1 shows RxR-CE SR (73.9%) is second to Qwen-RobotNav-4B (75.2%). Clarify that SOTA is achieved on primary metrics or specify which metrics lead, as the current claim is factually inaccurate for RxR SR.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a visual-language navigation foundation model (ABot-N1) and associated benchmarks for embodied agents. From a safety and ethics perspective, the work is low-risk. The research focuses on improving navigation robustness, interpretability (via Chain-of-Thought), and social compliance (avoiding vehicle lanes, respecting pedestrian zones) in simulated and real-world environments.

The paper explicitly addresses safety as a core design goal, introducing a "Safety Clearance" reward function in its GRPO post-training stage to penalize proximity to non-traversable regions and traffic-rule violations (Section 4.3.2). The benchmarks (ABotN-PointBench, ABotN-POIBench) are constructed using high-fidelity 3DGS reconstructions of real-world scenes, but the data collection and annotation processes described (LiDAR-inertial SLAM, manual annotation of walkable regions) do not appear to involve the collection of personally identifiable information (PII) or sensitive human data in a way that would require IRB approval for the *navigation* task itself. The "person-following" task uses synthetic avatars in simulation (Habitat) or teleoperation data where the focus is on tracking behavior, not biometric identification, and the paper does not claim to release raw video of identifiable individuals.

There are no indications of dual-use capabilities intended for surveillance, deception, or autonomous weaponization. The "social compliance" features are designed to prevent harm to humans and property, not to facilitate covert operations. The release of benchmarks and code is framed as advancing the field of safe navigation. No specific, non-trivial risks of harm are identified that are unacknowledged or unmitigated in the text. The paper does not require additional safety disclosures or mitigations beyond what is already present.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling architecture and reports impressive numerical gains across five navigation tasks. However, the experimental design currently lacks the rigor required to definitively attribute these gains to the proposed mechanisms (slow-fast factorization, pixel goals, GRPO) rather than confounding factors like training scale, data volume, or random seed variance. First, the evidence for "state-of-the-art" performance relies entirely on single-run results reported in Tables 1 thr

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1-5 report single-point performance metrics (e.g., '92.9% SR') without any measure of uncertainty (standard deviation, standard error, or confidence intervals) across multiple random seeds or runs. In deep learning, single-run results are insufficient to distinguish signal from stochastic variance. Report mean ± SD over at least 3-5 seeds for all primary results, or explicitly state that results are from a single run and treat them as such.
- **[writing]** The abstract and Section 6 claim 'state-of-the-art' and 'massive gains' (e.g., '+35.0% boost') based on point estimates. Without reported variance or statistical significance tests (e.g., paired t-tests or bootstrap CIs) comparing ABot-N1 against the strongest baselines, it is impossible to determine if these differences are statistically significant or within the noise floor of the evaluation protocol. Add uncertainty bounds or significance markers to the tables.
- **[writing]** Section 6.1.3 and 6.1.4 report results stratified by difficulty tiers (Low, Medium, High) and split by indoor/outdoor. This constitutes multiple hypothesis testing (e.g., 3 tiers × 2 splits × 2 metrics = 12+ comparisons per task). The paper highlights specific 'significant' improvements in these sub-splits without applying a correction for multiple comparisons (e.g., Bonferroni or Holm). Re-evaluate significance claims with a correction or explicitly acknowledge the multiplicity risk.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a complex architecture and extensive experimental results, but the prose occasionally struggles to deliver these details with the necessary clarity and momentum. While the technical content is dense, the writing quality generally allows a reader to follow the argument, though there are specific instances where sentence structure and paragraph organization impede smooth reading. The most significant friction points occur in the Methods section, particularly where the autho

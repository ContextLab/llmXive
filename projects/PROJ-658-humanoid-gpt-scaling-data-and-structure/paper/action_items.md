# Automated-review action items — Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In the Introduction (Sec 1, 'Science of Scale'), the claim that the training set is 'over 200x larger than prior tracker training sets' is not supported by the provided data. Table 1 lists SONIC (2025) with 100M frames. 2B / 100M = 20x, not 200x. The 200x figure likely compares against older baselines (~7-10M frames) but is misleading when SONIC is explicitly cited as a related work in the same section and table. Clarify the baseline used for this comparison.
- **[writing]** In the Introduction (Sec 1, 'Science of Scale'), the paper claims to provide 'the first systematic evidence that video-estimated motion can materially improve tracking.' However, the text does not cite a specific ablation study, figure, or table within the manuscript that isolates 'video-estimated motion' as a variable to prove this causal link. The claim appears to be an assertion without the immediate evidentiary support required for a 'first systematic evidence' statement.
- **[writing]** In Section 4 ('Evaluation in Simulation'), the text states: 'even the best baseline (TCN-L at 56.15mm) lags behind Humanoid-GPT-S (43.25mm) by 30%.' However, Table 2 (tab:sim_scaling_backbone) does not contain a row for 'TCN-L' nor does it list MPKPE values of 56.15mm or 43.25mm. The table lists TCN (8-layer) with MPKPE 79.75mm. The specific numbers and the 'TCN-L' variant mentioned in the text are missing from the provided tables, making the claim unverifiable from the current source.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains multiple grammatical errors and missing nouns, reading 'Overview of .' and 'The resulting can take...', which obscures the subject (Humanoid-GPT).
- **[writing]** Figure 1: The caption describes 'keypoint-level rewards' for stage (b), but the diagram only labels the loop as 'RL' without specifying the reward type.
- **[science]** Figure 2: The top x-axis is labeled 'Geometric-std' but the caption defines the horizontal axis as 'gstd'; the label should be updated to match the caption's terminology.
- **[writing]** Figure 2: The text 'Our Training data' is placed below the large brown bubble rather than inside it or connected by a leader line, which creates ambiguity about whether the label refers to the bubble or the empty space below.
- **[writing]** Figure 3: The caption contains a grammatical error and missing noun ('Overview of .', 'Real-world experiments for our .'), likely due to a missing model name placeholder.
- **[writing]** Figure 3: The text labels for specific tasks (e.g., 'Sit on sofa', 'Play with cat') are rendered in a low-contrast light blue font that is difficult to read against the background.
- **[science]** Figure 4: The claim '5 times faster' is unsupported by the data shown; the fastest method (C++ COMM, 0.39 ms) is only ~8.5x faster than TWIST (3.32 ms), while the labeled 'final optimization' (TensorRT & Cache, 0.58 ms) is only ~5.7x faster. The comparison baseline (TWIST) is separated by a dashed line and not grouped with the optimization methods, making the direct comparison ambiguous.
- **[writing]** Figure 4: The y-axis labels are cluttered and inconsistent; 'C++ COMM' and 'TWIST CPU ONNX' are split across two lines while others are not, and the dashed line separating TWIST is not explained in the caption.
- **[science]** Figure 6: The y-axis label 'Zero-Shot MPJPE' is present, but the caption 'Data Scaling up Curve on Zero-shot Performance' is vague; it should explicitly state that lower MPJPE indicates better performance to ensure the downward trend is interpreted correctly.
- **[writing]** Figure 6: The y-axis has a break symbol (zigzag) but no numerical scale or tick marks are provided, making it impossible to verify the magnitude of the improvement or the spacing between data points.
- **[science]** Figure 7: The plot displays 'Training Loss' on the y-axis, but the caption describes it as a 'Model Scalability Comparison'. Scalability comparisons typically show performance metrics (e.g., accuracy, success rate) or efficiency metrics (e.g., FLOPs, latency) against model size or parameter count, not training loss curves.
- **[science]** Figure 7: The x-axis is labeled 'Training Steps' (50K to 200K), which measures training duration rather than model scale (e.g., number of parameters). This contradicts the caption's claim of a 'Model Scalability Comparison'.
- **[writing]** Figure 7: The y-axis label 'Training Loss' is split across two lines ('Training' and 'Loss') with excessive vertical spacing, making it difficult to read as a single unit.
- **[science]** Figure 8: The pie chart displays percentages (68%, 18%, 9%, 4%) that sum to 99%, implying a missing 1% slice or rounding error, yet no 'Other' category is shown to account for the discrepancy.
- **[writing]** Figure 8: The caption 'Data distribution visualization' is too vague; it fails to specify what the categories (PHUMA, Inhouse, etc.) represent (e.g., source of motion data, dataset split) or the total number of samples.
- **[writing]** Figure 8: The label 'Motion Million' is ambiguous and likely a typo or truncated name; it is unclear if this refers to a specific dataset or a category of motion.
- **[science]** Figure 9: The figure displays three bar charts showing 'Success Rate' vs. 'Cluster Num', 'History Length', and 'Envs Num', but the caption only states 'Ablation studies for Humanoid-GPT' without specifying what is being ablated or what the baseline is. The charts show parameter sweeps rather than ablation of specific model components.
- **[writing]** Figure 9: The y-axis lacks a scale or tick marks, making it impossible to judge the magnitude of differences between bars beyond the labeled values. The x-axis labels are rotated and partially illegible in the rendered image.
- **[science]** Figure 9: No error bars or confidence intervals are shown despite presenting experimental results, which limits the ability to assess statistical significance of the observed differences.
- **[fatal]** Figure 10: The figure has no caption, making it impossible to interpret the axes, the meaning of the 'Blue', 'Brown', and 'Light blue' labels, or the nature of the visualization (e.g., t-SNE, UMAP, or raw data).
- **[science]** Figure 10: The plot lacks axis labels and units, preventing any assessment of the feature space dimensions or scale.
- **[science]** Figure 10: The legend is ambiguous; 'Light blue: All' suggests an overlay of the other two categories, but the visualization does not clearly distinguish the specific contributions of 'AMASS' and 'LAFAN' versus the combined set.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating unnecessary barriers for non-specialist readers. In the Abstract and Section 1, the term "G1-retargeted" and the standalone "G1" are used without defining the Unitree-G1 humanoid robot. Similarly, "MoCap" is used repeatedly (e.g., Section 1, Section 3.1) without spelling out "motion capture." Section 3.1 introduces "PD controller" and "DoF" (degrees of freedom) without de

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 3.1 (Eq. 1), the reward function includes a term $R_{	ext{penal}}(t)$, but the text immediately following refers to it as $R_{	ext{panel}}(t)$. This typo breaks the logical link between the defined equation and the explanation of penalty terms.
- **[science]** In Section 4.1, the text claims 'TCN-L achieves 89.05% at 2B tokens' and cites a 56.15mm MPKPE gap. However, Table 1 only reports TCN results at 2M tokens. The specific data for TCN-L at 2B tokens is missing, making the claim of saturation unsupported by visible evidence.
- **[science]** In Section 5, the paper claims to 'derive a scaling law' but only provides qualitative descriptions of trends. Without fitted exponents or a mathematical form, the claim of a derived law is not logically supported by the presented analysis.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extend beyond the provided evidence, particularly regarding the magnitude of generalization, the existence of a formal scaling law, and the specific contribution of data modalities. First, the abstract and introduction repeatedly use the term "unprecedented" to describe the zero-shot generalization capabilities (Abstract, Sec 1). However, the empirical evidence for this is limited to a small set of four specific dance clips (Table 3) and a few teleoperation de

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The 'Ethical Considerations' section (sec/6_limitations.tex) states that all human motion recordings are obtained with 'informed consent' but fails to specify the IRB approval number or the specific consent protocol used for the 'large internally captured dataset' mentioned in the Introduction. Given the use of human subjects for data collection, explicit IRB documentation is required to verify compliance with ethical standards.
- **[science]** The paper describes deploying a high-speed, zero-shot motion tracker on a physical humanoid (Unitree-G1) capable of 'collaboratively carrying boxes' and executing 'high-dynamic' motions. The safety section mentions an 'emergency stop mechanism' but lacks a quantitative risk assessment or a detailed safety protocol for human-robot interaction (HRI) in unstructured environments, which is critical for preventing physical harm during real-world deployment.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The scaling law analysis in Sec. 5.1 lacks statistical rigor. The text claims 'marginal gains decrease' but provides no confidence intervals, standard errors, or p-values for the differences between the 200M and 2B token runs. Without error bars or multiple seeds, the observed trend could be noise. Please report variance across seeds or statistical significance tests.
- **[science]** The real-world evaluation in Sec. 4.3 relies on only four specific dance motions for quantitative metrics. This sample size is insufficient to support the broad claim of 'unprecedented zero-shot generalization' to 'diverse, complex' motions. Please expand the test set to include a statistically significant number of unseen motion categories or provide a power analysis justifying the current sample size.
- **[science]** The comparison with baselines in Table 2 is confounded by data scale. Baselines are trained on ~6-9M frames, while Humanoid-GPT uses 2B frames. The paper attributes gains to architecture but does not isolate the effect by comparing a Transformer trained on 9M frames against an MLP trained on 9M frames. The claim that 'Transformers offer superior tracking precision' is not fully supported without this controlled ablation.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 4.3 (Evaluation in Simulation), the text claims TCN-L achieves 89.05% SR at 2B tokens, but Table 1 (tab:sim_scaling_backbone) does not list a TCN-L row or a 2B token entry for TCN. This specific data point is missing from the provided evidence and must be added to the table or removed from the text to ensure reproducibility.
- **[science]** Section 4.2 defines diversity metrics (gstd, log-volume) but does not report the standard deviation or confidence intervals for these estimates across the 10,000 sampled embeddings. Given the claim that the new dataset has a '4-5x increase' in log-volume, statistical significance testing or error bars are required to validate this difference is not due to sampling variance.
- **[science]** The scaling law analysis in Section 5 (Scaling Laws) describes trends qualitatively and references figures (Fig. 4, Fig. 5) that are not visible in the text source. The manuscript must explicitly state the fitted power-law exponents (e.g., $P \propto N^{-lpha}$) and their confidence intervals in the text or appendix to substantiate the claim of 'predictable trends'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Training Motion Experts), the text states 'presenting in Fig ef{fig:pipeline}	extbf{(b)}'. This is grammatically incorrect and should be rephrased to 'as presented in Fig. ef{fig:pipeline}(b)' or 'shown in Fig. ef{fig:pipeline}(b)'.
- **[writing]** In Section 3.2 (Building Zero-shot Foundational Tracker), the sentence 'This design of our \methodname model naturally exploits the Transformer’s inherent strengths of parallel sequence supervision and autoregressive temporal predicting,  Moreover, because...' contains a comma splice and a double space. It should be split into two sentences or joined with a conjunction (e.g., '...predicting. Moreover, because...').
- **[writing]** In Section 4.1 (Analysis on Data Diversity), the phrase 'video-esti data' appears in the Summary of Contributions (Appendix). This is a typo for 'video-estimated data' and should be corrected for clarity.
- **[writing]** In Section 4.2 (Evaluation in Simulation), the 'Metrics' paragraph lists five metrics but introduces them with 'We report three quantitative metrics:'. This numerical inconsistency (three vs. five) is confusing and should be corrected to 'five quantitative metrics'.

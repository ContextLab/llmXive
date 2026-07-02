# Automated-review action items — Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims '0.1 in VBench Total, 0.3 in VBench Quality' over SOTA. Table 1 shows these deltas apply only to the 2-step setting (84.14 vs 84.04; 84.89 vs 84.59). The 4-step setting yields different deltas (Total 84.10 vs 84.04; Quality 84.94 vs 84.59). Clarify that these specific gains refer to the 2-step setting to avoid ambiguity.
- **[writing]** Section 3.2 claims cost reduction from ~11,600 to ~2,900 GPU hours at '80K-video scale'. Table 1 lists these exact numbers but does not explicitly label the dataset size. Add '80K' to the table caption or row labels to fully support the scalability claim.
- **[writing]** Abstract claims '50% reduction in first-frame latency'. Table 1 shows 0.60s vs 0.27s, which is a 55% reduction. While 50% is a valid approximation, 'over 50%' or '55%' is more precise given the specific data provided.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims 'causal ODE suffers from scene collapse,' but the corresponding images (top row, right) show a coherent scene with a mouse and treadmill, contradicting the description of collapse.
- **[science]** Figure 1: The caption claims 'causal DMD blurs the mouse’s legs into a single indistinguishable mass,' but the corresponding images (bottom row, right) show distinct legs and clear motion, contradicting the description.
- **[science]** Figure 2: The caption describes a single action ('moving forward continuously'), but the image displays a sequence of 8 distinct video frames. Without a time axis, frame indices, or a legend, it is impossible to verify the continuity of motion or the temporal resolution of the generation.
- **[writing]** Figure 2: The image contains a 'W' icon and 'A S D' keyboard keys overlaid on the scene. These UI elements are not defined in the caption or legend, making it unclear if they represent the input control signal or are artifacts of the rendering engine.
- **[science]** Figure 3: The 'Before asymmetric DMD' images show a man in water, while the 'After' images show a snowboarder; the caption claims 'better visual quality' but the visual content is completely different, making a direct quality comparison impossible.
- **[science]** Figure 3: The bar charts show VBench scores, but the y-axis scales are truncated (78-82 and 83-83.5) without a break indicator, exaggerating the performance difference between Causal CD and Causal ODE.
- **[science]** Figure 4: The caption claims 'Causal DMD yields lower VBench scores than causal CD', but the bar charts compare 'Causal CD' vs 'Causal DMD' (left) and 'Causal CD Init.' vs 'Causal DMD Init.' (right). The right chart's legend labels ('Causal CD Init.', 'Causal DMD Init.') do not match the caption's description of 'used as the initialization for Stage 3' — it is unclear if these are initialization methods or results after Stage 3. This creates ambiguity in interpreting the comparison.
- **[writing]** Figure 4: The y-axis labels on both bar charts lack units or context (e.g., 'VBench score (%)'), making it unclear what the numerical values represent despite the x-axis label 'VBench ↑'.
- **[science]** Figure 5: The caption claims 'Causal Forcing's causal ODE initialization performs well,' but the figure's third column is labeled 'DMD after Casual Forcing ODE initialization' (typo: 'Casual' vs 'Causal') and the bottom text states it 'requires costly data curation,' which contradicts the caption's claim that it is 'difficult to scale' due to cost rather than data curation requirements.
- **[writing]** Figure 5: The bottom text labels contain typos ('Casual' instead of 'Causal') and the red text 'costly data curation' is not explicitly defined in the caption, creating ambiguity about the specific cost factor.
- **[writing]** Figure 6 caption: The phrase 'reduces training cost by 4$$' contains a typo (likely meant '4x') that contradicts the '4x' label shown in the chart.
- **[writing]** Figure 6 caption: The claim of '50% lower latency' is imprecise; the chart shows a reduction from 0.6 to 0.27, which is a 55% reduction.
- **[writing]** Figure 7: The label 'Causal Forcing ++ (1-step)' is visually ambiguous; the caption claims the method 'surpasses Causal Forcing', but the image shows the 1-step variant performing worse than the 2-step and 4-step variants, creating a potential contradiction between the specific visual evidence and the general claim.
- **[writing]** Figure 7: The caption states the figure is a 'Performance comparison', but the image contains no quantitative metrics (e.g., VBench scores, FID, latency numbers) or axes; it relies entirely on subjective visual inspection without providing the data to support the 'outperforming' claim.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and shorthand that are not defined at their first point of use, creating a barrier for non-specialist readers. In the Abstract, terms like "PF-ODE," "AR," and "CD" (causal consistency distillation) appear without expansion. While "AR" is common, "PF-ODE" is a specific technical construct that requires definition (e.g., "Probability Flow Ordinary Differential Equation") to ensure clarity. Similarly, "DMD" is introduced in Section 1 and Sec

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Sec 3.2, the claim that causal CD and causal ODE share the 'same learning target' relies on the assumption that the teacher's ODE step is exact. However, Eq 5 bounds the error by O((Δt)^p), implying a non-zero discrepancy. The text should clarify if this discrepancy is negligible in practice or if the 'same target' claim is an approximation, to avoid logical overreach.
- **[science]** In Sec 3.3, the argument that causal DMD fails due to 'mode-seeking' behavior causing exposure bias is intuitive but lacks a formal causal link. The paper asserts that reverse KL concentrates mass, making it sensitive to drift, but does not explicitly derive why this specific sensitivity leads to the observed 'rapid drift' compared to forward KL. A brief theoretical justification or citation to a specific theorem on AR rollout stability under reverse KL would strengthen the causal chain.
- **[writing]** In Sec 4.1, the latency claim ('reduces first-frame latency by 50%') contradicts the ASD footnote stating the first frame is always 4-step. If the first frame cost is identical, the reduction must apply to streaming latency. Clarify that the 50% reduction refers to per-frame latency after the first frame to resolve this logical inconsistency.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of '50% lower first-frame latency' (Abstract, Sec 4) is over-claimed. The footnote in Table 2 explicitly states that the 1, 2, and 4-step settings share identical first-frame latency due to the ASD trick. The reduction applies to *subsequent* frames, not the first frame. This misrepresentation must be corrected to avoid misleading readers about real-time interactivity.
- **[writing]** The claim that Causal Forcing++ 'surpasses SOTA 4-step chunk-wise Causal Forcing' (Abstract) is partially unsupported. Table 2 shows Causal Forcing++ (2-step) has a lower Semantic score (81.13) than Causal Forcing (81.84). The paper generalizes 'surpasses' despite this specific metric deficit. The claim should be qualified to reflect trade-offs or focus only on the metrics where it leads.
- **[science]** The assertion that causal CD 'learns the same AR-conditional flow map' as causal ODE distillation (Sec 3.2) is presented as a theoretical fact but relies on the assumption that the ODE solver error is negligible. The paper does not provide a bound or empirical check on this error term in the AR context. This theoretical equivalence should be framed as an approximation or hypothesis rather than a proven identity.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Content Safety: How the model prevents the generation of harmful, illegal, or non-consensual content (e.g., deepfake pornography, political disinformation) when users provide specific action prompts.
- **[writing]** Real-Time Threats: The 50% latency reduction enables real-time interaction. The authors should discuss the implications of this speed for automated harassment or real-time manipulation scenarios.
- **[writing]** Mitigation Strategies: Are there plans to integrate safety filters, watermarking, or usage policies to mitigate these risks? Data Privacy and Consent: Section 4.1 states the use of OpenVid and VidProm datasets (80K videos). There is no mention of:
- **[writing]** Data Provenance: Whether these datasets contain personally identifiable information (PII) or copyrighted material.
- **[writing]** Consent: How the privacy and consent of individuals appearing in the training videos were handled.
- **[writing]** Compliance: Confirmation that the data usage complies with relevant regulations (e.g., GDPR) and the terms of service of the source datasets. Recommendation: The authors should add a "Safety and Ethics" section (or expand the Conclusion) to explicitly address these points. This should include a discussion of potential misuse, the limitations of the current safety measures (if any), and the data privacy considerations regarding the training set. Without this, the paper is incomplete regarding the

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 50% first-frame latency reduction contradicts the footnote stating first-frame latency is determined by 4-step generation for all methods. Clarify the metric or correct the claim.
- **[science]** Table 1 compares 1/2-step Causal CD against a 4-step Causal ODE baseline. Re-run Causal ODE initialization for 1-step and 2-step settings to ensure a fair ablation comparison.
- **[science]** Report standard deviations for the Stage 2 training time (11,600 vs 2,900 GPU hours) to validate the robustness of the 4x efficiency claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report uncertainty estimates (e.g., standard deviation or 95% confidence intervals) for all quantitative metrics in Tables 1 and 2. Current values are presented as single point estimates without indication of variance across seeds or prompts, making statistical significance claims unsupported.
- **[science]** Clarify the statistical test used to claim 'surpasses SOTA' in the abstract and results. With multiple metrics (Total, Quality, Semantic, etc.) and multiple baselines, a multiple-comparisons correction (e.g., Bonferroni or FDR) is required to avoid inflated Type I error rates.
- **[science]** Specify the sample size (N) and random seed configuration for the evaluation benchmarks (VBench, VisionReward). The text mentions '100 prompts' but does not state if results are averaged over multiple runs or if the 100 prompts constitute the full test set, which is critical for reproducibility.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1, the phrase 'Casual ODE initialization' appears as a paragraph heading. This is a typo for 'Causal ODE initialization' and should be corrected to maintain technical accuracy.
- **[writing]** In Section 4.1, the sentence 'These efficiency metrics are measured on the single A800 GPU...' contains a missing article. It should read 'measured on **the** single A800 GPU' or 'measured on **a** single A800 GPU'.
- **[writing]** In Section 4.2, the phrase 'which is we discuss the underlying reason' in the paragraph about Causal DMD is grammatically incorrect. It should be rephrased to 'which is why we discuss the underlying reason' or 'as we discuss the underlying reason below'.
- **[writing]** In the Abstract, the phrase 'in the spirit of Genie3' is slightly informal for a technical paper. Consider replacing it with 'following the Genie3 paradigm' or 'inspired by Genie3' for a more formal tone.

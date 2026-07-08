# Automated-review action items — OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a comprehensive taxonomy and benchmark of modern optimizers. However, several claims rely on citations to papers with future dates (2026) or methods that appear to be hypothetical or not yet widely recognized. Specifically, the benchmark results for RMNP, SPlus, SAC, and SGG are based on citations to 2026 preprints or methods that may not be fully established. This raises concerns about the reproducibility and validity of the benchmark claims. The authors should verify the exi

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The x-axis timeline is cluttered and inconsistent; the '2014' label is merged with '2015 - 2019', and the '2020' label is merged with '2020 - 2023', making the specific year boundaries difficult to parse.
- **[writing]** Figure 1: The x-axis labels '2014' and '2020' are visually merged with adjacent time ranges (e.g., '2014 2015 - 2019'), creating ambiguity about the start of the 'Stage II' and 'Stage III' periods.
- **[writing]** Figure 2: The top-left 'Iterations' arrow points to the S0 block but lacks a clear label or connection to the 'Training Iteration t' box, creating ambiguity about the temporal flow.
- **[writing]** Figure 2: The 'Transformer Blocks' section lists 'Self-Attn' and 'MLP / FFN weights' but does not explicitly link these to the 'trainable parameter groups' arrow feeding into S0, which could confuse readers about the source of gradients.
- **[science]** Figure 7: The caption states 'stars mark frontier members,' but the left plot shows 'Lion' (green star) and 'GaLore' (red star) as stars, while 'APOLLO' (purple star) is also a star. However, 'Lion' is clearly dominated by 'GaLore' and 'APOLLO' in both PPL and time/memory, so it should not be on the Pareto frontier. This misrepresents the frontier definition.
- **[writing]** Figure 7: The x-axis label 'Per-step time (ms)' on the left plot and 'Optimizer-state memory (GB)' on the right plot are clear, but the y-axis label 'C4 val PPL (1B)' is repeated identically on both plots without clarifying that the left is time and right is memory — though this is minor since the x-axes differ.
- **[science]** Figure 8: The colorbar legend is inverted relative to the data and caption. The caption states 'Green is favorable' (lower PPL/Time/Memory), but the colorbar labels 'better than AdamW' at the top (green) and 'worse than AdamW' at the bottom (red). However, the data shows AdamW (PPL 14.48) is colored green, while methods with better PPL (e.g., Adan 14.35) are also green, and methods with worse PPL (e.g., AdaBelief 16.79) are red. The issue is that the colorbar labels 'Time/Mem baseline' and 'same
- **[writing]** Figure 8: The colorbar legend has ambiguous labels. The top label 'Time/Mem baseline' is unclear because the heatmap includes three metrics (PPL, Time, Memory), but the label suggests the baseline applies only to Time and Memory. The middle label 'same as AdamW' is placed on the colorbar, but it is not clear if this refers to the color value or the metric value. The bottom label 'worse than AdamW' is clear, but the overall legend design is confusing. The colorbar should be relabeled to explicitl
- **[writing]** Figure 9 caption: states 'hatch = architecture' for panel (c), but the rendered plot uses color intensity (opacity) to represent architecture, not hatching patterns.
- **[science]** Figure 9: The y-axis in panels (a) and (b) is inverted (1 at top, 12 at bottom) to indicate '1 = best', but the axis labels are not explicitly marked as inverted or 'best at top', which can be confusing for standard plot reading.
- **[writing]** Figure 9: The x-axis labels in panels (a) and (b) are stacked vertically (e.g., 'Tr++' over '340M'), which is readable but could be improved by rotating or spacing them to avoid crowding.
- **[writing]** Figure 9: The legend in panel (b) is placed inside the plot area and partially obscures the data lines; moving it outside or making it semi-transparent would improve readability.
- **[writing]** Figure 9: The x-axis labels in panel (c) are rotated at an angle, which is good for readability, but some labels (e.g., 'MARS-Shampoo') are still slightly cut off or hard to read at the edges.
- **[writing]** Figure 9: The caption mentions 'hatch = architecture' for panel (c), but the plot uses color intensity (opacity) instead of hatching, creating a mismatch between description and visual representation.
- **[science]** Figure 10: The heatmap cells display raw GNormCV values (e.g., 111, 161) while the colorbar scale is normalized (0.3–111.6), creating a misleading visual mapping where the highest numerical value (161) is colored identically to the scale's maximum (111.6).
- **[writing]** Figure 10: The x-axis labels ('340m', '1b') are ambiguous and do not specify the architecture or scale they represent, which is critical for interpreting the 'across architectures' claim in the caption.
- **[writing]** Figure 11: The caption defines the sensitivity score as '$s_LR$', but the panels display '$s$'; align the notation in the caption with the figure labels.
- **[writing]** Figure 11: The legend uses the symbol '★' for 'Best LR', but the caption states 'The star marks the tuned learning rate'; clarify if 'Best LR' and 'tuned learning rate' are synonymous.
- **[science]** Figure 12: The caption states the profile covers objectives O1–O6, but the heatmap only displays five columns (Performance, Efficiency, Stability, Robustness, Generalization). The mapping between these labels and the O1–O6 objectives is not provided in the caption or the figure, making it impossible to verify the data against the claimed metrics.
- **[science]** Figure 12: The colorbar indicates that green is 'best' and red is 'worst', but the underlying data values are not normalized or defined. For example, 'Performance' shows 14.35 (green) while 'Robustness' shows 23.0 (red); without knowing if lower or higher is better for each specific metric, the color mapping appears arbitrary and potentially misleading.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper is generally well-structured for a specialized audience, but it relies on a few internal shorthand conventions and symbols that are introduced in one section and then used extensively in others without immediate re-expansion or definition. Specifically, the symbol S_{opt} in the memory equation (Section 2.1) appears without a definition, creating a minor barrier for a reader not intimately familiar with the authors' specific notation for optimizer state counts. Similarly, the acronym "

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 5.2 claims 'removing AdamW's second moment collapses PPL to 70.74' in the Muon ablation, but Table 5 (tab_muon_cross_validation) does not contain a 'No Second Moment' row or the value 70.74. The text describes a specific ablation condition that is not represented in the cited table, creating a non-sequitur between the claim and the evidence.
- **[writing]** Section 5.2 states 'adding Newton--Schulz (NS) orthogonalization recovers to 16.86,' yet Table 5 lists the 'Standard Muon' (which includes NS) PPL as 16.60 at 350M. The text's specific value (16.86) contradicts the table's value (16.60) for the same configuration without explanation.
- **[writing]** Section 5.2 claims 'LR scaling and Nesterov provide secondary gains,' but Table 5 shows that for Gated DeltaNet (GDN-340M), the 'Both combined' configuration (24.12) is worse than 'Symmetric LR Scaling' alone (24.02). The text's generalization of 'gains' contradicts the specific data point in the table where the combination degrades performance.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Conclusion: Replace 'validates that no single optimizer dominates' with 'suggests no single optimizer dominates under tested protocols.' Qualify 'selection must match' to 'selection should match within these constraints' to avoid universal claims beyond the 24 optimizers and 2 domains tested.
- **[writing]** Conclusion: Rephrase 'Two empirical regularities' to 'Two observed trends in our study.' Specify that 'aggressive state compression is rank-bounded' applies to the tested T4 methods (APOLLO, AdaFactor) and 'spectral geometry is architecture-conditional' refers to the specific T2 instances (Muon, SOAP) evaluated.
- **[writing]** Section 5.2.5: Change 'Optimizer performance is strongly architecture-dependent' to 'Performance varied across the tested vision backbones.' Scope the claim to the three specific architectures (ResNet50, DeiT-S, CAFormer-S12) to prevent overgeneralization to untested model families.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a taxonomy and benchmarking study of modern optimization algorithms for deep learning. From a safety and ethics perspective, the work is low-risk. The research focuses on algorithmic efficiency, convergence properties, and memory usage of optimizers (e.g., AdamW, Muon, SOAP, Lion) applied to standard benchmarks (C4, FineWeb-Edu, CIFAR100).

There are no indications of dual-use capabilities that lower the barrier to harmful activities (e.g., automated vulnerability discovery, biological synthesis, or persuasive disinformation generation). The methods described are standard mathematical operations for training neural networks and do not constitute operational exploits or attack vectors.

The data sources cited (C4, FineWeb-Edu, CIFAR100) are public, widely used datasets in the ML community. The paper does not appear to use scraped data in violation of terms of service, nor does it release any datasets containing personally identifiable information (PII) or sensitive human subject data. No human subjects were involved in the experiments (no surveys, interviews, or behavioral logs), so IRB/consent statements are not required.

The paper does not disclose any conflicts of interest, but given the nature of the work (benchmarking existing open-source algorithms), there is no immediate evidence of undisclosed commercial bias that would constitute a safety or ethical violation. The authors acknowledge limitations regarding protocol sensitivity and scope, which is appropriate.

No specific, foreseeable risks of harm were identified that require mitigation or disclosure beyond what is standard for this type of algorithmic benchmarking research.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents an extensive benchmark of 24 optimizers across multiple scales and architectures, but the evidentiary strength of the central claims is compromised by a lack of variance reporting and potential confounds in hyperparameter tuning. First, the headline results in Section 4.2 (Tables 1, 2, and 3) are presented as definitive rankings based on single training runs. For instance, the claim that APOLLO achieves a PPL of 13.53 at 1B parameters, significantly outperforming AdamW (14.48)

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.2 and Tables 3-10 report single-point performance metrics (e.g., '13.53 PPL', '80.53%') without any measure of uncertainty (SD, SE, or CI) or mention of the number of random seeds used. In deep learning benchmarking, single-run results are indistinguishable from noise. Report mean ± SD over at least 3 seeds for all headline numbers, or explicitly state that results are from a single run and treat them as illustrative rather than definitive.
- **[writing]** Section 5.2.1 and Table 1 claim 'best' or 'worst' performance (e.g., APOLLO at 13.53 vs AdamW at 14.48) based on point estimates. Without reported variance or a statistical test (e.g., paired t-test or bootstrap), these differences cannot be distinguished from random fluctuation. Add error bars to figures and report statistical significance or effect sizes for all comparative claims.
- **[science]** The paper compares 24 optimizers across multiple architectures and scales (Section 5.2), effectively performing dozens of pairwise comparisons. However, no correction for multiple comparisons (e.g., Bonferroni, Holm, or FDR) is mentioned when declaring 'winners' or 'tiers'. This inflates the false-positive rate. Apply a correction method to the reported p-values or rephrase claims to avoid implying statistical significance where none was tested.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a dense, information-rich survey and benchmark. The prose is generally technical and precise, but several structural and syntactic issues create friction for the reader, requiring re-reading to parse the intended meaning or locate key claims. The most immediate issue is a punctuation error in Section 3.1 (Universal Meta-Pipeline), where item S4 contains a stray closing parenthesis ("S4 (Reconstruction):)"). While minor, such errors disrupt the visual rhythm of a structure

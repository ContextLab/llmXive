# Automated-review action items — Many-Shot CoT-ICL: Making In-Context Learning Truly Learn

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that CDS yields a '5.42 percentage-point gain on geometry with 64 demonstrations' (Abstract, Intro) is not supported by Table 1 in section/curvature.tex. For Qwen3 on geometry at 64 shots, the gain is 3.75 points (68.89 vs 65.14). The 5.42 figure appears to correspond to the gpt-5.2 model (80.79 vs 75.37), but the text does not specify this model, creating a misleading generalization.
- **[science]** In section/curvature.tex, Algorithm 1 contains a syntax error in the line: 'm[j] <- m[j] + x * score^{(j)}_{M}'. The variable 'x' is undefined. The text claims this algorithm outputs a correlation coefficient, but the undefined variable prevents verification of the calculation logic described.
- **[writing]** The paper claims 'Qwen3-Embedding-4B' is used for embeddings (Appendix, Section 4.3). However, the bibliography entry 'zhang2025qwen3embeddingadvancingtext' is not present in the provided .bib file. The citation exists in the text but lacks a corresponding reference entry, making the source unverifiable.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The y-axis on the 'BANKING77' subplot is non-linear and discontinuous (jumps from 20 to 45 to 70), which visually compresses the performance differences between the 'Original' and 'Most Similar' lines and exaggerates the flatness of the 'Most Dissimilar' line.
- **[writing]** Figure 2: The legend in the 'BANKING77' subplot is incomplete; it lists 'Sim>Ori/Dis' and 'Ori/Dis>Sim' (shaded regions) but fails to define the specific line styles (solid, dotted, dashed) for the 'Original', 'Most Similar', and 'Most Dissimilar' data series.
- **[science]** Figure 3: The y-axis scale is non-linear and discontinuous (jumps from 20 to 45 to 70), which visually distorts the performance gaps between the 'Original' and 'Most Similar' lines, making the 'Most Similar' line appear flat and superior when the absolute difference is small.
- **[writing]** Figure 3: The legend in the top-left subplot ('BANKING77') is positioned over the data area and lacks a background box, reducing readability against the shaded region.
- **[science]** Figure 4: The y-axis scales are inconsistent and misleading across subplots. For example, the GSM8K plots use a scale of 30–70 (left) versus 89–92 (right), and the number_theory plots use 28–40 (left) versus 78–82 (right). This prevents valid visual comparison of performance trends between the Llama 3.1 and Qwen 2.5 models.
- **[writing]** Figure 4: The legend in the top-left subplot (GSM8K, Llama 3.1) is missing the 'wr' (wrong answer) entry, which is present in the other subplots and the caption, making the data series incomplete.
- **[science]** Figure 5: The left subplot (Qwen 3 8B) includes a 'first_qwen3(14b)' series (diamonds) and a shaded 'wr>origin' region, but the right subplot (Qwen 3 14B) omits both the diamond series and the shaded region despite the caption implying a direct comparison of the same methods across models.
- **[writing]** Figure 5: The y-axis on the left subplot is labeled 'Accuracy' but lacks a visible scale or tick marks, making it impossible to read the specific performance values for the plotted points.
- **[writing]** Figure 6: The caption 'Llama-3.1-8B-Instruct' is insufficient; it fails to describe the plot's content (normalized accuracy vs. number of examples) or define the legend entries (e.g., WSC, COPA, GSM8K).
- **[science]** Figure 6: The y-axis 'Normalized Accuracy' includes negative values (down to -2), but the metric is undefined; without a baseline or formula, the meaning of negative accuracy is unclear.
- **[writing]** Figure 6: The x-axis label 'Number of examples in-context' is centered between two distinct panels, creating ambiguity about whether the scale applies to both or if they represent different conditions.
- **[science]** Figure 7: The right panel legend defines four series (number_theory_owO, geometry_owO, number_theory_R1, geometry_R1), but the plot displays eight lines (four solid, four dashed). The legend fails to map the dashed line styles to their corresponding models, making the data unreadable.
- **[writing]** Figure 7: The x-axis tick labels (20, 50, 80) are positioned inconsistently between the left and right panels, and the axis title 'Number of examples in-context' is centered below both, creating ambiguity about which scale applies to which panel.
- **[science]** Figure 8: The caption claims 'consistent performance improvements' for the Qwen3 family, but the left panel (8B) shows 'number_theory' and 'c&p' lines that decline significantly as examples increase, directly contradicting the text.
- **[writing]** Figure 8: The x-axis label 'Number of examples in-context' is centered below the panels, but the tick labels (20, 50, 80) are not aligned with the data points, making it difficult to read specific values.
- **[science]** Figure 9: The legend in the 'BANKING77' subplot (top-left) includes a 'Most Dissimilar' entry (red triangle), but the corresponding data line is missing from the plot area, making the legend inconsistent with the visual data.
- **[writing]** Figure 9: The y-axis label 'Accuracy' is placed on the far left and applies to the top-left plot, but the other three subplots (DetectiveQA, geometry, number_theory) lack individual y-axis labels or tick labels, making it unclear if they share the same scale or units.
- **[science]** Figure 10: The y-axis is labeled 'Standard Deviation' but displays negative values (down to -1.5), which is mathematically impossible for standard deviation. The caption does not define a transformation (e.g., log, z-score, or difference) that would explain these negative values.
- **[writing]** Figure 10: The legend uses specific model names (e.g., 'BANKING77_Qwen2.5', 'nt_Qwen3') but the caption describes the data only by task type ('classification' vs 'reasoning') and model family ('Qwen2.5' vs 'Qwen3'), failing to explicitly map the specific datasets (BANKING77, NLU, geometry) to the color groups described.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and acronyms that are either undefined or used in a way that assumes significant prior knowledge of specific sub-fields (educational psychology, differential geometry applied to embeddings). In the Abstract, the term "CoT-ICL" is used immediately without first spelling out "Chain-of-Thought In-Context Learning." While "ICL" is defined, the compound acronym is not. Similarly, "CDS" is introduced in the abstract without its full name, "Curvi

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that CDS yields 'up to a 5.42 percentage-point gain' (Abstract) is not supported by Table 1 in section/curvature.tex, where the maximum observed gain is 5.24 points (geometry, gpt-5.2, 16 shots). The text must be corrected to match the empirical data or the specific instance yielding 5.42 must be cited.
- **[writing]** The paper claims 'consistent gains across math and narrative reasoning' in the Conclusion, but Table 1 shows CDS underperforms the baseline on number_theory for Qwen3 (87.78 vs 86.30 at 64 shots is a gain, but 87.22 vs 86.30 at 64 shots is a gain, wait, 87.78 > 86.30 is a gain. However, at 128 shots, 90.74 vs 90.93 is a loss). The claim of 'consistent' gains is an overstatement given the performance drop at 128 shots for Qwen3 on number_theory.
- **[writing]** The abstract states similarity-based retrieval 'fails on reasoning' because 'semantic similarity poorly predicts procedural compatibility.' While the data shows similarity-based retrieval often underperforms random/original baselines, the paper does not definitively prove the *mechanism* is solely procedural incompatibility without ruling out other factors (e.g., noise in the embedding space for long CoT texts). The causal link is slightly over-claimed.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Impact Statement (Section 7) is generic and dismissive. Given the paper's focus on reasoning capabilities and the potential for these methods to automate complex problem-solving (e.g., in education or security), a more specific discussion of dual-use risks (e.g., generating sophisticated disinformation or bypassing safety filters via improved reasoning) is required.
- **[writing]** The study uses self-generated CoT demonstrations from weaker models (Section 4.2.1). The authors should explicitly address the risk of propagating or amplifying model hallucinations and biases when these "understandable" but potentially incorrect rationales are used as training signals for test-time learning.
- **[writing]** The paper relies on proprietary models (e.g., gpt-5.2, DeepSeek-R1) and embedding models (Qwen3-Embedding-4B) without detailing their safety alignment or known bias profiles. A brief note on the safety characteristics of the evaluated models or the potential for bias in the embedding space used for curvature calculation is needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of a 5.42 percentage-point gain on geometry (Abstract) lacks explicit statistical significance testing (e.g., p-values or confidence intervals) in the main text. While Appendix Table 3 shows means and standard deviations, the main text should explicitly state whether the observed gains are statistically significant to rule out random variance, especially given the reported order-scaling variance.
- **[science]** The 'Procedural-corruption ablation' (Table 1, section/factor.tex) shows a performance drop at n=128 but not at n=16. The sample size (number of test instances) for these specific ablation experiments is not explicitly stated in the text or table captions. Please report the number of test samples (N) used to calculate these accuracy percentages to allow for proper assessment of the effect size and statistical power.
- **[science]** The correlation analysis between curvature and performance (Section 4.3.2) reports Pearson r values (e.g., -0.547) but does not provide the number of permutations (k) sampled to generate these correlations. Since the correlation is computed over random orderings, the robustness of this finding depends on the sampling size. Please specify the number of random orderings used for the correlation analysis.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical analysis in this paper is generally sound in its experimental design, particularly the use of multiple random seeds (n=5) to estimate variance in demonstration ordering (Section 4.3, Appendix B). The distinction between non-reasoning and reasoning tasks is well-supported by the observed trends in Figures 1 and 2. However, several specific statistical and methodological details require clarification to ensure full reproducibility and rigor. First, Algorithm 1 in Appendix C contain

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction, the sentence 'our experiment uncover' contains a subject-verb agreement error. It should be 'our experiments uncover' or 'our experiment uncovers'.
- **[writing]** In the Related Works section, the sentence 'Auto-CoT... propose an automatic few-shot CoT prompting method' has a subject-verb agreement error. 'Auto-CoT' is singular, so it should be 'proposes'.
- **[writing]** In the Conclusion, the phrase 'rapid, low cost customization demonstrations orders' is grammatically incoherent. It likely intends to say 'rapid, low-cost customization of demonstration orders'.
- **[writing]** In section/curvature.tex, the sentence 'Our theoretical claim only requires a sufficiently smooth pedagogical progression, not the global minimum of Eq.~\eqref{eq:CDS_curvature}; empirically, this approximation is effective and remains inexpensive, taking under one minute on a standard CPU for n\le128.' contains a run-on structure. Consider splitting into two sentences for better flow.
- **[writing]** In section/factor.tex, the phrase 'With purely surface matching and LLMs are likely to be misled' is grammatically broken. It should be rephrased, e.g., 'With purely surface matching, LLMs are likely to be misled'.

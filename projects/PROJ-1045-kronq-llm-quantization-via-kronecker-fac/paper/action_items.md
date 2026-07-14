# Automated-review action items — KronQ: LLM Quantization via Kronecker-Factored Hessian

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims GPTQ/GPTAQ produce '>2000 perplexity' on LLaMA-3-70B at 2-bit, but Table 1 shows GPTQ at 2560.14 and GPTAQ as 'NaN'. Clarify that GPTQ yields ~2560 PPL while GPTAQ diverges (NaN) to accurately reflect the distinct failure modes.
- **[writing]** Abstract and Section 5.1 cite 7.93 perplexity for LLaMA-3-70B at 2-bit, but the primary Table 1 reports 8.43. The 7.93 value appears only in the Appendix. Update the abstract and text to cite the primary table value (8.43) or explicitly distinguish the sources.
- **[writing]** Section 5.1 states KronQ 'nearly doubles' GPTAQ on LiveCodeBench, but Table 4 shows >2x gains (37.3 vs 16.3 and 22.3 vs 9.6). Change 'nearly doubles' to 'more than doubles' to accurately reflect the magnitude of improvement shown in the data.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1 caption: The phrase 'GPTQ, GPTAQ, and on LLaMA-2-13B' is grammatically incomplete; it omits the third method name before the model list, though the legend identifies KronQ.
- **[writing]** Figure 1 caption: The list of methods 'GPTQ, GPTAQ, and KronQ' is grammatically incomplete; it omits the third method name before the model list, though the legend identifies KronQ.
- **[writing]** Figure 2(a) caption contains a typo '$$-incoherence' instead of the symbol '$\mu$-incoherence' shown on the plot axis.
- **[science]** Figure 2(b) y-axis labels (0, 1024, 2048, 3072, 4096) are inverted (0 at top, 4096 at bottom), which contradicts the standard convention for matrix visualization where row 0 is typically at the top.
- **[writing]** Figure 3: The y-axis labels use single letters (o, k, q, v) which are ambiguous without a legend or explicit definition in the caption stating they correspond to the output, key, query, and value projections.
- **[writing]** Figure 3: The labels '#4 o', '#5 k', etc., are rendered with a vertical bar artifact (e.g., 'k|', 'q|') likely due to a font rendering error, making them look like 'k|' or 'q|' instead of just the letter.
- **[science]** Figure 4: The x-axis labels (2.0, 2.17, 2.29, 2.43, 2.57, 3.0) are non-uniform and do not correspond to the visual spacing of the data points, making the 'Average Bit-width' scale misleading and difficult to interpret.
- **[writing]** Figure 4: The inset plot's x-axis is labeled only with '3.0', failing to show the full range of bit-widths for the zoomed-in region, which limits the utility of the inset for comparing the methods at that specific scale.
- **[science]** Figure 5: The caption states the data is 'relative to the bf16 baseline,' but the y-axes are labeled with absolute units ('Peak VRAM (GB)' and 'TPOT (ms/token)') and the bars show absolute values (e.g., ~100 GB) rather than relative ratios. This contradicts the caption's description of the data presentation.
- **[writing]** Figure 5: The legend in panel (a) includes 'W2', but the corresponding dark blue bars are not visible in the chart, likely obscured by the 'W4' bars or missing entirely, making the data for W2 unreadable.
- **[writing]** Figure 6: The caption is explicitly '(no caption)', leaving the plot unexplained and failing to define the context (e.g., model size) or the specific methods being compared.
- **[science]** Figure 6: The inset plot's x-axis is labeled '3.0' without a range or tick marks, making it impossible to determine the bit-width scale or the specific data points being highlighted.
- **[writing]** Figure 6: The x-axis label 'Average Bit-width' is present, but the axis ticks (2.0, 2.17, etc.) are rotated and crowded, reducing readability.
- **[writing]** Figure 7: The provided image is a 3-panel plot showing 'Original', '$H_X$ only', and '$H_X + H_G$' weight distributions with $CV_{in/out}$ metrics, which matches the content of Figure 2(b) in the paper, not Figure 7. The caption 'Weight distributions of LLaMA-2-70B' does not match the visual content shown.
- **[science]** Figure 7: The figure displays data for LLaMA-2-7B (inferred from the 8192 channel dimension and similarity to Figure 2), but the caption claims it shows LLaMA-2-70B. This is a factual mismatch between the visual data and the caption.

## paper_reviewer_jargon_police — verdict: accept

The manuscript demonstrates excellent accessibility for a competent reader from an adjacent field (e.g., optimization, numerical linear algebra, or general deep learning). The authors consistently define all non-standard acronyms, symbols, and method names at their first occurrence.

Specifically, the paper handles its specialized vocabulary well:
- **Acronyms:** Terms like "PTQ" (post-training quantization), "OBS" (Optimal Brain Surgeon), "K-FAC" (Kronecker-factored Approximate Curvature), and "BiIP" (Bidirectional Incoherence Processing) are explicitly expanded upon first use. Even newer or more specific terms like "LDLQ" are introduced with sufficient context or referenced to prior work where the definition is standard.
- **Notation:** The mathematical notation is rigorous and self-contained. Variables such as $\mathbf{H}_X$ (input activation covariance) and $\mathbf{H}_G$ (gradient covariance) are defined immediately before or within the equations where they appear (e.g., Section 3.1, Eq. 1 and Eq. 2). The dimensions of matrices (e.g., $\mathbf{X} \in \mathbb{R}^{d_{\mathrm{in}} \times n}$) are clearly stated in the Preliminary section.
- **Method Names:** References to specific algorithms (GPTQ, GPTAQ, QuIP, QuIP#, etc.) are accompanied by brief, one-sentence descriptions of their function or the specific limitation they address, ensuring a reader unfamiliar with the specific subfield of LLM quantization can follow the comparative logic.
- **Buzzwords:** Terms like "incoherence" are not used as vague buzzwords; they are given a precise mathematical definition ($\mu$) in Section 3.2 (Eq. 4) and explained intuitively.

There are no instances of undefined symbols, unexplained acronyms, or "lab slang" that would stall a reader with a strong PhD in a neighboring discipline. The paper successfully bridges the gap between the specific subfield of LLM quantization and the broader machine learning community.

## paper_reviewer_logical_consistency — verdict: accept

The paper's logical structure is sound and internally consistent. The central argument—that incorporating the gradient covariance $\mathbf{H}_G$ via the Kronecker-factored Hessian approximation improves quantization—follows logically from the premises. The derivation of the quantization objective (Eq. 6) correctly applies the K-FAC assumption, and the subsequent claim that $\mathbf{H}_G$ cancels in the column-wise OBS update (Proposition 1) is mathematically entailed by the provided proof in the Appendix.

The experimental claims are consistent with the presented data. The abstract's claim that GPTQ/GPTAQ diverge on LLaMA-3-70B at 2-bit while KronQ succeeds is directly supported by Table 3 (showing NaN/2560.14 vs 8.43) and the text in Section 5.1. The mixed-precision argument (Section 5.3) correctly links the proposed sensitivity metric $s_\ell = \mathrm{tr}(\mathbf{H}_G)\cdot\mathrm{tr}(\mathbf{H}_X)$ to the observed improvement in perplexity over activation-only baselines, as evidenced by Table 4 and Figure 4.

Definitions and notation remain stable throughout: $\mathbf{H}_X$ and $\mathbf{H}_G$ are consistently defined as input activation and gradient covariances, respectively. The scope of claims is appropriately bounded; for instance, the "generalization" claims in the abstract and conclusion are qualified by the specific models and bit-widths tested (LLaMA-2/3, W2/W3/W4), matching the experimental setup in Section 5.1. No contradictions were found between the limitations section and the results, nor between the method description and the algorithm pseudocode. The logical flow from problem identification (input-only Hessian) to solution (KronQ) to validation (experiments) is coherent.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract: The claim that GPTQ/GPTAQ 'diverge' at 2-bit is specific to LLaMA-3-70B (Table 3), yet the abstract implies a general failure of these methods. Table 1 shows they work on LLaMA-2 models. Scope the claim to 'on LLaMA-3-70B' to avoid implying universal divergence.
- **[writing]** Introduction: The claim of 'consistent state-of-the-art results' overstates the marginal gains on LLaMA-2-70B (W4). Clarify that gains are 'particularly significant at ultra-low bit-widths where baselines fail' to match the evidence in Tables 1 and 3.
- **[writing]** Section 5 & Conclusion: Claims of generalization to 'newer model families' and 'harder benchmarks' rely on limited tests (2 models, specific bits). Add qualifiers like 'on the tested newer model families' to align the scope with the specific evidence provided.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a post-training quantization (PTQ) method for Large Language Models (LLMs) that incorporates gradient covariance into the quantization objective. The work is purely algorithmic and computational in nature, focusing on model compression and efficiency.

A review of the manuscript for safety and ethics risks yields no actionable concerns:
1.  **Data Provenance:** The method uses standard, public calibration datasets (WikiText-2) and publicly available model weights (LLaMA-2, LLaMA-3, etc.). There is no use of private, sensitive, or scraped personal data requiring consent or IRB approval.
2.  **Dual-Use Risk:** While the resulting quantized models are more efficient and could theoretically be deployed in various contexts, the method itself (KronQ) does not lower the barrier to a specific harmful capability (e.g., generating disinformation, bypassing safety filters, or creating biological agents) in a way that differs from standard quantization techniques. The paper does not describe a system designed to deceive, surveil, or manipulate.
3.  **Vulnerability Disclosure:** The paper does not report a security vulnerability in a live system or an operational exploit; it reports a performance improvement in a compression algorithm.
4.  **Bias and Fairness:** The evaluation focuses on perplexity and standard commonsense reasoning benchmarks. The paper does not claim to address or introduce specific demographic biases, nor does it present results that suggest a new, unmitigated fairness harm to an identifiable group.

The research falls squarely within the domain of low-risk systems optimization. No specific disclosures, mitigations, or ethics statements are required beyond standard academic practice for this type of work.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method for incorporating gradient covariance into post-training quantization, but the experimental evidence relies heavily on single-run results without reported variance. Table 1 and Table 3 present headline perplexity and accuracy numbers (e.g., 8.15 vs 9.81 on LLaMA-2-7B at W2) as definitive facts. In the context of post-training quantization, where performance can fluctuate based on random seeds, calibration data ordering, or floating-point non-determinism, a

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Table 2 report single-point perplexity and accuracy values (e.g., '5.56', '79.2') without any measure of uncertainty (standard deviation, standard error, or range). Given that quantization results can vary with calibration seeds or numerical noise, report mean ± SD over at least 3 independent runs for all reported metrics to establish stability.
- **[writing]** The abstract and Section 4.1 claim GPTQ/GPTAQ 'diverge' or produce 'degenerate' results (e.g., PPL > 2000) while KronQ achieves low PPL. While the magnitude difference is clear, the paper lacks a formal statistical test or confidence intervals to confirm that the observed gains (e.g., 7.93 vs >2000) are not artifacts of a single lucky/unlucky calibration seed. Report variance across seeds or explicitly state that results are deterministic under the fixed seed used.

## paper_reviewer_writing_quality — verdict: accept

The manuscript demonstrates high writing quality, allowing a reader to move through the technical argument with minimal friction. The abstract effectively summarizes the problem, the proposed method (KronQ), and the headline results, including the specific perplexity gains on LLaMA-3-70B. The introduction clearly establishes the limitation of existing methods (ignoring $\mathbf{H}_G$) and outlines the contributions with precise topic sentences.

Throughout the paper, the logical flow is maintained. The transition from the Preliminary section to the Method section is smooth, with the Kronecker-factored approximation introduced naturally as a solution to the stated problem. Paragraphs are well-structured, typically opening with a clear statement of the point to be made (e.g., the motivation for bidirectional incoherence processing) followed by the necessary mathematical derivation or empirical evidence.

The prose is concise and professional. Technical terms are used consistently (e.g., $\mathbf{H}_X$, $\mathbf{H}_G$, BiIP), and the distinction between the base quantizer (GPTAQ) and the proposed enhancements is maintained without confusion. Transitions between sections, such as moving from the theoretical derivation of the sensitivity metric to the experimental validation of mixed-precision allocation, are handled effectively with signposting sentences.

While the paper is dense with mathematical notation, the surrounding text successfully guides the reader through the derivations, explaining the intuition behind equations like the Kronecker-factored objective and the cancellation of $\mathbf{H}_G$ in the update rule. The experimental section is well-organized, with clear subheadings for different quantization regimes and ablation studies that directly address the components of the proposed method. There are no instances of garden-path sentences, ambiguous pronoun references, or structural ordering issues that would force a reader to re-read a passage to grasp the meaning. The writing is clear, direct, and effectively communicates the paper's contributions.

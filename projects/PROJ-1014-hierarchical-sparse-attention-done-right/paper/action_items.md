# Automated-review action items — Hierarchical Sparse Attention Done Right: Toward Infinite Context Modeling

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a novel sparse attention mechanism, HiLS, with strong empirical results. However, several factual claims regarding performance metrics and comparisons require precise alignment with the provided tables to avoid overstatement or ambiguity. First, the Abstract claims HiLS extrapolates "64x the training context length with 90% retrieval accuracy." The training length is 8K, so 64x is 512K. Table 345M_main_ruler shows HiLS achieving 100% on Single Needle (S-N) at 512K, but 91% on

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption text is truncated mid-sentence at the end ('...loss c [HiLS-Attn.png]'), leaving the explanation of the gradient flow incomplete.
- **[writing]** Figure 2: The caption 'NSA kernel [kernel_design_NSA.pdf]' is a placeholder filename rather than a descriptive summary of the diagram's content.
- **[writing]** Figure 2: The text inside the green box ('(K,d)-(d,S) Compute m Tensor Core') is extremely small and illegible, making the specific operation unclear.
- **[science]** Figure 2: The diagram uses variable names (e.g., 'd', 'S', 'G', 'M') and specific tensor shapes without a legend or axis labels to define their dimensions or meaning.
- **[writing]** Figure 3 caption: contains broken LaTeX syntax ('Tab. \& Tab.') and a dangling file reference ('[1B_ppl_ruler_combined.pdf]') that should be removed.
- **[science]** Figure 3a: the y-axis label 'Perplexity' is missing units or a note that lower is better, though this is standard, the scale jump to '>10^2' is abrupt and lacks a clear visual break or annotation style consistency with other values.
- **[writing]** Figure 3b: the y-axis label 'RULER average exact match (%)' is present but the legend does not specify what 'Steps' refers to (training steps? inference steps?), though context implies training steps — clarify in caption or legend.
- **[writing]** Figure 4: The caption contains a typo 'at $$16K' with an extraneous dollar sign.
- **[writing]** Figure 4: The x-axis label 'Latency (ms, log scale)' is missing the '/token' unit for panel (b), which is present in the caption but not the axis label.
- **[science]** Figure 5: The left panel's y-axis is labeled 'Chunk ids (log scale)' but the caption describes it as 'loaded union size'; the axis label should be corrected to 'Loaded union size' to match the description and data.
- **[writing]** Figure 5: The right panel's y-axis label 'Overlap / reuse (%)' is ambiguous; it should be clarified as 'Overlap / reuse fraction (%)' or similar to distinguish between the two metrics being plotted.
- **[writing]** Figure 5: The legend in the right panel uses 'Layer range' for the shaded region, but the caption defines it as 'layer-wise min--max range'; the legend should be updated to match the caption's terminology.
- **[science]** Figure 6: The caption claims to compare 'HiLS-Attention' vs 'full attention', but the legend labels the baseline as 'Olmo3-CPT (YaRN)'. YaRN is a specific extrapolation method, not standard full attention, which misrepresents the comparison and the claim of 'strong long-context extrapolation advantages'.
- **[writing]** Figure 6: The y-axis label 'RULER average exact match (%)' is rotated 90 degrees and partially cut off at the top, making it difficult to read.
- **[fatal]** Figure 7: The caption is explicitly '(no caption)', yet the figure contains a legend ('Olmo3-CPT (YaRN)', 'Olmo3-HiLS-Attn') and specific data points that are not defined in the text or other captions.
- **[science]** Figure 7: The x-axis labels (8K, 16K, 32K, 64K, 128K, 256K, 512K, 1M) are not evenly spaced visually, but the axis is drawn as a linear scale, which misrepresents the exponential growth of context length.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper is generally well-written and uses standard terminology for the field of LLMs and attention mechanisms (e.g., "RoPE", "GQA", "KV cache", "perplexity"). However, there are a few instances where acronyms or specific method names are introduced without immediate definition, which could stall a competent reader from an adjacent field (e.g., a researcher in NLP who does not specialize in sparse attention architectures). Specifically, "BSA" (Block Sparse Attention) appears in the Introductio

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.1 claims HiLS-Attn 'sustains performance comparable to full attention' on MK-MQ, but Table 345M_main_ruler shows HiLS (95) vs Full-Attn (97). The text implies parity where the table shows a 2-point gap. Clarify if 'comparable' allows this margin or correct the claim.
- **[writing]** Section 4.2 states HiLS 'consistently outperforms' Full-Attn HoPE, but Table 345M_256K_ppl shows HiLS (7.51) vs Full-Attn HoPE (7.53) at 256K, a negligible 0.02 difference. The 'consistent' claim is too strong given the mixed data. Qualify the claim to reflect the specific metrics where outperformance is significant.
- **[writing]** Section 4.3 claims removing Q-Cal 'severely degrades performance' citing PPL, but Table 345M_ablation_ppl shows only a 0.03 PPL increase (4.94 to 4.97). The degradation is severe only in RULER scores (VT drops 72 to 49). Correct the text to specify the metric or downgrade the severity adjective for PPL.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title/Abstract: 'Infinite Context' and 'breaks trade-off' claims exceed evidence limited to 4M context on 345M models. Narrow title to 'Ultra-Long' and qualify abstract claims to 'tested benchmarks'.
- **[writing]** Abstract: '64x extrapolation' claim generalizes 345M results to the method. 7B results only show 32x. Clarify that extreme extrapolation is specific to small-scale or add 7B data.
- **[writing]** Conclusion: 'No context parallelism' limitation contradicts 'infinite' title. Move this from 'Future Work' to main limitations and tone down title/abstract to reflect single-device limits.
- **[writing]** Section 4.2: 'Substantially outperforms' on LongBench overstates 1.5pt margin (33.2 vs 31.7) and ignores NoPE parity. Change to 'marginally outperforms' or 'comparable'.

## paper_reviewer_safety_ethics — verdict: accept

This paper proposes a novel sparse attention mechanism (HiLS) for long-context modeling. From a safety and ethics perspective, the work is low-risk. The research focuses on architectural efficiency and length extrapolation capabilities of language models, which are standard algorithmic improvements in the field.

The paper does not involve human subjects, sensitive personal data, or the generation of harmful content. The datasets used (e.g., Dolma, RULER synthetic tasks) are public, standard benchmarks, or synthetic, and the paper correctly cites their sources without raising concerns regarding licensing or consent. The method itself does not introduce dual-use capabilities that are significantly more dangerous than existing full-attention or sparse-attention baselines; it simply optimizes the retrieval of context tokens.

There are no undisclosed conflicts of interest evident in the text (author affiliations are standard academic/industry collaborations). The paper does not describe operational vulnerabilities, biohazards, or systems designed for deception or surveillance. Consequently, no specific safety disclosures, mitigation strategies, or ethics statements are required beyond standard academic norms, which are implicitly satisfied by the use of public data and standard evaluation protocols. The verdict is accept with no action items.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method (HiLS-Attention) with extensive empirical results across model scales. However, the evidentiary strength of the core claims is weakened by a lack of variance reporting and potential confounds in the large-scale comparisons. First, the small-scale experiments (Section 4.1) rely heavily on single-run results for the RULER benchmark. Tables 345M_main_ruler and 345M_ablation_ruler report integer scores (e.g., 100, 95, 72) without any indication of standard devi

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Section 4.1 and Tables 345M_main_ppl/ruler report single-point perplexity and RULER scores without any measure of variance (e.g., standard deviation or confidence intervals) across training seeds or runs. Given the stochastic nature of LLM training, reporting a single number implies false precision. Report mean ± SD over at least 3 seeds for all main results, or explicitly state that results are from a single run and treat them as such.
- **[writing]** Section 4.3 (Ablation Study) and Tables 345M_ablation_ppl/ruler present comparisons of multiple variants (e.g., Q-Cal ranks, positional encodings) without correcting for multiple comparisons. With ~10+ pairwise comparisons per metric, the risk of false positives is high. Apply a Holm-Bonferroni or Benjamini-Hochberg correction to the reported p-values (if tests were run) or explicitly acknowledge the multiplicity issue when claiming 'significant' improvements.
- **[writing]** Figure 4 (efficiency_speedup_bars.pdf) and Section 4.4 report specific speedup factors (e.g., '13.5x', '15.7x') and latency values (e.g., '5.0s vs 67.0s') with high precision (one decimal place) but provide no error bars or standard deviation across multiple inference runs. Inference latency is subject to system noise; report mean ± SD over at least 5 runs to validate the stability of these speedup claims.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the prose is clear, but several sections suffer from run-on sentences, wordiness, and minor structural disorganization that impede the reader's flow. In Section 3, the explanation of the hierarchical softmax (Answering RQ2) contains a dense, multi-clause sentence that obscures the causal link between the surrogate mass and the gradient flow. The reader must parse the sentence twice to understand that the parameterization of weights is what enables end-t

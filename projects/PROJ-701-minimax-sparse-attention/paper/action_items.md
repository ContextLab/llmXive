# Automated-review action items — MiniMax Sparse Attention

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that MSA 'matches GQA on benchmarks' (Abstract, Intro) is contradicted by Table 2 (HELMET-128K), where MSA-CPT scores 45.93 vs. Full Attention's 46.53. The text must clarify that performance is 'comparable' or 'statistically indistinguishable' rather than 'matching,' or explicitly note the small degradation in long-context retrieval.
- **[writing]** The claim that the Index Branch 'always retaining the most recent block' (Intro) is not fully supported by the ablation in Appendix A.2 (Table: Forced Sink & Local Selection), which states that 'Removing forced sink/local selection has little effect on quality.' The text should reconcile this by noting that while the mechanism is present, the model learns to attend to local blocks naturally, making the explicit forcing less critical than claimed.
- **[writing]** The citation \citep{minimax01} in Section 5 is used to support 'Hybrid stacks... interleave linear and full-attention blocks.' However, the bib entry for minimax01 describes 'Lightning Attention' (a linear attention variant), not necessarily a hybrid stack interleaving linear and full attention. Verify if the citation accurately supports the specific claim of 'interleaving' or if a different citation (e.g., a specific hybrid model paper) is needed.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption reads 'Overview of .' with a missing model name or subject immediately following 'of', making the sentence incomplete.
- **[writing]** Figure 1: The caption contains a broken mathematical expression 'a set $$ of $k$ key blocks' where the variable defining the set size is missing between the dollar signs.
- **[science]** Figure 2: The caption claims 'four GQA groups' produce 'different long-range selection patterns,' but the four subplots (Head 0–3) show nearly identical diagonal and sink patterns with no visible differentiation in long-range behavior.
- **[writing]** Figure 2: The y-axis label 'Query Block' and x-axis label 'Key Block' are present, but the colorbar label 'Prob' is ambiguous without units or context (e.g., normalized probability? attention score?).
- **[science]** Figure 4: The title 'Capability Delta Relative to GQA Baseline' contradicts the caption 'Evaluation-score deltas relative to the Full-Attention baseline'; the baseline definition must be consistent.
- **[science]** Figure 4: The legend includes 'GQA Baseline' (dashed line), but the caption states the deltas are relative to a 'Full-Attention baseline'; the legend entry should match the caption's baseline definition.
- **[science]** Figure 5: The 'No gradient detach' (orange) curve in the LM Loss plot terminates abruptly around step 2500, while the 'Gradient detach' (teal) curve continues to step 8500. This missing data prevents a full comparison of training stability and loss convergence over the entire reported range.
- **[science]** Figure 5: The x-axis for the 'Grad Norm' plot is truncated at ~768 steps, whereas the 'LM Loss' plot extends to 10,000 steps. Since gradient spikes are the key phenomenon being illustrated, the short x-axis range makes it impossible to verify if spikes persist or recur later in training.
- **[writing]** Figure 7: The y-axis is labeled 'Value' instead of 'Entropy', which contradicts the figure title and caption.
- **[writing]** Figure 7: The legend defining the teal line (Main Branch) and the dashed red line (baseline) is missing from the plot area.
- **[writing]** Figure 8: The caption contains a grammatical error ('Evaluation results of with and without...') and fails to specify the model or method being evaluated.
- **[writing]** Figure 8: The x-axis label 'Tokens (Billion)' is ambiguous; it is unclear if this represents total training tokens, context length, or model size.
- **[writing]** Figure 9: The x-axis tick labels (512, 2048, etc.) are present only on the bottom row of plots, making the top row (Head 4, Head 5) ambiguous regarding the query positions shown.
- **[writing]** Figure 9: The top row plots (Head 4, Head 5) display only blue bars ('First token') but lack the orange bars ('Learnable sink') seen in the bottom row, which may confuse readers about whether the sink is absent or simply has zero value.
- **[writing]** Figure 11: The caption contains a grammatical error ('comparison between and a FLOP-matched...'), missing the name of the proposed method (likely 'MiniMax Sparse Attention' or 'MSA') which is only identifiable via the legend.
- **[writing]** Figure 11: The y-axis label 'Perplexity (PPL)' is redundant; 'Perplexity' is sufficient as PPL is the standard abbreviation.
- **[writing]** Figure 12: The caption 'LM loss' is insufficient; it fails to describe the comparison between 'Full Attention' and 'MSA-PT' shown in the legend or the specific training context.
- **[science]** Figure 12: The inset plot's x-axis labels (2.950, 2.975, 3.000) are illegible and lack units, making it impossible to verify the scale or the specific range of the zoomed-in region.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and hardware jargon that are not defined at their first occurrence, creating barriers for non-specialist readers. In Section 1, the term "MoE" is used to describe the model architecture without defining it as "Mixture of Experts." Similarly, Section 2.1 introduces "GQA" (Grouped-Query Attention) and "KV heads" without expanding the "KV" acronym, assuming prior knowledge of Transformer internals. In the kernel design section (Section 5), t

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The manuscript presents a coherent architecture for MiniMax Sparse Attention (MSA), but several logical gaps exist between the stated mechanisms and the derived efficiency claims. First, the central efficiency claim of a 28.4x reduction in per-token compute (Abstract, Sec 1) is not fully supported by the complexity analysis in Sec 4.3. The analysis correctly identifies the Index Branch cost as $O(N^2)$ (specifically $H_{kv} d_{idx} N^2$). At a context length of 1M, this quadratic term is signifi

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'on par with GQA' (Abstract, Sec 3) is overreaching given Table 2 shows a -0.60 point drop on HELMET-128K Overall. The authors must qualify this claim to reflect that performance is comparable on general benchmarks but slightly degraded on specific long-context retrieval metrics.
- **[writing]** The abstract states the model 'performs on par with GQA' while simultaneously claiming a 28.4x FLOP reduction. The paper does not provide a direct FLOP-normalized comparison to prove that the performance is maintained *at the same compute budget*, only at the same parameter count. This conflates efficiency with capability and overstates the efficiency gain's impact on quality.
- **[writing]** The conclusion claims the method 'preserves capabilities' at 109B scale. However, Table 2 shows a 2.40 point gain on HELMET ICL but a 0.60 point loss on Overall, and Table 1 shows mixed results (e.g., -1.35 on GSM8K in CPT). The text should avoid absolute preservation claims and instead report the specific trade-offs observed.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a technical architecture for efficient sparse attention (MSA) and reports performance on standard benchmarks. From a safety and ethics perspective, the paper does not raise immediate red flags regarding dual-use risks, data privacy, or human subject research.

**Data Privacy and Consent:**
The paper describes training on a 109B-parameter model with 3T tokens (Section 4) and continued pretraining on 140B tokens. While the specific composition of the training corpus is not detailed in the text, the authors cite standard public benchmarks (MMLU, GSM8K, RULER, etc.) for evaluation. There is no indication of the use of private, personally identifiable information (PII), or non-consensual data scraping in the methodology described. The model weights are released on Hugging Face, and the code on GitHub, which is standard practice for open research. No IRB or IACUC approval is required as the work involves computational modeling on existing datasets, not human or animal subjects.

**Dual-Use and Harm Potential:**
The proposed method (MSA) is an optimization technique for Large Language Models (LLMs) aimed at reducing computational cost and enabling longer context windows. While more efficient models can theoretically lower the barrier to deploying powerful AI systems, the paper does not introduce new capabilities for generating harmful content, bypassing safety filters, or conducting cyberattacks. The efficiency gains are architectural and apply to the inference/training process generally. The authors do not claim the model is designed for, or capable of, specific high-risk tasks (e.g., biological weapon design, autonomous weapon guidance) that would necessitate a dual-use risk assessment beyond standard LLM safety protocols.

**Transparency and Reproducibility:**
The authors provide links to the model weights (Hugging Face) and inference kernels (GitHub), facilitating external verification of the claims. The methodology, including the KL alignment loss and block selection strategy, is described with sufficient detail (Section 3, Algorithm 1) to allow for independent reproduction of the training dynamics. The ablation studies (Appendix) further support the validity of the design choices.

**Conclusion:**
The paper adheres to standard ethical norms for AI research. It does not involve human subjects, does not appear to utilize private data without consent, and the technology described does not inherently increase the risk of harm beyond the baseline risks associated with general-purpose LLMs. No action items are required regarding safety or ethics.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 28.4x FLOP reduction and 14.2x/7.6x speedups at 1M context (Abstract, Sec 6.3) lacks statistical validation. Provide standard deviations or confidence intervals across multiple runs or seeds to rule out variance from hardware noise or non-deterministic kernels.
- **[science]** The 'Full Attention' baseline in Table 2 (Sec 6.3) is not explicitly defined as a model trained with full attention from scratch or a GQA model with full attention. If the baseline is a GQA model with full attention, the comparison is valid; if it is a different architecture, the claim of 'on par' performance is confounded by architectural differences.
- **[science]** The ablation study in Table 4 (Appendix) shows mixed results for the 'No-value' variant (e.g., +0.9 on MMLU, -1.2 on GSM8K). The conclusion that the value head is 'not critical' is weak without a statistical test (e.g., paired t-test) to determine if these differences are significant or within noise.
- **[science]** The paper claims the Index Branch 'always includes the local block' (Sec 3.1) but the ablation in Table 5 (Appendix) shows 'Removing forced sink/local selection has little effect'. This contradicts the stability claim. Clarify if the 'little effect' refers to perplexity only or also to long-context retrieval, and provide evidence for the stability claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.2 and Table 1 report benchmark scores (e.g., MMLU 67.2 vs 67.0) without standard errors, confidence intervals, or p-values. Given the single-run nature of large-scale training, authors must clarify if these are single seeds or averages, and provide uncertainty estimates to support claims of statistical equivalence.
- **[science]** Table 1 and Table 2 present differences (e.g., +0.12 on RULER-128K) as definitive improvements. Without multiple independent runs or a statistical significance test, these marginal gains may be within the noise floor of the evaluation pipeline. Authors should either run multiple seeds or explicitly frame these as point estimates without claiming superiority.
- **[science]** The efficiency claims in Section 5.3 (14.2x speedup) rely on single measurements on H800. While kernel latency (Table 1) shows consistent gains, the end-to-end speedup lacks variance reporting. Authors should report the number of runs and standard deviation for the speedup metrics to ensure reproducibility.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Kernel Design), the phrase 'Programmatic Dependent Launch' appears to be a non-standard or awkward phrasing for 'Programmatic Dependent Launch' (if referring to CUDA streams) or 'Programmatic Dependency'. Verify the standard terminology for the specific CUDA feature used to avoid confusion.
- **[writing]** In the Appendix (e001), the sentence 'This suggests that the main role of O_idx in the earlier recipe was to provide an additional early training signal...' uses 'recipe' in a context that feels slightly informal for a technical paper. Consider replacing with 'methodology', 'architecture', or 'training procedure'.
- **[writing]** In Section 3 (Method), the description of the Index Branch states it 'Scores visible key tokens'. The term 'visible' is ambiguous here; does it mean 'causally visible' (i.e., past and current tokens) or 'visible to the specific query'? Clarify to ensure precise technical meaning.

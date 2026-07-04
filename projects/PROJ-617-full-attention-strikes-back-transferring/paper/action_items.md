# Automated-review action items — Full Attention Strikes Back: Transferring Full Attention into Sparse within Hundred Training Steps

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a compelling method for sparse attention, but several factual claims regarding the experimental setup and reported numbers require verification to ensure they are supported by the evidence provided. First, the experimental environment described in Section 5.1 lists "Python 3.14" and "PyTorch 2.8". These versions do not currently exist in the public software ecosystem (as of late 2025/early 2026, the latest stable versions are Python 3.12/3.13 and PyTorch 2.5/2.6). This appears

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption and chart legends contain a placeholder '.' instead of the method's name (likely 'RTPurbo' based on the legend), rendering the figure's subject undefined.
- **[science]** Figure 1: The right panel's x-axis labels (128K, 192K, 256K, 360K, 512K) do not align with the left panel's labels (32K, 64K, 128K, 256K, 512K, 1M), making direct comparison of efficiency and accuracy at specific context lengths difficult.
- **[writing]** Figure 1: The right panel's y-axis label 'Accuracy (%)' is present, but the bars are not explicitly labeled as accuracy values in the legend or caption, relying on the reader to infer the metric from the axis.
- **[writing]** Figure 2: The y-axis label 'Head Index' is ambiguous; the caption mentions 'query heads', but the axis includes indices up to 31, which may exceed the number of query heads per layer in the model, or implies a flattened index without explanation.
- **[writing]** Figure 2: The x-axis label 'Layer' and tick labels (0–47) suggest 48 layers, but the model name 'Qwen3-Coder-30B-A3B' does not clarify if this matches the actual architecture; a note on layer count or model specs would improve clarity.
- **[science]** Figure 2: No statistical context (e.g., averaging method, number of samples, or variance) is provided for the 'retrieval scores'; without this, the heatmap values lack interpretability regarding reliability or significance.
- **[writing]** Figure 3: The x-axis label 'train/global_step' is rendered as a grey text overlay on the plot area rather than a formal axis label, and the y-axis lacks a descriptive label (e.g., 'Loss').
- **[writing]** Figure 3: The plot contains a single data series but lacks a legend to explicitly identify the curve, relying solely on the caption for context.
- **[writing]** Figure 4: The caption contains a missing subject (e.g., 'Unlike baselines that collapse..., [METHOD NAME] sustains robust accuracy...'). The figure shows 'RTPurbo' in the legend, so the caption should explicitly name it.
- **[writing]** Figure 4: The right y-axis label 'Sparsity (%)' is ambiguous; the line values (94-98%) represent the percentage of tokens *kept* (or sparsity ratio), but 'Sparsity' usually implies the percentage of tokens *dropped*. Clarify if this is 'Retention Rate' or 'Sparsity'.
- **[writing]** Figure 5: The caption contains a missing subject (e.g., 'Sparse decoding speedup of [Model Name]'), making it grammatically incomplete and unclear.
- **[science]** Figure 5: The y-axis labels 'Ours (Fused)' and 'Full Attn (FA2)' are not explicitly defined in the legend; the legend only lists specific kernel components (e.g., 'D16 Score + Top-p'), requiring the reader to infer the grouping.
- **[writing]** Figure 5: The x-axis label 'Latency (µs)' is repeated for all three subplots, which is redundant and could be consolidated into a single label for the entire figure.
- **[fatal]** Figure 6: The caption reads 'Overall architecture of .' with a missing model name, and the diagram contains multiple instances of the same missing name (e.g., 'sustains robust accuracy' in Figure 4 caption context), indicating incomplete text rendering or copy-paste errors.
- **[science]** Figure 6: The 'Dynamic Top-p Selector' inset shows a cumulative curve with p=0.9 but lacks axis labels for the curve itself (e.g., what is plotted on y-axis vs x-axis beyond 'Cumulative' and 'p'), making the selection rule ambiguous.
- **[writing]** Figure 7: The caption contains a missing model name ('Overview of the hardware-aware decoding kernel in .'), likely due to a placeholder or formatting error.
- **[writing]** Figure 7: The legend items 'Sort-free top-p' and 'Bandwidth-optimized' are not explicitly defined in the caption, though their association with the red and green boxes is visually clear.
- **[science]** Figure 8: The figure displays abstract blocks labeled 'A', 'B', 'C' and a bar chart, but lacks the actual text passage or attention heatmap required to demonstrate 'semantic relatedness' or 'similar patterns' as claimed in the caption.
- **[science]** Figure 8: The orange arrows indicate a mapping from the first three blocks to the last three, but the middle section is obscured by '......', making it impossible to verify the 'long-range' or 'far away' context claim.
- **[writing]** Figure 8: The bar chart below the blocks has no axes, units, or legend to explain what the bar heights represent or the difference between orange and teal colors.
- **[writing]** Figure 9: The top panel's x-axis label 'Token position' is not aligned with the tick marks, and the top-right y-axis label 'Attn mass' lacks a clear scale or unit definition in the caption.
- **[science]** Figure 9: The red curve in the bottom-left plot is labeled 'Retrieval head' but no corresponding legend entry exists for the gray 'Uniform' line, making comparison ambiguous without external context.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 4.1 (Hardware-Aware Fast Top-p Decoding Kernel): The term 'CTA' (Compute Thread Array) is used without definition. While standard in CUDA programming, it is not universally known to all adjacent-field PhDs (e.g., those in NLP or statistics). Define it at first use: 'CTA (Compute Thread Array, the basic execution unit in CUDA)'.
- **[writing]** Section 4.1: The symbol $p_	ext{top}$ appears in the text ('cumulative attention mass reaches $p_	ext{top}$') without prior definition. The parameter is referred to as 'Top-$p$' or 'p' elsewhere (e.g., Table 1, Section 3.2). Define $p_	ext{top}$ explicitly as the cumulative probability threshold (e.g., 0.9) where it first appears in Section 4.1.
- **[writing]** Section 4.1: The term 'log-sum-exp pair $(m_b, ll_b)$' is used without defining the variables $m_b$ and $ll_b$. An adjacent-field reader may not know these represent the maximum and log-sum-exp values used in the stable softmax computation. Add a brief clause: '...reduces it to a block-level log-sum-exp pair $(m_b, ll_b)$, where $m_b$ is the block maximum and $ll_b$ is the log-sum-exp value.'
- **[writing]** Section 4.1: The term 'SM' is used ('allows the SM to maximize concurrent CTAs') without definition. In CUDA context, this stands for Streaming Multiprocessor. Define it at first use: '...allows the SM (Streaming Multiprocessor) to maximize...'
- **[writing]** Section 4.1: The term 'half2' is used ('vectorized $	exttt{half2}$ instructions') without explanation. While common in GPU optimization, it refers to a 2-element vector of 16-bit floats. A reader from a non-systems adjacent field might not know this. Add a brief gloss: '...via vectorized $	exttt{half2}$ (2-element 16-bit float vector) instructions...'
- **[writing]** Section 3.2: The term 'attention sinks' is used in the phrase 'sliding window with attention sinks' without definition. While 'streamingLLM' is cited, the concept of 'sinks' (specific tokens that attract attention to stabilize the distribution) is not explained. Add a brief parenthetical: '...sliding window with attention sinks (specific tokens that attract attention to stabilize the distribution)...'

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 5.1 claims 600 steps on 48K avg length, while Appendix A.3.2 claims 180M total tokens. With batch size 8, 600*8*48K = 230.4M, contradicting 180M. Reconcile step count, batch size, or total token count to ensure internal consistency.
- **[writing]** Abstract claims 'about 1M label tokens' and 'few hundred steps', but Appendix A.3.2 specifies '1.2M label tokens' and '600 steps'. Align the main text numbers with the appendix values or use consistent rounding to avoid minor numerical inconsistencies.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Intro claim the method 'solves' the bottleneck and is 'near-lossless' universally. Evidence is limited to two Qwen3 models on specific benchmarks. Replace 'solves' with 'mitigates' and scope 'near-lossless' to 'on evaluated Qwen3 models and benchmarks'.
- **[writing]** Intro claims RTPurbo is the 'first method' to achieve near-lossless compression with lightweight training. Evidence only covers Qwen3 models; prior work exists on other models. Qualify to 'first on Qwen3-Coder-30B-A3B' or remove 'first' to avoid overclaiming.
- **[writing]** Conclusion states 'full-attention models' generally support sparse execution, but evidence is limited to Qwen3. Limitations section admits this scope. Narrow conclusion to 'Qwen3 family studied' or explicitly acknowledge untested generalization to other architectures.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a method for sparsifying attention mechanisms in large language models to improve inference efficiency. The work relies on standard public datasets (FineWeb, Dolma 3) and evaluates performance on established public benchmarks (LongBench, RULER, MMLU-PRO). The methodology involves analyzing intrinsic model properties (attention head specialization) and applying lightweight post-hoc training (self-distillation) to existing open-weight models (Qwen3 family).

From a safety and ethics perspective, the paper does not present foreseeable, non-trivial risks of harm that are unaddressed.
1. **Data & Privacy:** The training data sources are public web corpora with no indication of personally identifiable information (PII) collection or human-subjects research requiring IRB approval. The evaluation benchmarks are standard, non-sensitive datasets.
2. **Dual-Use:** While the method improves inference efficiency (lowering cost/latency), this is a general capability improvement common to many optimization papers. It does not specifically lower the barrier to a concrete harmful capability (e.g., automated vulnerability discovery, biological synthesis, or targeted disinformation generation) in a way that requires unique mitigation beyond standard responsible AI practices. The paper does not release new models or datasets that could be directly weaponized.
3. **Bias & Fairness:** The paper reports accuracy on standard benchmarks but does not claim to solve fairness issues nor does it present results showing a new, unmitigated bias against a specific demographic group. The focus is on efficiency vs. accuracy trade-offs, which is within the scope of the reported experiments.

The paper includes a "Limitation" section (Appendix) acknowledging constraints on head specialization stability and evaluation scope. No specific safety disclosures, responsible release plans, or ethical statements are missing given the nature of the research (algorithmic optimization on public data). The work is low-risk by construction.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method for sparse attention, but the experimental design has specific gaps that prevent the evidence from fully supporting the claims of "near-lossless" accuracy and robust efficiency gains. First, the accuracy results in Tables 1, 2, and 3 are presented as single-point estimates without any measure of variance (standard deviation, confidence intervals) or seed count. In long-context benchmarks, performance can fluctuate significantly based on the specific random

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1-3 (LongBench, RULER, Reasoning) report single-point accuracy scores (e.g., '54.24%') without any measure of uncertainty (SD, SE, or CI) or mention of the number of random seeds used. In deep learning, single-run results are not statistically robust. Report mean ± SD over at least 3 seeds for all reported metrics, or explicitly state that results are from a single run and treat them as such in the text.
- **[writing]** Section 5.1 claims 'up to a 9.36× prefill speedup' and '2.01× decode speedup' based on single measurements. Speedup ratios in systems papers are highly sensitive to hardware noise and warm-up effects. Report these speedups as mean ± SD over multiple runs (e.g., 5-10 iterations) to establish statistical stability, rather than presenting a single point estimate as a definitive property.
- **[writing]** Table 2 (RULER) and Table 3 (Reasoning) compare RTPurbo against 5+ baselines across multiple sub-tasks (e.g., 10+ columns in RULER). The paper highlights 'best' results with bolding but performs no statistical significance testing (e.g., paired t-tests or bootstrap) to determine if the observed differences are real or due to random variance. At minimum, add a note acknowledging that without multiplicity correction or significance testing, the 'best' labels may reflect noise.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the prose is clear, but there are specific instances where sentence construction and structural flow impede immediate comprehension. In Section 2.2, the subsection begins with a sentence fragment ("Retrieval heads should assign high attention...") that fails to function as a complete thought, forcing the reader to wait for the next sentence to find the main verb. This breaks the momentum of the argument. Similarly, in Section 3.2, the explanation of spa

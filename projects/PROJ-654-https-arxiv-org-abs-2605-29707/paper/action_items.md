# Automated-review action items — Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In the Introduction (lines 105-108), the text claims EAGLE-3 achieves an acceptance length of 4.86 and speedup of 3.28x, while DFlash achieves 4.03 and 3.42x. However, Table 1 (main_result.tex) reports EAGLE-3 (16) on Qwen3-8B with an acceptance length of 3.27 and speedup of 2.21x, and DFlash with 6.59 and 5.21x. The values in the text do not match the primary results table, suggesting the text may be citing a different configuration or contains a factual error.
- **[writing]** The Introduction (lines 128-130) states Domino improves average acceptance length by 16.6% and speedup by 12.3% over DFlash. Calculating from Table 1 (Qwen3-8B, T=0): Acceptance length increases from 6.06 to 7.17 (~18.3%), and speedup from 4.66 to 5.49 (~17.8%). The specific percentages cited in the text do not align with the reported table data.
- **[writing]** The Abstract claims 'up to 5.8x throughput speedup under SGLang serving'. Table 2 (high_concurrency.tex) shows the maximum speedup for Domino on Qwen3-8B (GSM8K) at concurrency 2 is 5.1x. The 5.8x figure is not supported by the provided table data, which lists a maximum of 5.1x for Qwen3-8B and 4.3x for Qwen3-4B.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The bar chart on the right shows 'Accept length' for EAGLE3 (4.86) and Domino (4.70) as higher than DFlash (4.03), yet the 'Speedup' for EAGLE3 (3.28) and Domino (3.84) is lower than DFlash (3.42). This contradicts the caption's claim that speedup is evaluated on GSM8K, as higher acceptance length should generally correlate with higher speedup, suggesting a potential data labeling or calculation error.
- **[writing]** Figure 1: The legend for the left panel uses five distinct shades of blue to represent 'verify', 'draft', 'LM Head', 'DHead', and 'Tree', but the 'verify' and 'draft' bars are identical in color to the first two legend entries, while the remaining three categories are represented by progressively lighter shades that are difficult to distinguish visually, especially in the 'EAGLE3' bar where multiple small segments are present.
- **[science]** Figure 2: The legend includes 'DART' (yellow bars), but the caption only lists 'Domino, DFlash, and EAGLE-3'. The figure presents data for an unlisted method, creating a mismatch between the visual content and the description.
- **[science]** Figure 2: The x-axis labels (e.g., GSM8K, MATH) represent specific datasets, but the caption describes the figure as a general 'Speedup comparison... on Qwen3-8B' without explicitly stating that the comparison is broken down by these specific benchmarks.
- **[science]** Figure 3: The diagram shows the 'Domino Head' receiving hidden states $h_0, h_1, h_2$ as inputs to the MLPs, but the caption states the head updates causal state from 'previously sampled draft tokens' ($d_i$). The visual flow contradicts the textual description of the mechanism.
- **[writing]** Figure 3: The legend defines 'Draft token' as a gray box, but the diagram uses gray boxes for $d_0, d_1$ (inputs to the head) and $d_0, d_1, \dots, d_N$ (outputs), creating ambiguity about whether the gray boxes represent the input to the MLP or the final sampled token.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript generally maintains a high standard of technical writing, but several acronyms and specialized terms are used without definition, potentially excluding non-specialist readers or those new to the specific sub-field of speculative decoding optimization. First, in Section 5 (Methodology), under the "Training" subsection, the authors introduce the term "training-time testing (TTT)" and immediately use the acronym "TTT" in the following sentence ("We compare teacher forcing with TTT").

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 2, the claim of improving speedup from 5.21x to 7.92x on GSM8K lacks explicit mention of the Qwen3-8B model size, creating ambiguity against Table 1 which shows different values for Qwen3-4B. Specify the model size to align the text claim with the specific data point.
- **[science]** Section 5 describes training the causal GRU on ground-truth prefixes but using sampled prefixes at inference. While the 'accepted-prefix' argument is made, the logical robustness of the GRU to prefix noise during inference needs a brief mechanistic justification to fully support the causal claim of performance gains.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract claims 'up to 5.8x throughput' and intro claims 'up to 7.92x speedup on GSM8K'. Table 1 shows 8.02x on GSM8K (Qwen3-4B). Clarify if 7.92x is the max for 8B specifically or correct the global max claim to 8.02x to avoid ambiguity.
- **[writing]** The claim that Domino 'consistently outperforms' baselines ignores that DFlash is competitive on MBPP (e.g., 5.48x vs 5.59x). Acknowledge the narrow margin on code benchmarks where parallel drafting is strong to avoid overgeneralizing dominance.
- **[writing]** The claim 'adds only 56M parameters (+5.3%)' lacks the base parameter count in the text. Specify the backbone size (e.g., 'on a 1B backbone') to make the percentage verifiable without external context.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a technical optimization for Large Language Model (LLM) inference, specifically focusing on speculative decoding to reduce latency. From a safety and ethics perspective, the work does not raise immediate red flags regarding dual-use risks, data privacy, or human subject harm.

The training data utilized is the `mlabonne/open-perfectblend` dataset (Section 6, "Training Data"), which is a publicly available instruction-tuning dataset. The authors explicitly state that they regenerated responses using the target models (Qwen3-4B and Qwen3-8B) rather than using original dataset responses. This approach mitigates risks associated with propagating specific biases or errors present in the original dataset annotations, as the model learns from the target model's own distribution. No personally identifiable information (PII) or sensitive data is mentioned in the methodology or data sections.

The proposed method, "Domino," is an inference acceleration technique. While faster inference can theoretically lower the barrier for deploying powerful models in potentially harmful applications (e.g., automated disinformation generation or code exploitation), this is a general characteristic of efficiency improvements in AI rather than a specific flaw in this paper. The paper does not introduce new capabilities for generating harmful content, nor does it bypass existing safety alignment mechanisms; it merely speeds up the execution of the existing target model.

There are no indications of conflicts of interest, and the authors provide clear links to code and model weights (Abstract), ensuring transparency. The "Limitations" section (Section 7) appropriately acknowledges hardware dependencies and framework compatibility without making unsupported claims about universal applicability.

As the research focuses on system efficiency without introducing novel safety vulnerabilities or ethical dilemmas specific to the methodology, the paper is accepted from a safety and ethics standpoint.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Section 6.3.2 (Training Strategy) claims the base-anchored curriculum prevents backbone collapse, citing Figure 5. However, the text does not report the specific loss values or the magnitude of the 'collapse' observed without the curriculum. Quantitative metrics (e.g., final backbone loss with/without curriculum) are required to substantiate the claim of 'collapse' versus mere suboptimal convergence.
- **[science]** The high-concurrency throughput results in Table 3 (tab:high-concurrency-tps) show significant gains at low concurrency (2-4 requests) but diminishing returns at high concurrency (32 requests). The paper lacks a statistical analysis or error bars to determine if the observed differences at high concurrency are statistically significant or within the noise margin of GPU scheduling variance.
- **[science]** The latency breakdown in Figure 1 (fig:draft_overhead) attributes a 2.8% total latency increase to the Domino head. The text does not specify the standard deviation or variance of these latency measurements across multiple runs. Given the small magnitude of the overhead, reporting confidence intervals is necessary to rule out measurement noise as the primary driver of the reported difference.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports specific speedup and acceptance length metrics (e.g., Table 1, Section 6) but lacks any measure of statistical uncertainty (standard deviation, confidence intervals) or significance testing. Given the variability in LLM inference latency and the stochastic nature of sampling (T=1), the authors must report results over multiple seeds or provide error bars to substantiate the claimed improvements.
- **[science]** In Section 6.3 (Ablation), the comparison of training strategies (TTT vs. TF vs. TF+Curriculum) relies on single-point estimates of average acceptance length. To validate the claim that the curriculum 'prevents backbone collapse' and 'improves draft quality' beyond random fluctuation, the authors should report variance across runs or perform a statistical test (e.g., paired t-test) on the acceptance lengths.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In `latex/sec/2introduction.tex`, the sentence 'This raises a natural question: can we retain...' uses a lowercase 'c' after a colon. Standard English style (and ACL guidelines) typically requires a capitalized first word after a colon if it introduces a complete sentence or a formal question. Please capitalize 'Can'.
- **[writing]** In `latex/sec/5method.tex`, the paragraph under 'Low-Rank Correction Head' contains the phrase '...much cheaper than repeatedly applying a full LM head in an autoregressive draft loop.' The term 'draft loop' is slightly informal. Consider 'autoregressive drafting loop' or 'sequential drafting process' for better technical precision and flow.
- **[writing]** In `latex/sec/6experiment.tex`, the subsection 'Training Data' begins with 'We train the draft modules on...'. Later in the same section, the text says 'The draft models are trained on ShareGPT'. Ensure consistent terminology between 'draft modules' and 'draft models' throughout the paper to avoid confusion.

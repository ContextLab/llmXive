# Automated-review action items — From Pixels to Words -- Towards Native One-Vision Models at Scale

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.1, the claim that 'Native-RoPE' with THW-aware frequency is supported by the generic 'TransF:RoPE' citation is inaccurate. The specific decoupling mechanism is likely novel; verify if a specific prior work exists or if this requires a self-citation.
- **[writing]** In Section 4.2, the claim that NEO-ov 'surpasses' modular counterparts is slightly overstated given it underperforms InternVL3.5 on DocVQA and OCRBench. Qualify the claim to specify 'surpasses on reasoning benchmarks while matching on OCR'.
- **[writing]** The bibliography lacks full citations for benchmark papers like 'fu2025videomme' and 'li2024mvbench', listing only dataset URLs. Add full paper references to support the performance claims on these specific benchmarks.
- **[writing]** The claim of being 'fully encoder-free' in the Abstract may be ambiguous given Section 3.1 initializes weights from 'NEO', which may have used distillation. Clarify that 'encoder-free' refers to the inference architecture, not necessarily the initialization history.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The diagram depicts the 'Native Vision-Language Foundation Model' as a single monolithic block, but the caption explicitly states the backbone is 'composed of stacked native primitives.' The figure fails to visualize these primitives or the internal architecture, making it a high-level schematic rather than the detailed 'Overview' promised by the caption.
- **[science]** Figure 1: The 'Word Embedding Layer' is shown processing the text 'Take the red pill, NEO ov', but the output arrows point to the same tokens ('the', 'red', 'pill', etc.) at the top. This implies the model outputs raw text tokens directly from the embedding layer, omitting the crucial decoder/generation step described in the caption ('processed within a single decoder-only backbone').
- **[writing]** Figure 2: The text labels 'T rope index', 'H / W rope index', 'T base rope', and 'H / W rope' are rendered in a very small, low-contrast font that is difficult to read.
- **[writing]** Figure 2: The diagram for 'Native Rotary Position Embedding' contains a large amount of dense numerical data (e.g., [0,0,0], [1,0,1]) without clear axis labels or a legend explaining what these specific indices represent.
- **[writing]** Figure 3: The caption describes the stages as 'aligning Pre-Buffer', 'optimizing with diverse data', and 'instruction tuning', but the figure labels them 'Pre-Training', 'Mid-Training', and 'Supervised Fine-Tuning'. The figure labels are more standard and precise; the caption should be updated to match the figure's terminology.
- **[science]** Figure 3: The 'WEL' (Word Embedding Layer) box in Stage 1 contains an ice cube icon, while the 'PEL' (Pixel Embedding Layer) box contains a fire icon. However, the text inside the Stage 1 box says 'Pretrained Pre-Buffer, New QK' and the fire icon is placed next to 'NEO-ov'. The icons (fire/ice) are used inconsistently to denote 'frozen' vs 'active' components across the stages (e.g., in Stage 2, fire is next to NEO-ov and PEL, but ice is absent), making the visual encoding of model state (frozen
- **[science]** Figure 4: The legend labels 'Image Encoder' and 'Video Encoder' are ambiguous and do not clearly correspond to the 'VEs' (Vision Encoders) mentioned in the caption, making it difficult to distinguish which specific models are being compared against the 'Pre-Buffer'.
- **[writing]** Figure 4: The y-axis lacks a label (e.g., 'Accuracy (%)'), relying solely on the title, which is non-standard for scientific plots.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'Pre-Buffer' and 'Post-LLM' at first use in Section 3.1. These are introduced as specific architectural components without explaining their function or origin to a general reader.
- **[writing]** Define 'QK-related parameters' in Section 3.4. While experts know this refers to Query and Key projections, the term is opaque to non-specialists and should be expanded or clarified.
- **[writing]** Define 'Native-RoPE' in Section 3.1. The text mentions implementing 'Native-RoPE' but does not explicitly define what makes it 'native' compared to standard RoPE before using the term.
- **[writing]** Replace 'inductive biases' in Section 1 with 'built-in assumptions' or 'pre-existing assumptions' to improve accessibility for readers outside the deep learning subfield.
- **[writing]** Replace 'KV caching' in Section 1 with 'key-value caching' or explain the acronym, as it is a specific implementation detail not universally known to all multimodal researchers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3.1 claims the T-branch models 'cross-image relations' but Eq. 6 enforces strictly causal attention across units. Clarify how bidirectional relations emerge if cross-unit attention is unidirectional, or refine the claim to 'sequential dependency'.
- **[science]** Section 4.2 states the ablation uses 'randomly initialized' models for fair comparison, yet Section 3.1 says NEO-ov is initialized from pretrained NEO/Qwen3. If baselines are pretrained while the native model is random, the comparison conflates architecture with initialization. Clarify the initialization state of all compared models.
- **[writing]** Section 3.2 introduces a global prefix p_global for temporal cues but Section 3.1 defines RoPE indices for text tokens as h=w=0. Explain how the prefix tokens receive temporal indices to enable 'temporal localization' relative to video frames.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that NEO-ov 'surpasses' modular counterparts (Abstract, Intro) is over-claimed. Table 1 shows it trails Qwen3-VL on DocVQA (91.9 vs 96.1) and OCRBench (81.6 vs 89.6). Temper to 'competitive on' or 'surpasses on specific benchmarks'.
- **[writing]** The assertion of 'robust understanding' of structure and motion (Intro) overstates evidence. Table 3 shows NEO-ov ties or trails GeoThinker on EmbSpatial and Omni-Spatial. Qualify claims to reflect mixed results on specialist spatial tasks.
- **[writing]** The phrase 'competitive at scale' (Abstract) extrapolates beyond data. Experiments are limited to 2B/8B models. In VLM contexts, 'scale' often implies 70B+. Qualify to 'competitive at the 2B-8B scale'.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents a technically sound advancement in native vision-language modeling but requires significant expansion in its ethical disclosure to meet safety standards. The primary concern lies in the Ethical Considerations section (lines 630–638). The current text is boilerplate, stating that resources are from "open-access datasets" and risks "cannot be entirely ruled out." This is insufficient for a model trained on approximately 80 million multimodal samples (20M pre-training + 60M

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Figure 1 (compare_encoder.pdf) claims a 'fair comparison' with randomly initialized encoders but lacks statistical significance testing (e.g., p-values or confidence intervals) across multiple seeds. Given the high variance in LLM training, single-run results are insufficient to support the claim of superiority.
- **[science]** The training data composition (20M pre-training, 60M mid-training) is stated in Section 3.4, but the specific sources, filtering criteria, and deduplication methods are not detailed. Without this, the reproducibility of the 'native' signal learning and the potential for data contamination in benchmarks cannot be verified.
- **[science]** Table 1 and Table 2 report performance on numerous benchmarks, but standard deviations or error bars are missing. For claims of 'surpassing' or 'matching' modular counterparts (e.g., NEO-ov vs. Qwen3-VL on MMMU), effect sizes and variance metrics are required to distinguish signal from noise.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports extensive benchmark results (Tables 1-3) but lacks any measure of statistical significance (e.g., standard deviations, confidence intervals, or p-values) across multiple runs. Given the small margins in several comparisons (e.g., VideoMME 2B scale), the authors must report variance or perform significance testing to validate that observed gains are not due to random seed sensitivity.
- **[science]** The ablation studies (Section 5.2) rely on visual comparisons of performance curves (Figures 4-6) without statistical validation. The claim that 'Performance improves consistently' requires quantitative evidence of statistical significance (e.g., paired t-tests or bootstrap confidence intervals) to rule out noise, especially given the multi-stage training complexity.
- **[science]** The training data composition (e.g., 2:4:1:1 ratio in Mid-Training) is described as a 'unified mixture' but lacks statistical justification. The authors should clarify if this ratio was optimized via hyperparameter search or if it represents a single fixed configuration, and discuss potential sampling bias or variance introduced by this specific mixture.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the spelling error 'trainning' to 'training' in the filename 'figures/trainning_recipe.pdf' and the corresponding caption in Section 3.3 (line ~330). Consistency in terminology is essential for professional presentation.
- **[writing]** In Section 2.1 (line ~115), the phrase 'and tc.' is grammatically redundant. Since 'tc' already implies 'and others', the preceding 'and' should be removed to read '...Qwen-VL series, tc.'.
- **[writing]** In Section 3.1 (line ~215), the sentence 'The text input T is tokenized using original LLM tokenizer' lacks a definite article. It should be revised to 'using the original LLM tokenizer' for grammatical correctness.
- **[writing]** In Section 3.2 (line ~265), the phrase 'For one single image' is slightly awkward. Consider revising to 'For a single image' or 'For a single image input' to improve flow and conciseness.

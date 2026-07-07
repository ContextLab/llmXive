# Automated-review action items — DataComp-VLM: Improved Open Datasets for Vision-Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.1 claims 3.9B samples/6.0T tokens, but the 83% token share for image-caption pairs isn't verified by the text breakdown. Please add a table or sentence confirming the 3.9B/6.0T totals sum correctly with the component counts to support the 83% claim.
- **[writing]** Section 4.1 states 'English data carries almost all signal (0.6pp drop if removed)' based on Table 2 (All 49.1 vs Eng-only 48.5). However, the text also says 'Non-English tail alone is insufficient (-3.0pp)'. Clarify that the 0.6pp drop refers to removing non-English data, not English, to match the table comparison and avoid confusion.
- **[writing]** Section 5.1 claims 'only 0.29% of all training samples are removed' globally despite high rates in specific datasets (e.g., InfoVQA 100%). Confirm this 0.29% is the global average across the entire 3.9B pool, not just the subset in Figure 3, to validate the 'cheap' decontamination claim.
- **[science]** Section 6.1 states the 'Instruction-heavy mix is the worst at 1Bx6.25B', but Figure 4 shows the red line (Instruction-heavy) as the highest (best) at that point. Verify the data in Figure 4 and correct the text or figure labels to resolve this direct contradiction.
- **[writing]** Section 6.2 claims Pearson r=0.99 between pre- and post-SFT scores for 27 checkpoints. Clarify if this correlation is calculated on the 27 checkpoint averages (not 54 runs) and ensure the figure caption explicitly states the number of points used.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The legend uses 'IC' and 'IT' (e.g., '10% IC, 70% IT'), but the caption defines the mixtures using 'c' and 'i' (e.g., '10c-70i'). This inconsistency between the visual legend and the text description is confusing.
- **[writing]** Figure 2: The y-axis label 'Micro Avg (%)' is ambiguous; it is unclear if the values (e.g., 41, 42) represent raw percentages (41%) or a scaled score (e.g., 41.0 out of 100).
- **[science]** Figure 3: The caption claims the optimal configuration at medium scale is '70%IT (+2.0% over baseline)', but the chart shows the baseline (dotted line) at ~54.3% and the best point at 56.3%, which is a +2.0% absolute difference, not a relative one. However, the text says '+2.0% over baseline' which is ambiguous (could mean percentage points or relative percent). Given the context of micro avg %, it likely means percentage points, but the phrasing is slightly imprecise. More critically, the capti
- **[writing]** Figure 3: The y-axis label 'Micro Avg (%)' is present, but the tick labels on the left plot start at 41.0 and go to 43.5, while the right plot starts at 54.25 and goes to 56.25. This makes direct visual comparison between scales difficult. Consider using a shared y-axis scale or adding a note explaining the different baselines.
- **[writing]** Figure 4: The title text 'Only 3 of 39 filters show any gain — all < 1% and wash out at larger scale' contradicts the caption's claim that gains are '>= +0.5%'; the title's '< 1%' is ambiguous and potentially misleading regarding the magnitude of the positive results.
- **[writing]** Figure 4: The title text 'Small scale (1B model, 6.25B tokens)' is redundant with the caption and makes the header cluttered; this information is better placed in the caption or a subtitle.
- **[writing]** Figure 7: The caption contains a typo 'flattening ($T 2$)' which is missing the inequality symbol (likely $T \ge 2$ or $T > 1$) and does not match the x-axis label '2.0 (sqrt)'.
- **[science]** Figure 7: The orange line labeled 'T=1 baseline' extends from T=1.0 to approximately T=2.5 without data points, implying a trend that is not supported by the discrete sampling shown for the red line.
- **[science]** Figure 8: The caption claims a +13.2% gain in 'General' and +18.1% in 'Vision', but the chart shows +13.2% (68.4 vs 55.2) and +18.1% (57.2 vs 39.1) respectively. However, the caption states 'outperforms on 5 of 6 categories', but the chart shows 'Ours' trailing in 'Knowledge' (67.6 vs 68.0) and 'OCR' (54.1 vs 58.9). This is only 4 out of 6 categories where 'Ours' outperforms, contradicting the caption's claim of 5.
- **[writing]** Figure 8: The title mentions '+5.8% Micro Avg improvement', which matches the chart (58.9 vs 53.1), but the caption does not mention this specific value, creating a disconnect between the visual title and the textual description.
- **[writing]** Figure 9: The caption states 'The largest drops are on ScienceQA (-10.7%), nq (-7.6%), and ChartQA (-5.9%)', but the chart shows 'ChartQA_TEST' at -5.9% and 'nq' at -7.6%, while 'ScienceQA_VAL' is -10.7%. The caption omits the '_VAL' and '_TEST' suffixes present in the chart labels, creating a minor inconsistency in dataset naming.
- **[writing]** Figure 9: The caption text '...categories where appeared strongest' contains a missing subject (likely 'DataComp-VLM' or 'the model'), making the sentence grammatically incomplete.
- **[writing]** Figure 10: The caption ends with 'closing roughly half the remaining gap with decontaminated .' which is grammatically incomplete and missing the noun (likely 'FineVision') that the bar labels imply.
- **[science]** Figure 10: The title claims 'Upsampling OCR to 25% yields +3.1% gain', but the visual comparison between the 'Ours (standard)' bar (45.8) and the '+ OCR Upsampled 25%' bar (48.9) shows a difference of 3.1, which is correct, yet the caption text 'closing roughly half the remaining gap' is vague without explicitly stating the gap size to the FineVision baseline in the text.
- **[writing]** Figure 11: The rightmost bar chart lacks a y-axis label; the axis shows values (0.90–1.15) but does not explicitly state the unit or metric (e.g., 'Runtime multiplier' or 'Relative runtime'), relying solely on the caption for context.
- **[writing]** Figure 12: The x-axis label contains a typo ('orignal' instead of 'original').
- **[science]** Figure 12: The title claims 'no significant gain,' but the 'MTL' category shows a +1.2% gain for synthetic spatial captions, which appears to contradict the title's absolute claim without a statistical significance indicator (e.g., error bars) to justify the dismissal.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 'Extended Related Work' (Appendix) uses 'Q-formers' without definition. While 'cross-attention' is mentioned, the specific architecture component 'Q-former' (Query-former) is a named method from BLIP-2 that may not be known to all adjacent-field readers. Add a brief gloss: 'Q-formers (query-based cross-attention modules)'.
- **[writing]** Section 'Train-Test Decontamination' (Appendix) introduces 'SSCD' (self-supervised copy-detection descriptor) and 'MinHash' without expansion. While 'MinHash' is standard in NLP, 'SSCD' is specific to this pipeline. Define SSCD at first use: 'SSCD (self-supervised copy-detection descriptor)'.
- **[writing]** Section 'Train-Test Decontamination' (Appendix) uses 'Jaccard' similarity without defining the metric or the set operation (intersection over union) for a reader who might know MinHash but not the specific similarity metric used. Add: 'Jaccard similarity (intersection over union of the n-gram sets)'.
- **[writing]** Section 'Evaluation Suite Details' (Appendix) lists 'MTL' as a benchmark category without defining the acronym. In this context, it likely means 'Multilingual', but 'MTL' often stands for 'Multi-Task Learning' in adjacent fields. Define explicitly: 'MTL (Multilingual)'.
- **[writing]** Section 'Data Mixing' (Appendix) uses 'pp' as an abbreviation for 'percentage points' (e.g., '+1.1pp'). While common in economics and some ML subfields, it is often confused with 'percent' by readers from adjacent disciplines. Define at first use: 'percentage points (pp)'.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically sound and internally consistent. The central thesis—that data mixing strategies are scale-dependent and that quality filtering yields diminishing returns at scale—is supported by a coherent chain of reasoning: the authors establish a baseline, introduce controlled variables (mixtures, filters), and demonstrate that outcomes reverse or stabilize depending on model scale and token budget.

Specifically, the transition from the "Filtering rarely helps" section to the "Data Mixing" section is well-motivated. The authors correctly identify that the lack of filtering gains (Section 4) suggests the underlying mixture distribution is the primary driver of performance, leading logically to the mixing experiments in Section 5. The conclusion that "Data mixing cannot be scale agnostic" follows directly from the empirical observation in Figure 4 (and Table 2 in the appendix) where the "Instruction-heavy" mix performs worst at small scales but best at large scales. This is a valid inductive inference from the presented data.

The decontamination protocol (Appendix) is defined with precise thresholds (SSCD $\geq 0.75$, MinHash $\geq 0.55$) and the rationale for these choices (balancing precision/recall on non-natural images) is consistent with the reported removal rates. There are no contradictions between the stated methodology and the reported results (e.g., the removal rates in Figure 5 match the textual description).

Definitions of data types (image-caption, instruction-tuning, etc.) remain stable throughout the text and tables. The distinction between "Core," "Extended," and "Validation" suites is clearly defined and applied consistently in the results tables. No non-sequiturs or circular arguments were detected. The argument holds together as a valid proof of the paper's claims given the stated premises.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract/conclusion claims the method 'solves' or 'eliminates' the need for quality filtering, but Section 4 and Appendix E002 show filtering provides diminishing returns or small gains only on specific subsets (e.g., global CLIP-score on small scale). Replace absolute terms like 'solves' with 'reduces the efficacy of' or 'shows diminishing returns for' and scope the claim to the tested model scales (1B-4B) and token budgets.
- **[writing]** The paper states 'no individual quality filter provides reliable and consistent gains' (Section 2/Abstract), yet Table E003 (medium scale) shows NVIDIA Nemotron (text-only) and OpenAI-CLIP (im-cap) achieving +0.4pp to +0.6pp gains over the baseline in specific categories. The claim of 'no reliable gains' overgeneralizes the mixed results. Qualify the claim to 'no consistent gains across all data types and scales' or explicitly acknowledge the specific conditions where filters did help.
- **[science]** The conclusion implies the findings generalize to 'all VLMs' or 'any scale,' but the experiments (Section 4, Appendix E001) are restricted to Qwen2.5-based models (1B, 2B, 4B) and a specific training recipe (InternVL-style). The claim of universality is not licensed by the single-family study. Narrow the claim to 'within the Qwen2.5 family and tested scales' or add experiments on a distinct architecture (e.g., LLaVA or Flamingo-style) to support broader generalization.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a large-scale dataset curation and training study for Vision-Language Models (VLMs). From a safety and ethics perspective, the work is low-risk and well-documented.

The authors explicitly address the primary ethical concern for data-centric ML papers: **data provenance and licensing**. Section `appsub:licensing` and the extensive license table (spanning `e003`) meticulously list the source, license type (e.g., CC-BY, Apache-2.0, MIT, or "Unknown" where applicable), and access links for all 160 datasets in the pool. This transparency allows downstream users to verify compliance with their own usage constraints.

Furthermore, the paper demonstrates rigorous **decontamination practices** (Section `app:decontamination`) to prevent train-test leakage, which is a standard integrity requirement rather than a safety risk, but the detailed methodology (SSCD for images, MinHash for text) shows a commitment to scientific rigor. The exclusion of grounding benchmarks (RefCOCO variants) due to contamination risks further underscores this careful approach.

There are no indications of:
- **Human-subjects data** requiring IRB approval (the data consists of public web crawls, synthetic data, and standard academic benchmarks).
- **PII exposure** (the paper does not release raw scraped content with personal identifiers; it aggregates and filters).
- **Dual-use capabilities** that lower the barrier to specific harms (the work improves general VLM performance, a standard capability in the field, without introducing novel offensive or deceptive mechanisms).
- **Undisclosed conflicts of interest** (the authors are from a mix of academic and industry labs, but the work is presented as open research with open data/code links).

The paper adheres to the norms of the field regarding dataset construction and does not present foreseeable, non-trivial risks that are unaddressed. No action items are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a rigorous investigation into VLM data curation, particularly regarding decontamination and mixing strategies. However, the evidentiary strength of the central claims regarding data mixing and filtering is weakened by a lack of variance reporting and potential confounds in experimental design. First, the headline findings on data mixing (Section 4.2, Figure 3) and learning rate selection (Appendix, Table 1) are presented as single-run results. The reported improvements, such a

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Sections 4.2 and 5 report benchmark scores as single point estimates without uncertainty (SD/SE/CI). Report mean ± SD over ≥3 seeds for main results, or explicitly state results are from a single run to avoid implying false precision.
- **[writing]** Section 3.2 reports Pearson r=0.99 and Spearman ρ=0.99 for N=27 without confidence intervals or p-values. Add 95% CIs for these correlation coefficients to support the statistical significance of the claim.
- **[writing]** Sections 3.1 and 4.1 report specific decimal improvements (e.g., +0.6pp) without reported variance. Without SD across seeds, these decimal claims are unsupported. Round differences to integers or report variance to justify the precision.

## paper_reviewer_writing_quality — verdict: accept

The manuscript "DataComp-VLM: Improved Open Datasets for Vision-Language Models" demonstrates a high standard of writing quality. The prose is clear, concise, and allows the reader to move through the complex technical details without friction.

The structure is logical and well-signposted. The paper begins with a clear statement of contributions, followed by a detailed exposition of the data pool construction, decontamination protocols, and experimental results. Each section flows naturally into the next, with effective transitions that orient the reader to the purpose of the upcoming content. For instance, the transition from the general dataset description to the specific decontamination methodology is smooth and motivated by the need for rigorous evaluation.

Paragraphs are well-constructed, each focusing on a single main point. Topic sentences are generally clear and appear at the beginning of paragraphs, allowing the reader to quickly grasp the paragraph's intent. The authors avoid burying key claims in the middle or end of paragraphs. Sentences are grammatically correct and free of garden-path constructions or ambiguous pronoun references. The tense and voice are consistent throughout the document, maintaining a professional and objective tone.

The abstract effectively summarizes the paper's method, results, and conclusions, providing a clear roadmap for the reader. Terminology is used consistently; for example, "DCVLM" and "pool" are used uniformly to refer to the dataset and its components. The figures and tables are well-integrated into the text, with captions that are descriptive and easy to parse.

While the paper is dense with information, the writing manages this density effectively. The use of bullet points and tables helps to break up complex data and makes it more digestible. The authors also do a good job of explaining technical terms and concepts, ensuring that the paper is accessible to a broad audience within the field.

In summary, the writing quality of this paper is excellent. It is well-organized, clearly written, and free of the common readability issues that can hinder comprehension. No revisions are necessary from a writing quality perspective.

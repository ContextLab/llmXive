# Automated-review action items — ResearchStudio-Reel: Automate the Last Mile of Research from Paper to Poster, Video, and Blog

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** The paper makes several central claims regarding the performance of ResearchStudio-Reel against state-of-the-art baselines. However, the evidence provided in the text and tables fails to support these claims due to the citation of non-existent models. Specifically, Section 5 ("Experiments") and Table 1 list "GPT-5.5", "Gemini-3.1 Pro", and "Claude-4.8 Opus" as single-shot baselines. As of the current date, these model versions do not exist in the public record (the latest public versions are GPT

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The legend defines 'Skills' as light blue boxes, but the 'Paper2Assets' box is light blue while the subsequent 'Paper2Poster', 'Paper2Video', and 'Paper2Blog' boxes are white, contradicting the legend's implication that they are all skills.
- **[writing]** Figure 2: The 'Reusable Assets' box contains a 'JPEG' icon, but the caption does not explicitly list 'figures/logos' as part of the bundle, creating a minor disconnect between the visual detail and the textual description.
- **[writing]** Figure 3: The 'Staged-fill loop' legend uses color-coded labels (OVERFLOW, SPILLAGE, etc.) that are not visually represented in the diagram's flowchart elements, creating a disconnect between the legend and the process visualization.
- **[science]** Figure 3: The 'Staged-fill loop' diagram depicts a feedback cycle but lacks explicit iteration counters or stopping criteria visualization, making it difficult to verify the 'bounded ~12 rounds' claim mentioned in the caption.
- **[writing]** Figure 4: The caption defines the color coding for the debug overlay (red/amber for EMPTY/SPARSE, green for FULL, orange/magenta for SPILLAGE/OVERFLOW), but the rendered image lacks a visible legend or key to map these colors to their specific verdicts.
- **[writing]** Figure 4: The fill percentage annotations on the debug boxes are extremely small and illegible in the rendered image, making it impossible to verify the '90--98%' claim mentioned in the caption.
- **[writing]** Figure 5: The 'Pace narration' box lists 'target duration' and 'section ids' as inputs, but the caption states the skill 'plans narration and duration,' creating ambiguity on whether these are user inputs or internal outputs.
- **[writing]** Figure 5: The 'Run pipeline ppt-master' box contains a small attribution 'by Hugo He' that is not mentioned in the caption and appears to be a watermark or credit rather than a functional diagram element.
- **[science]** Figure 8: The 'Typography gate' annotation points to a specific paragraph in the English document, but the text is not 'balanced' (it is a standard left-aligned block); the visual evidence does not support the claim of 'balanced article lines' or the specific location of the check.
- **[science]** Figure 8: The 'Figure-fit gate' annotation points to a diagram in the English document, but the diagram is clearly cropped and cut off at the bottom edge of the page, contradicting the claim that the figure is 'sized to the flow'.
- **[science]** Figure 8: The 'Pagination gate' annotation points to the bottom of the English page, but the text ends abruptly in the middle of a sentence ('...making global relationships easier to model while keeping the computation highly parallel and scalable.'), indicating a pagination error rather than a successful check.
- **[writing]** Figure 8: The annotations on the left (e.g., 'Typography gate', 'Figure-fit gate') are not defined in the figure caption or the image itself; the viewer must infer their meaning from the text below them, which is not a standard or clear way to present a 'showcase' of checks.
- **[writing]** Figure 8: The Chinese document (right) has no corresponding annotations or checks shown, making it impossible to verify if the same layout checks were applied to it, despite the caption stating 'the two required Word deliverables' are shown together with the checks.
- **[science]** Figure 10: The caption claims this is a 'Qualitative ablation study' varying 'harness and base model', but the image displays a scientific poster titled 'Butterfly Effects of SGD Noise' (a different paper entirely). The visual content does not match the caption's description of the study or the artifacts being compared.
- **[science]** Figure 10: The caption references a 'Codex panel' and a 'max reasoning' panel, but the image contains no such labels or text annotations to identify these specific variants.
- **[science]** Figure 11: The caption claims to show 'Paper2Poster Tool paper2poster' and 'PosterGen postergen' baselines in the center, but the rendered image displays a single large poster with no visible baselines or comparison panels.
- **[writing]** Figure 11: The caption lists specific baselines (Paper2Poster Tool, PosterGen, P2P, and three LLMs) that are not visually present or labeled in the rendered image, making the comparison claim unverifiable.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 (Introduction) and Abstract use 'VLM' (Vision-Language Model) without expansion. While common in ML, an adjacent-field PhD (e.g., NLP or Systems) might not assume this acronym is universal. Define at first use: 'vision-language model (VLM)'.
- **[writing]** Section 3.2 (Paper2Poster) introduces the symbol `fullRatio` in the equation `fullRatio = h_content / h_card` without explicitly defining the sets or units for `h_content` and `h_card` (e.g., 'where h_content is the rendered content height in CSS pixels'). Add a brief clause defining these terms.
- **[writing]** Section 3.2 (Paper2Poster) uses the term 'OMML' (Office Math Markup Language) when describing the conversion of MathJax equations to PowerPoint. This is a specific Microsoft standard not known outside the Office ecosystem. Expand to 'Office Math Markup Language (OMML)' at first use.
- **[writing]** Section 3.2 (Paper2Poster) and Section 3.3 (Paper2Video) refer to 'ppt-master' as a workflow dependency. While a citation is provided, the term is used as a proper noun without a brief gloss of what it is (e.g., 'an AI-driven slide generation skill'). Add a one-clause definition.
- **[writing]** Section 3.2 (Paper2Poster) uses the phrase 'Scan-to-Read block' as a specific UI component name. While descriptive, it is introduced as a defined term without prior context. Ensure it is clear this is a specific named block in the poster layout, perhaps by adding 'the Scan-to-Read block (a QR code section)' on first mention.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically sound and internally consistent. The central thesis—that a composition of five skills sharing a single upstream extractor (Paper2Assets) solves the problems of isolated extraction (G1), one-way renders (G2), and soft quality gates (G3)—is supported by a coherent chain of reasoning throughout the text.

The definitions of the five skills (Paper2Assets, Paper2Poster, Paper2Video, Paper2Blog, Paper2Reel) are established in Section 3 and used consistently in the Experiments (Section 5) and Applications (Section 6). The causal claims regarding the "measured-fill loop" improving aesthetics are supported by the ablation study in Section 5, which explicitly isolates the loop's contribution by holding the model fixed while changing the harness. The results in Table 1 align with the textual claims: the text states the method leads on aesthetics and information sub-criteria, and the table data confirms this with bolded/underlined values for the ResearchStudio-Reel rows.

There are no contradictions between sections. The Limitations section (Appendix A) honestly addresses the gap to human posters (generative vs. compositional) and the proxy-bound nature of the evaluation, which is consistent with the Future Work section and does not undermine the main claims. The distinction between the "Claude Code" and "Codex" settings is maintained consistently in the text and tables. The numerical values in the pipeline breakdown table (Table 2) sum correctly to the reported totals, and the cost analysis logic (cached vs. fresh tokens) is applied consistently.

The argument that the system is the "only pipeline to ship all three editable artifacts" is supported by the capability audits in Tables 3 and 4, which clearly mark prior systems with 'x' for missing capabilities while marking the proposed system with checkmarks. The logical flow from problem definition to architectural solution to empirical validation is tight, with no non-sequiturs or unsupported leaps in the reasoning.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Conclusion claim 'surpasses authors' own' with specific margin (3.52 vs 2.94), but Table 1 shows 3.33 vs 3.02. The text in Sec 5 contradicts the table. Align the abstract's numerical claim with the table's reported means to avoid misrepresenting the evidence.
- **[writing]** Abstract claims the system is 'the only pipeline to ship all three editable artifacts.' This implies a universal fact, but capability audits (Tables 2-3) only compare against a curated subset of baselines. Scope the claim to 'among systems evaluated here' or 'to our knowledge' to match the evidence.
- **[writing]** Conclusion states 'any dissemination target... fits the same composition' as a fact. The paper only validates this on three artifact types. Rephrase as a hypothesis (e.g., 'We hypothesize this pattern extends to...') to avoid overgeneralizing beyond the demonstrated scope.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a system for automating the creation of research dissemination artifacts (posters, videos, blogs) from academic papers. This is a low-risk application domain. The system processes user-provided PDFs or LaTeX sources and generates editable outputs; it does not involve scraping private data, training on non-consensual human datasets, or generating content designed to deceive, surveil, or cause physical harm.

The authors have included a dedicated "Ethics" appendix (Section app:ethics) that appropriately addresses the primary risks associated with this work:
1.  **Provenance and Disclosure:** The paper explicitly recommends preserving metadata to disclose AI involvement, acknowledging that generated artifacts could otherwise be mistaken for human-made work.
2.  **Licensing:** The authors correctly note that figure copyright follows the source paper's license and that institution logos are fetched from public sources (Wikimedia/Wikidata) under their respective licenses. They clarify that the system does not redistribute third-party content but rather processes user-provided inputs.
3.  **Hallucination/Factual Consistency:** The "Limitations" section (app:limit) and the system design (shared evidence map, hard gates) address the risk of factual drift or hallucination, which is the primary safety concern for automated summarization systems.

There are no indications of dual-use capabilities (e.g., generating disinformation at scale, impersonating specific individuals without consent, or creating deepfakes of real people). The "video" component uses text-to-speech and slide animations, not generative video of human faces. The "blog" component produces text in Word format, not deceptive social media content.

No human-subjects data, PII, or sensitive datasets are used or released. The evaluation relies on a public benchmark (Paper2Poster) and the authors' own generated outputs. The paper does not require an IRB statement as no human subjects were recruited or observed.

The risk profile is minimal, and the authors have provided adequate disclosure regarding the limitations and ethical considerations of their system. No action items are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 claims ResearchStudio-Reel beats author ground-truth on aesthetics (3.52 vs 2.94) with no reported variance or seed count. A single run per paper cannot distinguish a real effect from seed noise or VLM idiosyncrasy. Report results across 3-5 seeds with mean ± SD or bootstrap CIs to confirm stability. (science)
- **[science]** Section 5.1 attributes the ~0.76 aesthetic gain to the 'measured-fill loop' by comparing single-shot vs. pipeline. However, the pipeline also uses multi-turn tool use while the baseline is static. This confounds the loop with the agent harness. Add a control with tool use but no iterative loop to isolate the loop's specific contribution. (science)
- **[science]** The claim of 'surpassing authors' relies solely on VLM judges, which may bias towards the system's consistent layout over human bespoke designs. Include a small human evaluation (n=20-30) blind to source to verify VLM scores correlate with expert human preference before claiming superiority. (science)

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 reports mean scores (e.g., 3.33, 4.00) for 100 papers but omits uncertainty measures (SD, SE, or 95% CI). Report mean ± SD or 95% CIs for all quality metrics in Table 1 and the Appendix to allow assessment of stability.
- **[writing]** The abstract and Section 5 claim the method is 'significantly better' without reporting a formal hypothesis test (e.g., paired t-test) or p-values. Either run paired tests on the 100 paper scores and report p-values, or rephrase claims to 'higher mean score' without invoking statistical significance.
- **[writing]** Table 1 compares 7 systems across 8 metrics (56 comparisons) and highlights 'best' values without multiple-comparison correction (e.g., Bonferroni or FDR). Apply a correction method to pairwise comparisons or explicitly state that 'best' labels are uncorrected and may include chance findings.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the narrative flow is strong, but several sentences are overly long and complex, forcing the reader to re-parse them to recover the intended meaning. The abstract contains a grammatical error and a run-on sentence that obscures the contrast between prior work and the proposed method. In Section 3.1, the description of the figure-cleanup chain is a single, dense run-on sentence that lists multiple steps without clear breaks; splitting this would improve

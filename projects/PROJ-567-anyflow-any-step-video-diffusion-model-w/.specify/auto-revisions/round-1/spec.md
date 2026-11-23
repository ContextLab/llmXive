# Revision Specification: Paper Science Revision — PROJ-567-anyflow-any-step-video-diffusion-model-w round 1

**Generated**: 2026-06-21T09:55:41.359541+00:00
**Kind**: paper_science
**Project**: PROJ-567-anyflow-any-step-video-diffusion-model-w
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[2168843c4583] (severity: writing)** Clarify the 'first' claim in Abstract/Intro to account for concurrent work TMD (Section 2) which also studies flow map distillation for video, distinguishing the specific 'backward simulation' novelty.
- **[60b85e2ab97c] (severity: writing)** Code artifacts are not provided for review. The paper claims code is released at https://github.com/NVLabs/AnyFlow but no repository or implementation files are available in the review package. This prevents evaluation of code quality, reproducibility, and implementation fidelity to the described method.
- **[368b909ec438] (severity: writing)** Explicitly state the software and model weight license (e.g., MIT, Apache 2.0) in the Abstract or Conclusion. Currently, the GitHub link is provided without legal terms (Abstract, line 28).
- **[071fead716d0] (severity: writing)** Provide a specific commit hash or version tag for the released code repository to ensure reproducibility. The GitHub URL lacks a pinned version (Author info, line 12).
- **[4ac0e48abda2] (severity: writing)** Clarify the licensing constraints of the synthetic training data derived from Wan2.1-T2V-14B. The base model's license dictates permissible use of generated data (Sec 5.1, Implementation Details).
- **[d7c93533994a] (severity: writing)** Replace nimategraphics dependencies with static representative frames in figures like fig:teaser and fig:ablation_onpolicy to ensure qualitative claims are visible in non-interactive PDF viewers.
- **[3034422aed2d] (severity: writing)** Move the embedded table in fig:ablation_time_sampler (lines ~1050-1070) to a standalone table environment to prevent numbering conflicts and improve accessibility.
- **[e5b51fb3a659] (severity: writing)** Add alt text metadata to all figure environments (e.g., lttext{...}) to support screen readers and accessibility compliance.
- **[bc2b0e4560dc] (severity: writing)** Verify axis labels and tick marks in quantitative charts (e.g., fig:teaser, fig:ablation_interpolated_embedding) are legible at standard print resolution (300 DPI) and grayscale.
- **[8eda274556c4] (severity: writing)** Define "NFEs" at first use in Abstract (line 3) as "Number of Function Evaluations" for non-specialists. The term still appears multiple times without definition.
- **[0a005fd9fadc] (severity: writing)** Define "KV-cache", "patchify kernels", "context compression", and "teacher-forcing" in Section 4.3 (AnyFlow for Causal Video Diffusion) where they appear without explanation. These remain undefined in the current revision.
- **[ab06658d6d9e] (severity: writing)** Define "LoRA" in Section 5.1 (Implementation Details) as "Low-Rank Adaptation" at first mention. The acronym appears with only a citation, no plain-text definition.
- **[c220e1184abb] (severity: writing)** Define acronyms "FAR" and "rCM" in text rather than relying solely on citations (e.g., Abstract, Section 1, Section 2). Both remain undefined despite prior flagging.
- **[20dc797850df] (severity: writing)** Replace "rollout" with "sampling sequence" or "generation path" in Sections 1, 4, and 5 to improve accessibility. The term "rollout" still appears throughout without substitution.
- **[1577b5b8ba16] (severity: writing)** Simplify compound terms like "guidance-fused training", "adaptive loss reweighting", and "differential derivation equation" in Section 4.1 with brief parenthetical explanations. These remain unexplained technical compounds.
- **[cba63584ca0b] (severity: writing)** Clarify the tested range for 'any-step' claims. The Abstract and Introduction assert support for 'arbitrary inference budgets,' but tables only show 4 and 32 NFEs. Include intermediate steps or qualify the claim.
- **[52831b67ad03] (severity: science)** Provide quantitative metrics for downstream fine-tuning. The claim about continued training adaptability in sections/4_method.tex relies only on qualitative figures (figures/downstream_results.tex). Add VBench scores for fine-tuned models.
- **[1eb883f873de] (severity: science)** Strengthen baseline degradation evidence. The claim that consistency models degrade at higher NFEs (sections/1_introduction.tex) relies on ablation tables (tables/ablation_anyflow.tex). Include multi-step results for main baselines (rCM, Krea) in tables/t2v_comparison.tex.
- **[1804ce72a685] (severity: writing)** Add a dedicated Ethics Statement section discussing potential misuse (e.g., deepfakes, disinformation) and mitigation strategies (e.g., watermarking).
- **[bc1a7ff8a5d4] (severity: writing)** Clarify data provenance regarding the base Wan2.1 model and synthetic dataset generation to address copyright and consent concerns.
- **[c0a9840d7ed2] (severity: writing)** Discuss limitations of the VBench evaluation in assessing fairness, bias, or safety metrics beyond quality and semantic alignment.
- **[dd965d3a3e0f] (severity: science)** Specify the exact number of evaluation prompts/samples used for VBench metrics to assess statistical reliability.
- **[1e970e0c5675] (severity: science)** Provide error bars or variance across random seeds for key quantitative results (e.g., Table 4) to support small effect sizes.
- **[dfaa1e216ede] (severity: science)** Clarify if baseline results taken from original papers used identical evaluation protocols to the re-evaluated models to ensure fair comparison.
- **[f9ef72563b0d] (severity: science)** Main quantitative results (e.g., Tab. tab:t2v_comparison) report point estimates without standard deviations or confidence intervals. Margins are small (e.g., 84.04 vs 83.73), requiring statistical significance testing.
- **[a17ed0288712] (severity: science)** Evaluation protocol in Sec. 5.2 lacks details on the number of random seeds or prompts used to compute VBench scores. Variance estimation requires this information.
- **[7853de3b00cb] (severity: writing)** Multiple baseline comparisons are made across tasks and scales without addressing multiple-comparisons correction or controlling for Type I error inflation.
- **[fb3ed10b55eb] (severity: writing)** Move the abstract environment inside the document body (i.e., after \maketitle). Currently the abstract is input before \begin{document}, which breaks the standard LaTeX article structure.
- **[f07f27544be7] (severity: writing)** Ensure a consistent heading hierarchy: all top‑level sections use \section, subsections use \subsection, and subsubsections use \subsubsection. Verify that no \section* is used where a numbered section is expected (e.g., the Acknowledgments macro should be \section* if unnumbered, but its placement should follow the main sections).
- **[4b1773c32e9e] (severity: writing)** Standardize figure placement specifiers. Several figures use [!tb] while others use [!tb] inconsistently; consider using a uniform placement option (e.g., [htbp]) and ensure that \caption appears before \label for better cross‑referencing.
- **[261fcd5a5695] (severity: writing)** Remove duplicate package imports (e.g., \usepackage{booktabs} appears twice in preamble.tex). Duplicate imports can cause warnings and increase compilation time.
- **[2484afdaf82d] (severity: writing)** Check that all cross‑references use the same macro (e.g., \cref) and that the corresponding \crefname definitions in preamble.tex match the referenced object types (sections, tables, figures, algorithms). Inconsistent naming can lead to incorrect reference text.
- **[0d4a660d3cb8] (severity: writing)** In Section 1, reduce repetition of the phrase 'at 4 NFEs' which appears three times in close proximity within the results summary paragraph. Vary phrasing to improve readability.
- **[048a57ad625a] (severity: writing)** Fix hard line breaks in source files that split sentences or section titles (e.g., 'Differential Derivation
Equation' in Section 3, 'with
a flow map' in Section 2).
- **[4c8f6ea91053] (severity: writing)** Split the long sentence in the Abstract (lines 10-15) describing extensive experiments into two sentences to reduce cognitive load for readers.
- **[50f661487821] (severity: writing)** Remove double space before 'simulation' in Table 6 caption (tables/training_cost.tex).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 36 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

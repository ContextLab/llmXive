# Revision Specification: Paper Science Revision — PROJ-751-moebius-0-2b-lightweight-image-inpaintin round 2

**Generated**: 2026-06-28T12:54:32.837360+00:00
**Kind**: paper_science
**Project**: PROJ-751-moebius-0-2b-lightweight-image-inpaintin
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[c3cf6a18e771] (severity: science)** Multiple critical citations are missing from main.bib (e.g., xie2024sana, xie2025sana for Mix-FFN; jordan2024muon for optimizer). Claims regarding method components cannot be verified without these sources.
- **[aa407ebb8f84] (severity: writing)** Related work citations for Knowledge Distillation and Efficient Architectures (e.g., li2014KLDNN, romero2015fitnet, qin2024mobilenetv4) are absent from the bibliography, undermining the factual support for the literature review.
- **[117dcb4c554e] (severity: writing)** The GitHub URL in the 'Code Availability' section is a placeholder ([username]) and must be replaced with the actual repository link before publication.
- **[d27aae89a340] (severity: science)** The manuscript claims code availability but does not provide the actual code artifacts for review. Ensure the repository includes training scripts, evaluation pipelines, and data preprocessing code.
- **[244a9fa8cbbe] (severity: writing)** Dependency versions (e.g., PyTorch, CUDA, diffusers) are not specified in the text or supplementary material, hindering reproducibility.
- **[57c67b598e9a] (severity: writing)** The GitHub repository URL in the Code Availability section is a placeholder ([username]). This prevents verification of the data preprocessing pipeline and mask generation scripts.
- **[0aaa197e20f3] (severity: writing)** The license for the trained model weights is not explicitly stated, despite the use of CC BY-NC 4.0 datasets. Clarify compatibility to ensure legal compliance for downstream users.
- **[01b172ddaa0a] (severity: writing)** The supplementary material containing the data preprocessing JSON schema is referenced but not provided. Confirm its availability to validate the data split and mask generation claims.
- **[0a9e1dbe1520] (severity: writing)** Several figures (e.g., Fig. 4, Fig. 5, Fig. 6, Fig. 7, Fig. 8, Fig. 9) lack clear axis labels, units, or legends; add descriptive axis titles and units where applicable (e.g., latency in ms, FID/LPIPS values) and include a legend for color‑coded series.
- **[21b25a817c3d] (severity: writing)** The current color palette (red/green contrasts) may be problematic for readers with color‑vision deficiencies; replace with a color‑blind‑friendly palette (e.g., teal/orange) and ensure sufficient contrast for printed grayscale.
- **[374c9c64a85f] (severity: writing)** Captions are sometimes placed after the \label command or missing the required \label; ensure every \includegraphics is immediately followed by \caption and then \label, as mandated by the style guidelines.
- **[864e26dba1f6] (severity: writing)** Add concise alt‑text descriptions for all raster figures (e.g., qualitative comparisons, user‑study bar charts) using the \includegraphics[alt={...}] option to improve PDF accessibility.
- **[dfe74f5b8f47] (severity: writing)** For multi‑panel figures (Fig. 2 and Fig. 3), provide sub‑figure labels (a), (b), … and reference them in the caption to aid readability.
- **[086256cc1b8e] (severity: writing)** Verify that all figures are vector PDFs (not rasterized images) to maintain legibility at any print scale; re‑export any bitmap‑based figures at ≥300 dpi or convert to vector format.
- **[a54367eb544f] (severity: writing)** Define acronyms at first textual use rather than relying solely on preamble commands (e.g., GLA, LCG, SOTA).
- **[d8172170ab5e] (severity: writing)** Replace buzzwords like 'synergistically pair' and 'optimal synergy' with precise technical descriptions.
- **[8c96cde03f35] (severity: writing)** Clarify specialized terms like 'Muon optimizer' and 'Hadamard product' for non-specialist accessibility.
- **[1281e5585660] (severity: science)** Clarify the discrepancy between FID 26.43 (Ablation Exp 9, 18K iters) and FID 9.48 (Main Results, 138K iters) on Places2 Test. The text in Sec 3.2.3 implies Exp 9 represents the 'fully equipped optimization scheme', but the table caption specifies an intermediate checkpoint. This conflates architectural contribution with training duration.
- **[4bf1f1323e0e] (severity: writing)** Address the logical inconsistency of listing 'qwen.qwen3.5-122b' as an author. An LLM cannot hold authorship; this undermines the paper's provenance and ethical standing.
- **[990106fd0810] (severity: writing)** Correct the claim in the Data-Privacy Impact Assessment that weight decay and gradient clipping constitute 'differential privacy-aware regularization'. These are standard regularization techniques, not DP mechanisms.
- **[3d10d5d020ae] (severity: writing)** Revise the Supplementary claim that Moebius 'surpasses its teacher model' to align with the quantitative tables and user study data where the Teacher consistently outperforms Moebius.
- **[bc62c8303031] (severity: writing)** Replace the absolute term 'flawless object removal' in Section 4.4 with more measured language that acknowledges the limitations described in the Failure Case Analysis.
- **[30ef12b3087f] (severity: writing)** Update the Code Availability section to provide a valid, accessible repository URL instead of the placeholder '[username]'.
- **[88f87dd3a2aa] (severity: writing)** Authorship listing includes 'qwen.qwen3.5-122b' which appears to be an AI model name, not a human author. This raises ethical concerns about proper attribution and accountability. Please clarify the role of this entity and ensure all authors meet standard authorship criteria per publication guidelines.
- **[326293f711a8] (severity: science)** User study (Sec. 4.3) involved 22 participants but lacks IRB approval documentation or informed consent procedures. For research involving human subjects, institutional review board approval and documented consent processes are required. Please add this information to the manuscript.
- **[69d4d94b7911] (severity: writing)** Dataset consent for CelebA-HQ and FFHQ is not adequately addressed. These datasets contain faces of real individuals where consent for AI training is debated. Please expand the Data Availability section to discuss how consent concerns were handled and whether dataset licenses permit the claimed use cases.
- **[ec8a61952060] (severity: writing)** Dual-use risks (deepfakes, evidence tampering, watermark removal) are mentioned only briefly in the Responsible Deployment section. Given the technology's potential for harm, please expand this discussion with specific mitigation strategies and acknowledge limitations of proposed safeguards.
- **[3ddf36d038aa] (severity: science)** Differential privacy claims in the Data-Privacy Impact Assessment are vague. Please specify the privacy budget (epsilon), mechanisms used, and provide evidence that these measures actually reduce memorization risks rather than just mentioning weight decay and gradient clipping.
- **[ca3bde4e0f52] (severity: science)** The 'Code Availability' section lists a placeholder URL 'https://github.com/[username]/Moebius'. Replace with the actual repository link to ensure reproducibility of the scientific claims.
- **[df8feba31173] (severity: science)** The User Study (Sec. 4.3, Fig. 5) reports preference percentages (31.76% vs 32.18%) without explicit statistical significance testing (e.g., binomial test p-values) in the main text. Add significance tests to support the claim of 'matching' performance.
- **[59c2dd4e4a69] (severity: science)** Correct the statistical significance paragraph in Supplementary Materials; reported FID values (12.3) do not match OOD table (17.81) or main tables.
- **[00cc1c54bae9] (severity: science)** Report confidence intervals or standard deviations for all main benchmark results (FID/LPIPS) across multiple seeds.
- **[d0564cab6ebd] (severity: science)** Include statistical significance tests (e.g., t-test, bootstrap) for User Study preference percentages.
- **[3e9a7152b07e] (severity: writing)** Replace placeholder code link with actual repository URL for reproducibility.
- **[5ea938f605fb] (severity: writing)** Title block placement is incorrect: title appears after Data-Privacy Impact Assessment section. Move title block before any sections per LaTeX document structure requirements.
- **[6ddea1f4c02e] (severity: writing)** Table column specifications use non-standard >{hspace{2pt}}c<{hspace{2pt}} syntax. Preamble comment explicitly recommends standard c/l/r specs for compiler compatibility.
- **[4cbebbae7d94] (severity: writing)** Multiple label commands placed incorrectly after end{figure} instead of after caption. Labels should immediately follow captions for proper cross-referencing.
- **[ba024a5bdcd5] (severity: writing)** Duplicate consecutive vspace commands throughout. Consolidate to single spacing command.
- **[1e0a22e4ec0e] (severity: writing)** Table label contains space: tab: abla_CFG. Label names should not contain spaces for reliable cross-referencing.
- **[414c2099bd3f] (severity: writing)** Bibliography file main.bib is truncated/incomplete. All cited references must be present for compilation.
- **[cb7cdf84060e] (severity: writing)** Excessive commented-out code blocks throughout. Clean up to avoid confusion and potential compilation conflicts.
- **[4c02b5259d15] (severity: writing)** Fix the misplaced \label{sec:experiments} in Section 4 (line ~330). It is currently inside a paragraph text rather than attached to a section command, which breaks cross-referencing.
- **[7794dad29a15] (severity: writing)** Standardize capitalization for '10B-level' vs '10B-Level' throughout the manuscript (e.g., Abstract vs. Introduction) for consistency.
- **[d5364bb4e648] (severity: writing)** Correct 'ie.' to 'i.e.' in Section 3.2.1 (line ~235) to adhere to standard academic formatting.
- **[302162205c4c] (severity: writing)** Standardize table label naming conventions (e.g., 'tab:abla_distill' vs 'tab: abla_distill') to ensure consistent LaTeX compilation and referencing.
- **[86dcc809cbd1] (severity: writing)** Break down overly long sentences in the Abstract and Introduction (e.g., lines 10-15) to improve readability and flow.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 46 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

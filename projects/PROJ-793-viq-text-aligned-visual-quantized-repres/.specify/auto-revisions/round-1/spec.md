# Revision Specification: Paper Science Revision — PROJ-793-viq-text-aligned-visual-quantized-repres round 1

**Generated**: 2026-06-27T16:47:08.211945+00:00
**Kind**: paper_science
**Project**: PROJ-793-viq-text-aligned-visual-quantized-repres
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[64791cae3a28] (severity: writing)** Abstract and Introduction claim ViQ ranks 'first among mainstream discrete visual autoencoders' on rFID (0.62). Table 2 shows UniTok achieves 0.37 (lower is better), making ViQ second. Correct this claim to reflect the actual ranking.
- **[5b0a9b64666c] (severity: writing)** Section 4.1 Results claims ViQ 'trails some continuous encoders with fewer parameters' on OCRBench. Table 1 shows ViQ (1.3B) scores 636.0 vs SigLIP2-g (1.1B) 590.0. ViQ outperforms the smaller continuous encoder. Revise text to match data.
- **[1e9b5065c135] (severity: writing)** Multiple citation keys (e.g., zhao2025qlip, mentzerfinite, tschannen2025siglip) are missing from the provided main.bib snippet. Verify the full bibliography includes all cited works to ensure reproducibility.
- **[2d369a79efcf] (severity: writing)** Code artifacts (scripts, models, configs) are not included in the submission package. Please include a `requirements.txt` or `environment.yml` in the supplementary material to verify dependency hygiene.
- **[6e6aebfba05e] (severity: writing)** The GitHub link in the Abstract (sec/0-Abstract.tex) should be verified to contain the exact commit hash used for the reported results to ensure reproducibility from scratch.
- **[070ddfecf115] (severity: writing)** Dataset provenance is incomplete: specify exact versions/commits for LLaVA-OneVision and other training datasets used in Sec 4.1 and Appendix A.
- **[d6f086881881] (severity: writing)** Artifact license missing: explicitly state the license (e.g., MIT, Apache 2.0) for the code and model weights linked in sec/0-Abstract.tex.
- **[31d1f9c0c20d] (severity: writing)** Link rot risk: replace blog URLs in main.bib with arXiv IDs or DOIs where available to ensure long-term accessibility.
- **[1287257e8298] (severity: writing)** Data cleaning undocumented: describe procedures for handling missing data or corrupted images in the training pipelines.
- **[4fad494b3314] (severity: writing)** Caption for fig:supp_vis (Appendix) is ambiguous ('Left or above'). Specify exact layout (e.g., 'Top: Original, Bottom: Reconstructed') for clarity.
- **[95ca680ec839] (severity: writing)** Remove manual \vspace{-5pt} in fig:teaser to prevent potential overlap in different print layouts; rely on standard float spacing.
- **[4e16acc62abf] (severity: writing)** Ensure fig:acceleration includes explicit axis units (e.g., 'Time (s)') in the rendered image, as caption implies quantitative comparison.
- **[881776733bf9] (severity: writing)** Define acronyms SFT, VLM, LoRA, MHSA, ViT, BF16, and AdamW at first use.
- **[093155ee788e] (severity: writing)** Clarify 'BN' in Eq 3 to avoid confusion with Batch Normalization.
- **[b0fb538db94d] (severity: writing)** Define metrics PSNR, rFID, and SSIM in text or caption.
- **[0ad16f021fee] (severity: writing)** Correct the Abstract claim regarding reconstruction ranking. It states ViQ ranks 'first among mainstream discrete visual autoencoders,' but Table 2 shows UniTok outperforms ViQ in PSNR (25.32 vs 22.73) and rFID (0.37 vs 0.62). Align the Abstract with the Results section which correctly states 'second only to UniTok'.
- **[ac627bd33465] (severity: science)** Resolve the inconsistency in storage efficiency calculations. Section 4.2.2 claims 1/96 compression based on 64 pixels/code (8x8 downsampling), but Section 3.2 and Appendix specify maintaining 16x16 downsampling (256 pixels/code). Recalculate the compression ratio or clarify the downsampling factor to ensure the efficiency claim is mathematically consistent with the architecture.
- **[715d4f95b609] (severity: writing)** Abstract and Introduction claim ViQ ranks 'first among mainstream discrete visual autoencoders' for reconstruction quality. However, Table 2 shows UniTok achieves superior PSNR (25.32 vs 22.73) and rFID (0.37 vs 0.62). The Results section correctly states 'second only to UniTok'. Update Abstract/Intro to align with the data.
- **[385f7efe3a23] (severity: writing)** Figure 1 caption and Introduction claim 'state-of-the-art performance compared with continuous visual encoders'. While average scores are competitive, ViQ trails significantly on OCRBench (636 vs 690 for 6B continuous). Qualify this claim to acknowledge specific task gaps where continuous encoders remain superior.
- **[bdc6e1da4d56] (severity: writing)** Add a dedicated Ethics Statement or Broader Impact section addressing data privacy, consent, and dual-use risks.
- **[771422ba2d4f] (severity: writing)** Explicitly discuss data privacy and consent protocols for web-scraped training datasets (e.g., LLaVA-OneVision, SigLIP2-g).
- **[227b0e40961b] (severity: writing)** Analyze potential dual-use implications of the efficiency gains (20-70% speedup) in the context of surveillance or automated document analysis.
- **[7d6edf6e602a] (severity: science)** Correct the Abstract claim that ViQ ranks 'first among mainstream discrete visual autoencoders' for reconstruction; Table 3 shows UniTok achieves higher PSNR (25.32 vs 22.73).
- **[385dbacdafc5] (severity: science)** Clarify the 'AnyRes' control in Table 1; checkmarks indicate baselines lack AnyRes support, contradicting the text claim that the pipeline was adapted for fair comparison.
- **[7a06cfcbcd02] (severity: science)** Provide statistical significance testing or error bars for the marginal benchmark gains (e.g., 0.1-0.2 points) to validate the 'surpassing SOTA' claim.
- **[01c58c2030b8] (severity: science)** Verify and clarify the '30B vision-language tokens' training claim in Appendix A, as this is unusually high for Stage 2 quantization and impacts reproducibility.
- **[a2a20033f370] (severity: science)** Report standard deviations or confidence intervals for all benchmark scores in Table 1 and Table 5. Single-point estimates do not support claims of statistical significance (e.g., 57.2 vs 57.0).
- **[fd9eb22a35fb] (severity: science)** Address multiple-comparisons handling when claiming state-of-the-art performance across nine distinct benchmarks without correction for Type I error inflation.
- **[e2288a5531b6] (severity: science)** Clarify the number of random seeds used for evaluation and whether results are averaged. MLLM benchmarks often exhibit high variance across seeds.
- **[a8ef28b48f99] (severity: writing)** The manuscript demonstrates a solid structure, but several text formatting inconsistencies require attention to ensure professional presentation and LaTeX hygiene. First, there is a notable inconsistency in paragraph heading commands. The custom command \paragrapha is used extensively (e.g., Line 220, Line 310, Line 710), yet standard \paragraph appears in the Experiments section (Line 460, Line 660). This creates visual and structural irregularities in the heading hierarchy. Authors should unif
- **[1db6b054c260] (severity: writing)** Several sentences are overly long and contain multiple clauses, making them hard to follow (e.g., the first paragraph of the Introduction, lines 9‑20). Break them into shorter sentences and use clearer connectors.
- **[3886c6f14dae] (severity: writing)** Inconsistent terminology and capitalization (e.g., “any resolution” vs. “Any Resolution”, “visual encoder” vs. “Visual Encoder”) appear throughout the manuscript. Standardize terms and follow a consistent style.
- **[1dc4f7232e8c] (severity: writing)** Frequent misuse of punctuation, such as missing commas before subordinate clauses and misplaced commas before “and” in lists (e.g., line 45: “...high‑dimensional visual features, while maintaining high precision…”). Add commas where needed for readability.
- **[e2ec76122d38] (severity: writing)** Redundant phrasing and duplicated content (e.g., the same table appears twice in Sections 3 and 4, and the description of Figure 1 is repeated). Remove duplicates and ensure each element is introduced only once.
- **[4221ca2f600f] (severity: writing)** Inconsistent use of LaTeX macros for symbols (e.g., sometimes `	extbf{ViQ}` is used, other times plain text). Use macros consistently for model names and abbreviations.
- **[f6091a933223] (severity: writing)** Some mathematical notation lacks proper spacing and formatting (e.g., `f_1=L_{\infty}(	ext{BN}(f))` should have spaces around ‘=’ and proper operator formatting). Refine equations for clarity.
- **[27caa0e77213] (severity: writing)** Figure and table captions contain informal language and missing periods (e.g., “	extbf{ViQ delivers high-quality multimodal quantized representations…}”). Rewrite captions in a formal, complete‑sentence style.
- **[b782a801558d] (severity: writing)** The abstract contains a run‑on sentence and ambiguous phrasing (e.g., “...while supporting inputs at native resolutions, thereby enabling it to serve as a unified and general discrete representation for arbitrary visual inputs.”). Simplify and clarify the claim.
- **[5b42d671ff4b] (severity: writing)** The use of symbols like `\ding{51}` and `\ding{55}` in tables is not explained in the legend, which can confuse readers. Add a legend or replace with clear textual markers (e.g., ✓/✗).
- **[78f643f5e4f7] (severity: writing)** The bibliography includes many entries that are not cited in the main text (e.g., some arXiv preprints). Remove unused references to keep the reference list concise.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 40 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

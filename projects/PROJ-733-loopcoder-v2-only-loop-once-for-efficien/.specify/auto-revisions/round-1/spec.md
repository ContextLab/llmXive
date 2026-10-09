# Revision Specification: Paper Science Revision — PROJ-733-loopcoder-v2-only-loop-once-for-efficien round 1

**Generated**: 2026-06-20T21:33:31.720699+00:00
**Kind**: paper_science
**Project**: PROJ-733-loopcoder-v2-only-loop-once-for-efficien
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[6225cf906e3f] (severity: writing)** Add explicit citations for the SWE-bench Verified and Multi‑SWE (SWE‑M) benchmark suites when reporting performance improvements (e.g., baseline 43.0 → 64.4 points).
- **[6c28e63ceec6] (severity: writing)** Provide source references for the comparative numbers of larger open and proprietary models shown in Table 1 (e.g., GPT‑5.1, Claude‑Opus‑4.5, Gemini‑3‑Pro). If these are taken from external papers or leaderboards, cite them accordingly.
- **[9fd38989425b] (severity: writing)** Remove duplicated and unused \usepackage statements (e.g., multiple \usepackage{inputenc}, \usepackage{graphicx}, \usepackage{multirow}) and consolidate the preamble into a single, well‑documented block.
- **[201d426b7437] (severity: writing)** Create a minimal build script (Makefile or a short bash script) that invokes pdflatex/biber with the correct flags and lists all required LaTeX packages, enabling anyone to compile the paper from a fresh TeX Live installation.
- **[e0c6e822d600] (severity: writing)** Add a README.md that documents the exact TeX distribution version, required packages, and any non‑standard fonts or assets (e.g., the custom class `map.cls`), and include instructions for obtaining the `resources/packages.tex` and figure PDFs.
- **[bed88b9ec98e] (severity: writing)** Separate the large preamble into a dedicated file (e.g., `preamble.tex`) and `\input{preamble}` from the main document to improve modularity and readability.
- **[344eb796f1ee] (severity: writing)** Provide a small test suite (e.g., a CI script) that checks the LaTeX source compiles without errors and that all referenced figures/tables exist, ensuring reproducibility of the PDF.
- **[d0b5a952d9f9] (severity: writing)** Document random seeds or deterministic settings used during any data‑driven figure generation (e.g., plots in `graph/`), and include the scripts that produce those figures.
- **[744d1afcf178] (severity: science)** Add a detailed data statement describing the pretraining corpus: source repositories, licensing terms for each component, deduplication methodology, and any filtering applied.
- **[03f5e79046c0] (severity: science)** Provide explicit version identifiers (e.g., commit hashes, dataset release tags) for all external data used, and include checksums (SHA‑256) for the released model checkpoints and any auxiliary files.
- **[c702f90a2369] (severity: writing)** Document the licensing of the released model and any associated code or scripts, and ensure the license is included in the repository (e.g., MIT, Apache‑2.0).
- **[a93f083ad009] (severity: writing)** Archive or snapshot external URLs (e.g., the HuggingFace model page) using a service like archive.org and cite the archived link to mitigate link rot.
- **[bec993cf0e64] (severity: science)** If possible, release a small sample of the pretraining data or a manifest file listing the constituent datasets with their licenses, to improve reproducibility and transparency.
- **[a1ba7d368ba3] (severity: writing)** Add concise, descriptive alt‑text for every figure (e.g., Fig. 1–7) so that screen‑reader users can understand the visualized metrics such as step size δ⁽ʳ⁾, angular change cos θ⁽ʳ⁾, effective rank, KL‑divergences, etc.
- **[3efe05693c29] (severity: writing)** Verify that all axes in the plotted figures have explicit labels (including units where applicable) and that legends are large enough to be legible when the figure is printed at column width.
- **[e2719701bf42] (severity: writing)** Replace or augment the current colour‑only encodings with colour‑blind‑safe palettes or add hatch/marker patterns, especially in heat‑map figures (e.g., Fig. 3 and Fig. 4) where red‑green contrasts are used.
- **[4a65b60e2616] (severity: writing)** Ensure that every caption fully defines all symbols and abbreviations used in the figure (e.g., Ω⁽ʳ⁾, Δp⁽ʳ⁾, ḡ⁽ʳ⁾, D_KL⁽ʳ⁾) so that the figure can be understood without referring back to the main text.
- **[74e84fca1380] (severity: writing)** Provide high‑resolution (300 dpi) PDF/PNG versions of all figures for the final camera‑ready version to avoid loss of detail in print, and check that line widths remain distinguishable at the final scale.
- **[62d96d22c4ee] (severity: writing)** Define every acronym at first use (e.g., PLT, KV, G‑SWA, CLP, RMSNorm, bf16, G‑SWA, LLM, CoT).
- **[1560d641a05e] (severity: writing)** Replace overly technical phrases such as “cross‑loop position offsets”, “latent chain‑of‑thought”, “gain–cost scissors”, and “intrinsic offset cost” with plain‑language equivalents or add brief explanatory footnotes.
- **[dcf27276a351] (severity: writing)** Introduce a concise glossary for domain‑specific jargon (e.g., “sliding‑window attention”, “shared‑KV”, “fixed‑point gap”) to aid non‑specialist readers.
- **[e3f647267307] (severity: writing)** Avoid dense noun clusters like ‘parallel loop transformer (PLT) mechanism, G‑SWA with window size w = 64 and first‑loop KV sharing’ (see Section 2, Eq. (2)). Break into shorter sentences and explain each component in simple terms.
- **[6265e510f34b] (severity: writing)** Limit the use of mathematical symbols without verbal description; for instance, explain the meaning of symbols R, N, δ⁽ʳ⁾, Ω⁽ʳ⁾ in the text rather than only in equations.
- **[74b73da9fe40] (severity: writing)** Reduce repetitive use of the term “loop‑count” when a simpler phrase like “number of iterations” would suffice, especially in Sections 3.1–3.3.
- **[efe52b05cb81] (severity: writing)** Clarify the meaning of “gain–cost trade‑off” early in the Introduction (Section 1) for readers unfamiliar with optimization terminology.
- **[0be5d556baaf] (severity: science)** The paper asserts that the intrinsic offset cost Ω⁽ʳ⁾ remains nearly constant across loops despite a documented decline in effective rank (representation diversity). Provide a more rigorous justification (e.g., statistical analysis across layers and tokens) or reconcile this apparent contradiction.
- **[b0d5ee78f27c] (severity: writing)** Clarify the computational cost of using effective‑rank as a ‘lightweight’ diagnostic for loop‑count selection. If it requires a full forward pass, the claim of low overhead is misleading.
- **[f39c8eae40eb] (severity: writing)** In Section 3.2 (Intrinsic offset cost) the definition of Ω⁽ʳ⁾ uses a mean over adjacent token distances, but the paper does not specify how sequence boundaries (first token) are handled. Explicitly state the treatment of edge cases to avoid ambiguity.
- **[e56605eda4ba] (severity: science)** The gain–cost trade‑off argument hinges on the offset cost being a fixed per‑loop tax while the marginal gain shrinks. Include a quantitative model (e.g., a simple equation or plot) that demonstrates the point where gain < cost, rather than relying solely on qualitative description.
- **[f6514dc1f0b7] (severity: science)** Temper the claim that the observed saturation at two loops is a universal property of PLT. The experiments only cover loop counts 1‑4 and a single 7B model; broader model sizes or higher loop counts are not evaluated.
- **[ea0feb45c88b] (severity: writing)** Clarify that the constancy of the CLP‑induced offset cost is demonstrated only for the PLT₄ configuration; acknowledge that this may not hold for other architectures or training regimes.
- **[d5ad49df98d1] (severity: science)** Add a dedicated section on dual‑use risks, explicitly discussing how LoopCoder‑v2 could be used to generate malicious or vulnerable code (e.g., exploits, ransomware) and outline mitigation strategies such as usage‑policy enforcement, model‑output filtering, and rate‑limiting.
- **[3c3ff7539aaf] (severity: science)** Provide a clear data‑licensing audit for the 18 T‑token pre‑training corpus, especially the code portion. Verify that all code snippets are either public‑domain, permissively licensed, or have been appropriately filtered for copyrighted material.
- **[6c2bf939a0ee] (severity: writing)** Describe any steps taken to remove personally identifiable information (PII) from the text side of the corpus and from the instruction‑tuning dataset. If no PII‑scrubbing was performed, acknowledge the risk and propose a remediation plan.
- **[0adec09aef6c] (severity: writing)** Include a responsible‑release statement in the paper and the HuggingFace repository, specifying the intended use cases, prohibited applications, and a contact channel for reporting misuse.
- **[426b609440d2] (severity: science)** Assess the potential impact of the CLP positional offset on model interpretability and safety: could the offset cause subtle mis‑alignments that lead to incorrect code generation in safety‑critical contexts? Recommend evaluation on safety‑focused benchmarks (e.g., code that must not contain insecure patterns).
- **[f3f941393510] (severity: writing)** Clarify whether any human annotators were involved in the instruction‑tuning data creation. If so, confirm that IRB approval or equivalent ethical review was obtained, and include a brief description of consent procedures.
- **[59bc2fb50b68] (severity: science)** The manuscript reports benchmark scores (e.g., Table 1) without any statistical significance testing or confidence intervals. Add appropriate hypothesis tests (e.g., paired bootstrap) and report p‑values or confidence intervals to substantiate claims of improvement over baselines.
- **[f70b8b66d00f] (severity: science)** Multiple benchmark suites are evaluated (≈10) and many metrics are compared across loop counts, yet no correction for multiple comparisons is discussed. Include a brief justification (e.g., Bonferroni, Holm) or report family‑wise error rates.
- **[8f711118a6c4] (severity: writing)** Figures show 95 % confidence bands derived from 500 samples, but the sampling procedure (random seed, data split) is not described. Clarify how the samples are drawn, whether they are independent, and provide the exact method for CI computation.
- **[2afbda66ffb1] (severity: science)** Reproducibility of the statistical analyses is limited: the code for computing step‑size, effective rank, KL divergences, and the offset cost is not released. Provide a public repository (or include in the HuggingFace repo) with scripts and exact random seeds used for all diagnostics.
- **[6cd0433ae825] (severity: science)** Assumptions underlying the per‑loop metrics (e.g., normality of hidden‑state updates, independence of token‑wise distances) are not examined. Add a brief diagnostic (e.g., QQ‑plots or Shapiro‑Wilk tests) to justify the use of means and standard errors.
- **[d13adb9c02fb] (severity: writing)** Remove duplicate and redundant package imports (e.g., multiple `inputenc`, `graphicx`, `booktabs`, `array`, `multirow`, `float` etc.) to improve LaTeX hygiene and reduce compilation overhead.
- **[2510b3387af6] (severity: writing)** Standardize table formatting: use `booktabs` consistently, align numeric columns on the decimal point (e.g., `S` column type from `siunitx`), and ensure all tables have a `\\label` placed after the `\\caption`.
- **[d7716014df52] (severity: writing)** Place all figure `\\caption{...}` commands immediately after the `\\includegraphics` line and before the `\\label`, and add a `\\label` to each figure for reliable cross‑referencing.
- **[3a0c8986bb1b] (severity: writing)** Replace raw `\\paragraph{}` headings with proper `\\subsection` or `\\subsubsection` where appropriate to maintain a clear hierarchical structure and avoid overly dense paragraph headings.
- **[fb2864233b27] (severity: writing)** Ensure all cross‑references (`\\autoref{...}`) point to existing `\\label`s; some references (e.g., `\\autoref{sec:exp-results}`) lack a matching label in the source.
- **[827c8dfbb4d3] (severity: writing)** Consolidate and order package imports: load core packages first (`amsmath`, `amssymb`, `graphicx`, `hyperref`), then optional ones, and avoid re‑defining colors or commands in multiple places.
- **[71f1f74db70f] (severity: writing)** Abstract (lines 1‑9) contains several run‑on sentences and inconsistent tense; break into shorter sentences and ensure parallel structure.
- **[a73c6e121746] (severity: writing)** In the Introduction (section 1, lines 120‑150) the phrase “standard sequential looping is difficult to deploy efficiently” is vague; replace with a concrete description of latency and memory growth.
- **[d56b2d69bdb4] (severity: writing)** Throughout the manuscript, commas are often missing before coordinating conjunctions (e.g., “...and attention routing, and output‑distribution shift” in §3.2); add Oxford commas for clarity.
- **[00511d5d85d2] (severity: writing)** The term “gain–cost” is introduced in multiple places with inconsistent hyphenation (e.g., “gain–cost view” vs. “gain–cost trade‑off”); standardize to “gain–cost”.
- **[d9e65d163bc4] (severity: writing)** Algorithm 1 (lines 260‑285) mixes inline comments with full sentences; reformat comments to be concise fragments and align indentation.
- **[3910ebc33a67] (severity: writing)** Table 1 (lines 340‑360) mixes units and symbols without spaces (e.g., “7B‑parameter”); insert a space or use an en‑dash consistently.
- **[dd0eeb02ae65] (severity: writing)** Figure captions (e.g., Fig 2 caption lines 380‑390) contain informal language like “the gain–cost scissors”; replace with formal phrasing such as “gain–cost trade‑off diagram”.
- **[c4c40baa6d03] (severity: writing)** The Discussion section (§6) repeats the same bullet points from the analysis; consolidate to avoid redundancy.
- **[bfac9c9e87e2] (severity: writing)** Multiple sections contain duplicated LaTeX packages (e.g., \usepackage{graphicx} appears three times in the preamble); clean the preamble to improve readability of source.
- **[e7854438f586] (severity: writing)** Some equations lack proper punctuation after the displayed formula (e.g., Eq. (1) on line 210); add commas or periods to integrate them into the narrative.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 58 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

# Revision Specification: Paper Science Revision — PROJ-638-https-arxiv-org-abs-2605-28820 round 1

**Generated**: 2026-06-18T16:14:54.602882+00:00
**Kind**: paper_science
**Project**: PROJ-638-https-arxiv-org-abs-2605-28820
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[544978953e2c] (severity: writing)** Complete the truncated bibliography file (custom.bib ends mid-entry at 'OpenImag') to ensure all citations can be verified and compiled properly.
- **[bf9810b128fc] (severity: writing)** Remove redundant LaTeX package imports (wrapfig appears twice, colortbl appears twice) to improve compilation reliability.
- **[5eb1734f97fb] (severity: writing)** Clarify the arXiv submission date (2605.28820 appears to be May 2026, which is future-dated) to avoid confusion.
- **[23a9d320bd63] (severity: science)** Expand ablation studies to include comparisons across different backbone sizes and training data scales.
- **[ba17c4f34ab8] (severity: science)** Provide detailed breakdown of training data composition (sources, quality filtering, domain distribution) beyond approximate counts.
- **[6dc852f7512e] (severity: writing)** Correct the DocVQA citation: The current bib entry (Clark & Gardner, 2018) refers to reading comprehension, not the DocVQA dataset (Masry et al., 2021). Update to the correct source to ensure factual accuracy.
- **[56fa4191e634] (severity: writing)** Complete the truncated bibliography entry for OpenImag (Datasets:OpenImag). The current entry is cut off, preventing verification of this citation.
- **[1dc4195139f5] (severity: writing)** Verify all future-dated citations (e.g., Qwen3, GeoThinker 2026) are intentional and consistent with the paper's timeline context, as they may appear as hallucinations to external readers.
- **[981efc80f304] (severity: writing)** Code artifacts (training scripts, model definitions, evaluation pipelines) are missing from the review package, preventing assessment of reproducibility and implementation quality.
- **[d5cf4cbcc398] (severity: writing)** Dependency specifications (requirements.txt, environment.yml) are absent, making it impossible to verify dependency hygiene or environment reproducibility.
- **[01e04f42270a] (severity: writing)** Test suites and CI configurations are not provided, so test coverage and modularity cannot be evaluated.
- **[45a1b3e2308d] (severity: science)** Explicitly list training dataset names, licenses, and access URLs in a new Data Availability section.
- **[66a770198739] (severity: science)** Include version hashes or commit tags for the code and data used to generate reported results.
- **[e2683d7e87dc] (severity: writing)** Verify all external URLs in the bibliography for stability and provide DOIs where possible.
- **[1a2d26e1d90a] (severity: writing)** Restructure the three-panel layout at line 548. Multiple \caption commands in one figure* environment cause numbering conflicts. Use subcaption package or separate floats.
- **[7eb8dc60199e] (severity: writing)** Correct the filename typo 'trainning_recipe.pdf' to 'training_recipe.pdf' at line 252 to maintain professionalism.
- **[3d91e3b2f21c] (severity: writing)** Ensure all plot axes in figures 4a-c have sufficient font size for print legibility and verify colorblind-safe palettes are used.
- **[39914879e337] (severity: writing)** Define all acronyms (KV, RoPE, VE) at first use; KV caching appears in Introduction without definition.
- **[338dc0164b4f] (severity: writing)** Replace coined terms like 'Pre-Buffer' and 'One-Vision' with plain descriptions or define them clearly upon first mention.
- **[48cd90866585] (severity: writing)** Reduce frequency of 'native' and 'spatiotemporal'; use 'unified' and 'space and time' to improve accessibility.
- **[b3f05340aabf] (severity: writing)** Clarify the claim 'excelling at fine-grained visual perception' in the abstract, as Table 1 shows lower performance on OCRBench and TextVQA compared to modular counterparts. Define scope to avoid ambiguity.
- **[3110dfeea530] (severity: writing)** Resolve terminology inconsistency between 'NEO-ov (9B)' in Section 4.1 and 'Instruct-8B' in Table 1 to ensure parameter count clarity.
- **[df4e92ebf2c5] (severity: science)** Specify LLM initialization state (random vs. pre-trained) in the Ablation Study (Section 5.1) to validate the causal link between attention mechanism and performance gains.
- **[b49516778f2e] (severity: writing)** Abstract claims NEO-ov 'excels at fine-grained visual perception' (Line 28). Table 1 shows NEO-ov 8B trails Qwen3-VL on DocVQA (91.2 vs 93.3) and OCRBench (81.2 vs 85.8). Limitations (Line 558) admit OCR is underexplored. Tone down 'excels' to 'remains competitive' to avoid overclaiming on fine-grained tasks.
- **[8572f9d1ccc8] (severity: writing)** Title 'At Scale' (Line 1) implies frontier scaling. Model uses 8B backbone (Line 362). While valid for native VLMs, clarify scale context in Abstract to distinguish from trillion-token modular predecessors to prevent overinterpretation of 'scale'.
- **[a936e6d88a5e] (severity: writing)** Expand the 'Ethical Considerations' section to detail specific data safety protocols used for the 80M+ web-scraped samples (e.g., PII removal, copyright filtering, harmful content moderation).
- **[834a1c4d9ccf] (severity: writing)** Provide a more concrete analysis of potential dual-use risks, specifically regarding the model's fine-grained OCR and spatial intelligence capabilities, rather than generic statements.
- **[a0dd4fc13bed] (severity: science)** Provide statistical significance testing (e.g., confidence intervals, p-values) for benchmark comparisons, as point estimates alone cannot establish reliable performance differences.
- **[3b8c95a403bd] (severity: science)** Clarify compute budget parity in Figure 3a ablation; claim of 'fair comparison' conflicts with main model using pretrained Qwen3 backbones.
- **[db5dfbd803dc] (severity: science)** Report variance across multiple training runs (e.g., 3 seeds) rather than single-run results to assess reproducibility and robustness.
- **[cf1b5db97666] (severity: science)** Address multiple comparisons problem across 27+ benchmarks without statistical correction to reduce false positive risk.
- **[4d554eb9b91b] (severity: science)** Report standard deviations or confidence intervals for key benchmark scores (e.g., MMMU, VideoMME) to validate claims of superiority over baselines. Single point estimates are insufficient for statistical significance.
- **[6d6ed7235c6f] (severity: writing)** Resolve the model size inconsistency between Implementation Details (Qwen3-1.7B) and Table headers (Instruct-2B) to ensure reproducibility.
- **[75937ef41d03] (severity: science)** Discuss the statistical significance of ablation study results (Figures 3-5) or acknowledge the limitation of single-run comparisons.
- **[46cda104201e] (severity: writing)** Remove duplicate package imports (e.g., `xspace`, `wrapfig`, `colortbl`) to avoid unnecessary loading and potential conflicts. See lines near the top of `main-llmxive.tex` where packages are listed twice.
- **[893805a98012] (severity: writing)** Consolidate color definitions: `tablerowcolor`, `tablerowcolor1`, `tablerowcolor2`, `mygray`, `mytableblue`, `mytablegreen`, `mygreen`, `mycitecolor` are defined both in the wrapper and in `review.tex`. Keep a single definition to maintain consistency. Refer to lines 45‑55 in `main-llmxive.tex` and lines 70‑80 in `review.tex`.
- **[f996fde15a90] (severity: writing)** Standardize table formatting: avoid mixing `\rowcolor` commands with `\multicolumn` rows that span the full width; instead place `\rowcolor` after the `\multicolumn` line or use `\rowcolors` for alternating rows. This improves readability and prevents unexpected background colors. See Table 1 around line 210.
- **[230a830d2511] (severity: writing)** Ensure all figure and table captions are placed immediately after the `\caption{...}` command and before any `\label{...}` to follow LaTeX best‑practice. Double‑check consistency across all figures (e.g., Figure 1 at line 120).
- **[aab433fd1580] (severity: writing)** Remove unused macro definitions (e.g., `\providecommand{\TODO}[1]{}`) if they are not referenced in the manuscript to keep the preamble tidy.
- **[7823c4f3ae90] (severity: writing)** Replace informal transition words like 'Besides' with 'Furthermore' or 'Moreover' in the Introduction to maintain academic tone.
- **[6855a3ea9125] (severity: writing)** Correct missing definite articles, such as 'the original LLM tokenizer' in the Methodology section.
- **[9210576ece8d] (severity: writing)** Replace commercial phrasing like 'launch' in the Conclusion with 'propose' or 'present' to align with academic conventions.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 42 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

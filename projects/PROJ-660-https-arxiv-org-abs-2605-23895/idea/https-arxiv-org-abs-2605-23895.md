---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/271
---

# https://arxiv.org/abs/2605.23895

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.23895

Submitted by: github-actions[bot]

(Intake from human-submission issue #271.)

## Rejection rationale (2026-06-16)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[55caeb97bd54]** Correct the citation for the statement about activation-maximization methods. The cited papers (Sereno1995Science, Engel1997CerebCortex) discuss retinotopic mapping and low-level visual organization, not activation-maximization techniques. Replace with appropriate references to modern activation-maximization work in neuroscience (e.g., NeuroGen \cite{neurogen} or related studies).
- **[321d079ba314]** Provide a supporting citation for the claim that activation-maximization methods cannot distinguish true concept representations from correlated cues. If this is an empirical observation, cite a study that demonstrates the limitation, or qualify the statement as a hypothesis.
- **[4fea594a5404]** Verify that all statements about “early fMRI studies revealed important aspects of visual organization” are accurately matched to the cited references. For example, ensure that the citation to Kanwisher1997 indeed supports the claim about category-selective regions for faces, and similarly for Epstein1998, downing2001cortical, and cohen2000visual.
- **[8776dc5544fc]** When asserting that BrainCause “recovers known functional localizations and identifies new candidate representations across dozens of concepts,” ensure that the quantitative results (e.g., number of concepts with high causal scores) are explicitly reported in the main text or appendix to substantiate the “dozens” claim.
- **[286020b4caf4]** Clarify the source of the 260 concepts list. The manuscript states it was generated using ChatGPT (GPT-5) \cite{openai2025gpt5systemcard}; confirm that this system card indeed describes GPT-5 capabilities relevant to concept list generation, or replace with a more appropriate citation.
- **[ec07533c49a1]** Remove duplicate and redundant package imports (e.g., multiple `\usepackage{graphicx}`, `\usepackage{multirow}`, `\usepackage{makecell}`, `\usepackage{booktabs}`). This improves readability and reduces potential compilation warnings.
- **[7e1cf6f0d644]** Add a reproducibility README or Makefile that documents the exact LaTeX compilation command (e.g., `pdflatex -interaction=nonstopmode neurips_2026.tex` followed by `bibtex` and a second LaTeX run). Include any required font or style files.
- **[50d59df15aa6]** Explicitly list all external dependencies (e.g., the `neurips_2026` class, LaTeX packages not in standard distributions) and provide version numbers or a `texlive` snapshot reference to ensure builds are deterministic.
- **[d1568133ef31]** Consolidate all table and figure inputs into a single `src/` directory and reference them with relative paths (e.g., `\input{src/tables/sanity_check.tex}`). This clarifies the project structure and aids modularity.
- **[ee90b7035185]** Provide a short script (Python or shell) that automates the generation of the synthetic image datasets used in the paper, including model download commands, random seeds, and any required API keys. This is essential for full reproducibility of the results.
- **[c4f8d6806d07]** Add unit‑style checks (e.g., a CI workflow) that verify LaTeX compilation succeeds on a fresh environment and that all `\input{}` files are present. This prevents broken builds when files are moved or renamed.
- **[a21cd849f480]** Consider splitting the large `methods` and `results` sections into separate `.tex` files (`methods.tex`, `results.tex`) and `\input` them. This improves modularity and keeps the main file concise.
- **[d8ffd9d45917]** Remove the commented‑out `\usepackage{neurips_2026}` lines that are no longer needed once the `preprint` option is set. Clean comments reduce visual clutter.
- **[5ec4e4328d6b]** Add an explicit data‑availability and licensing statement for all external resources (NSD fMRI data, FLUX.2, Gemma‑3, Qwen3‑VL, COCO image pool). Specify the exact version/release used and include a permissive license identifier (e.g., CC‑BY‑4.0, MIT).
- **[cad2402ec48f]** Provide a persistent, archived URL (e.g., via Zenodo or OSF) for the project page and any code repositories referenced. Include a DOI to guard against link rot.
- **[65775c7dd386]** Document the schema used for the generated stimulus sets (image files, metadata, verification labels) and describe how missing or failed generations are handled (e.g., filtering criteria, fallback procedures).
- **[968e1a0db793]** Include version‑control information for the pipeline (git commit hash, branch name) and for the large models (model card identifiers, checkpoint hashes). This aids reproducibility and provenance tracking.
- **[5194c2b22e93]** Clarify how the retrieved images from the NSD and COCO pools are stored, whether any preprocessing (e.g., normalization) is applied, and provide checksums for the final image‑fMRI pairs to detect corruption.
- **[a6305e9e106c]** Figure 1 (Overview) lacks a clear legend for the color coding used in the bottom panel. Add a concise legend or annotate the regions directly to indicate which colors correspond to high activation versus low causal response.
- **[899bdc07494c]** Figures 4 and 5 (causal ranking and concept activation maps) present flatmaps without axis ticks or a scale bar indicating cortical distance. Include a scale bar or annotate approximate anatomical landmarks to aid interpretation.
- **[3211cfc009df]** Figure 6 (clusters) uses color gradients but does not provide a color bar for the intensity values. Add a color bar to clarify the meaning of the color scale.
- **[28050683acce]** In Figure 7 (Retrieval Statistics) the two histograms share the same y‑axis label but the units differ (counts vs. number of images). Separate the axes or add distinct labels to avoid confusion.
- **[8a0aa9cecbf0]** Several supplementary figures (e.g., S1 activation comparison, S2 negative fail) contain small text that becomes illegible when printed at 1 column width. Increase font size for axis labels and legends to ensure legibility at print scale.
- **[43a738665f5b]** Alt‑text descriptions are missing for all figures, which hampers accessibility. Provide concise alt‑text for each figure describing the main visual content and the key takeaway.
- **[2fd99d150cec]** Figure 3 (causal evaluation) shows example regions but does not label which brain area each panel corresponds to (e.g., FFA, EBA). Adding region labels will help readers connect the visualizations to known functional anatomy.
- **[a6166bc5fbdb]** Figure 2 (Methods) includes a dense schematic with multiple arrows; some arrows overlap, reducing clarity. Redraw the schematic with clearer spacing or use numbered steps to improve readability.
- **[ceea1f7bdc9c]** The color palette in Figures 4 and 5 uses reds and blues that may be problematic for color‑blind readers. Consider using a color‑blind‑friendly palette or adding patterns/annotations to differentiate categories.
- **[34cb3d4a1ea8]** Define every acronym at first appearance (e.g., fMRI, NSD, VLM, LLM, CLIP, ROI).
- **[e4624f2f349f]** Replace overly technical phrases such as “causal specificity scores”, “counterfactual negatives”, and “semantic-negative generation failures” with plain alternatives like “specificity score”, “edited images that remove the target”, and “failed negative examples”.
- **[e63044e8d1d6]** Shorten and simplify long, nested sentences (e.g., the multi‑clause description in the Introduction and Methods). Break them into two sentences and use everyday verbs where possible.
- **[92c943cb02ec]** Avoid discipline‑specific jargon that may be opaque to non‑specialists, e.g., replace “image‑to‑fMRI encoding model” with “model that predicts brain responses from images”.
- **[7644aec562a2]** Provide brief, lay‑person‑friendly explanations for specialized concepts such as “counterfactual editing” and “semantic negative images” the first time they are introduced.
- **[9ec9aa6ae4c5]** Standardize terminology: use either “positive images” or “target images” consistently throughout, and likewise for “negative images”.
- **[ecc4570e59e0]** Add a short glossary of key terms (e.g., causal dataset, voxel, region of interest) either in the appendix or as footnotes to aid readers from adjacent fields.
- **[d1542d57b681]** Temper claims that BrainCause ‘discovers’ robust, concept‑specific brain representations when most of the evidence relies on predicted fMRI responses; provide explicit caveats and quantify the prediction model’s reliability for each voxel/region.
- **[0c03f9928267]** Add a dedicated evaluation on measured fMRI data for a representative subset of concepts (especially those highlighted as novel discoveries) to substantiate the “new candidate representations” claim.
- **[716398f942e3]** Report the encoding performance (e.g., Pearson r) of the image‑to‑fMRI model for the voxels used in the analysis, and discuss how prediction error may affect causal scores.
- **[6f42ed630ca5]** Clarify the statistical significance thresholds used for the final verdict and include multiple‑comparison correction when reporting p‑values across 260 concepts.
- **[7abfa78cb9b2]** Rephrase statements that suggest causal inference about brain function (e.g., “BrainCause reveals causal representations”) to acknowledge that causal conclusions are limited to the set of tested counterfactuals and model assumptions.
- **[235807b81a73]** Explicitly state that any new fMRI data collection (Section 3.3 and Appendix C) will be performed under a fully approved IRB protocol, describing informed‑consent procedures, especially for stimuli containing human bodies, faces, or potentially sensitive content.
- **[0f39a89ffd5c]** Add a dedicated discussion of privacy and dual‑use considerations (e.g., potential for decoding personal visual experiences) and outline data‑handling safeguards for the NSD data and any newly collected data.
- **[c6dc4d07e095]** Implement and describe a content‑filtering pipeline for generated and edited images to prevent the inclusion of offensive, disturbing, or otherwise inappropriate visual material in both the training set and any follow‑up experiments.
- **[f6a9ebe65092]** Provide a more detailed statistical analysis of the causal scores, including effect size estimates, confidence intervals, and correction for multiple comparisons across the 260 concepts.
- **[c3e8888b0d50]** Quantify and report the false‑positive rate of the semantic‑negative generation pipeline (Fig. S9) and discuss mitigation strategies, such as iterative refinement or human verification.
- **[563c326e19f6]** Clarify the criteria used to select the p‑value thresholds for the five validation tests (Appendix C) and justify the choice to avoid potential p‑hacking.
- **[801a20c4edca]** Include an ablation that isolates the contribution of the image‑to‑fMRI encoder’s prediction noise on the causal scores (e.g., by varying the voxel‑filtering Pearson‑r threshold).
- **[79749196b4e6]** Report the distribution of activation and causal scores (e.g., mean ± SD) for each method in the main text rather than only averages, to convey variability across concepts.
- **[61946feceda1]** Provide a clear multiple‑comparisons correction (e.g., FDR or Bonferroni) for the 260 concepts × 4 subjects when reporting p‑values, and update the significance tables accordingly.
- **[c430dfc9868b]** Report confidence intervals or standard errors for the activation, semantic‑negative, and edit scores (both on generated and measured data) to convey estimation uncertainty.
- **[03f919bacba4]** Clarify the exact procedure for the empirical p‑value calculation: size of the baseline concept set, how baseline concepts are generated, and whether the same baseline set is reused across concepts.
- **[618c5aeee17b]** Document the random seeds, model version hashes, and prompt templates used for image generation, editing, and verification to enable exact replication of the causal stimulus sets.
- **[e8379460f3cc]** Include diagnostic checks (e.g., normality, homoscedasticity) for the voxel‑wise score distributions and discuss whether the assumptions of the statistical tests hold.
- **[11f34e573fb8]** Specify how the training/validation split of images is performed (e.g., number of images per split, stratification) and ensure that region selection is fully independent of the held‑out evaluation data.
- **[c9ebcb9803c9]** Remove duplicate \usepackage entries (e.g., graphicx, makecell, multirow). This redundancy clutters the preamble and can cause warnings.
- **[0711f35b7fe1]** Avoid manual \vspace adjustments immediately before \section headings and after \caption. Use proper LaTeX spacing commands or let the class handle vertical space to maintain consistent layout.
- **[c5cb641a1f59]** Place \label{...} directly after \caption{...} in all figures. The current pattern (\caption{...}\vspace{-0.4cm}\label{...}) may lead to mis-numbering or broken references.
- **[ed469de099cf]** Add \centering to all table environments that currently lack explicit alignment to ensure tables are centered on the page.
- **[6f15b6d3508e]** Consolidate package loading: keep a single occurrence of each package and remove commented-out \usepackage{neurips_2026} lines that are no longer needed.
- **[87dd19a3301b]** Consider moving \vspace adjustments inside the figure/table environments (e.g., using \setlength{\belowcaptionskip}{...}) rather than inserting raw \vspace commands, which improves maintainability.
- **[6b137869a871]** Reduce overly long, nested sentences (e.g., in the abstract and introduction) to improve readability; split into shorter sentences where possible.
- **[9ff8de4d6245]** Correct inconsistent verb tenses (e.g., mix of present and past in the methods description) to maintain a uniform narrative.
- **[a2794674ef2b]** Standardize terminology for key concepts (e.g., use either "causal score" or "causality score" consistently throughout the manuscript).
- **[9e977bd66a20]** Fix minor grammatical errors such as missing articles, misplaced commas, and subject-verb agreement (e.g., add a comma after "representation").
- **[a4d5929f0a54]** Improve figure captions for clarity by explicitly defining abbreviations (e.g., "Pos.", "Neg.") and ensuring they are self-contained.
- **[b0ae8375ff80]** Remove redundant phrasing (e.g., "In addition, BrainCause also retrieves") to tighten the prose.
- **[ac3a16006bfa]** Ensure consistent formatting of citations (e.g., avoid mixing \cite{...} with plain text references in the same sentence).
- **[43f47c5c9ba9]** Proofread the reference list for typographical consistency (e.g., uniform use of periods after journal names and consistent capitalization).

# Revision Specification: Paper Science Revision — PROJ-682-your-unembedding-matrix-is-secretly-a-fe round 1

**Generated**: 2026-06-14T00:46:21.992069+00:00
**Kind**: paper_science
**Project**: PROJ-682-your-unembedding-matrix-is-secretly-a-fe
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[3b151a9a66b3] (severity: writing)** The proof in Appendix Section 8 incorrectly states that the projection matrix V_tau V_tau^T is identity. This is mathematically false when dimensionality reduction is applied (V_tau is a subset of columns). While Equation 1 holds, the justification misrepresents the transformation as an isometry on the full space. Correct the text to accurately describe the projection property.
- **[94b7f0d9f5cc] (severity: writing)** The claim citing lv2024fact states it describes the 'average token' as a 'frequency-weighted average embedding over the training corpus'. Verify this attribution explicitly matches the cited paper's content to ensure citation accuracy.
- **[4c3b8fa91e3e] (severity: writing)** The term 'Logit Spectroscopy' is attributed to spectral. The cited paper title is 'Spectral Filters...'. Clarify if this is a direct quote or a new naming convention to ensure proper credit and terminology accuracy.
- **[accae5eed9ca] (severity: science)** Code repository is referenced externally (github.com/CentreChen/EmbFilter) but not included in submission. For code quality review, actual implementation files must be accessible to verify reproducibility, modularity, and test coverage.
- **[0a9fcbe17559] (severity: writing)** Algorithm pseudocode and PyTorch implementation in the appendix are commented out (# comments). Include working code snippets or at minimum un-comment the implementation for reviewer verification.
- **[e858b91931c4] (severity: science)** No dependency specification (requirements.txt, environment.yml, or similar) is included in the paper artifacts. Add explicit dependency list for reproducibility from scratch.
- **[5af66173d9e3] (severity: writing)** Update conference metadata in lines 48-52 to reflect the 2026 submission context instead of the 2018 template placeholders.
- **[86fb96875fa6] (severity: science)** Specify exact version numbers for MTEB benchmark and RedPajama dataset used in experiments (e.g., MTEB v1.0) in Section 3.2.1 and Section 5.1.
- **[8fcd1d94ef3e] (severity: writing)** Include a software license (e.g., MIT, Apache 2.0) and a specific git commit hash or tag for the code repository linked in the abstract (Line 167).
- **[cff7f0b76812] (severity: writing)** Replace word clouds in Figure 1 with quantitative bar charts showing top-k token probabilities to support mechanistic claims.
- **[de07c4d238bb] (severity: writing)** Ensure all plots (Fig 2, Fig 4) include explicit axis labels (e.g., Dimension Index, Delta Pi) visible at print scale.
- **[c838703cacc6] (severity: writing)** Verify color choices in Tables and Figures (e.g., MediumPurple, DodgerBlue) are colorblind-safe and legible in grayscale.
- **[5886174897b8] (severity: writing)** Add alt text descriptions to all figure captions for accessibility compliance.
- **[0b15f864de76] (severity: writing)** Define the acronym MTEB at its first occurrence in the Abstract or Introduction, rather than waiting until Section 5.
- **[ff1385d5585e] (severity: writing)** Provide a brief gloss of 'Logit Spectroscopy' in Section 1 when first invoked, instead of deferring the definition to Section 2.
- **[7017e6668bf8] (severity: writing)** Replace or parenthetically explain 'anisotropic' and 'representation collapse' in Section 1 to aid non-specialist readers.
- **[9d7916207499] (severity: science)** The mathematical proof in Appendix sec:proof incorrectly claims V_tau * V_tau^T is the identity matrix. For dimensionality reduction (k < d), this is a projection matrix, not identity. This invalidates the claim that the transformation preserves the original norm.
- **[7714047b00d5] (severity: science)** Table 5 shows filtering the Dominant subspace (Config 3) degrades performance (47.53 vs 50.07 baseline), contradicting the claim that both edges of the spectrum encode noise. Explain why filtering both edges (EmbFilter) helps while filtering Dominant alone hurts.
- **[b24b79ae4b0b] (severity: writing)** Clarify the "distance-preserving" claim in Section 4.2. The transformation preserves distances within the subspace, not the original Euclidean distance. The current phrasing implies original distance preservation, which is mathematically false for reduced dimensions.
- **[2b443c738d5a] (severity: science)** Correct the mathematical proof in the Appendix claiming the projection matrix is identity.
- **[0da91ea9b31f] (severity: writing)** Soften claims of "universal pattern" in Abstract and Introduction to reflect limited model scope.
- **[e4989ccf4acf] (severity: writing)** Rephrase "actively writing" in Abstract to avoid implying unproven causal mechanisms.
- **[7e3d595f5472] (severity: science)** Report standard deviations and confidence intervals across multiple random seeds. All MTEB results in Tables 1-4 appear to be single-run averages without variance estimates.
- **[671015828049] (severity: science)** Add statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals) between EmbFilter and baseline methods. Claims of 9-14% improvements lack statistical validation.
- **[f4375e6a98e5] (severity: science)** Clarify whether the optimal τ=2 configuration was pre-specified or selected post-hoc from τ={2,4,8} trials. Multiple τ testing without correction risks cherry-picking.
- **[447dab7e93a9] (severity: science)** Provide causal evidence for the edge spectrum mechanism. Currently relies on correlational Logit Lens analysis; consider ablation studies that isolate edge spectrum effects from general dimensionality reduction.
- **[def8465e8ccc] (severity: science)** Report standard deviations or confidence intervals over multiple random seeds for all MTEB results.
- **[7e507b72e55e] (severity: science)** Correct the data inconsistency in Table 4 where PromptEOL and ECHO baselines are identical.
- **[c0747ea3683c] (severity: science)** Include statistical significance testing (e.g., paired t-tests) to validate reported performance gains.
- **[c752e4e42c2c] (severity: writing)** The input source contains two complete LaTeX document structures. If concatenated as a single file, this will cause compilation errors. Ensure only one valid document structure is submitted.
- **[1902b7e9be8e] (severity: writing)** Subsection headings exhibit inconsistent capitalization and punctuation. For example, Text embedding with EmbedFilter uses lowercase e, while Text Embedding Paradigm uses uppercase. Additionally, some titles end with periods while others do not.
- **[413dda606ebe] (severity: writing)** Equation formatting is inconsistent. The manuscript mixes display math environments and equation environments, often with size modifiers. Standardize on equation environments for consistency.
- **[7d983d4990a6] (severity: writing)** Citation commands are used inconsistently with different natbib variants. Select one command style for uniformity.
- **[e626da1a3d01] (severity: writing)** There is an extra space in the subsection title Comparison between EmbedFilter and Embedding Calibration Baselines. Remove the double space between and and Embedding.
- **[b09d292400be] (severity: writing)** Correct subject-verb agreement errors (e.g., '
ame suppress' -> 'suppresses', 'contributor that steer' -> 'steers', 'methods exhibits' -> 'exhibit', 'requires' -> 'require').
- **[d4804c59236e] (severity: writing)** Fix article usage and typos (e.g., 'an mechanism' -> 'a mechanism', 'from training corpus' -> 'from the training corpus', 'acorss' -> 'across', 'speedup retrieval' -> 'speed up retrieval').
- **[98ff5cf4cfe9] (severity: writing)** Ensure proper punctuation, including adding a period after 'identification' in the Introduction and capitalizing 'This completes' in the Appendix.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 37 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.

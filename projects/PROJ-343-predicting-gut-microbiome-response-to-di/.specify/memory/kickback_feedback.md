# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 specifies subsampling to **[deferred] reads per sample**, while the Assumptions section later states subsampling to **10,000 reads per sample**. The placeholder in the requirement is not explicitly resolved, creating an internal inconsistency between the functional requirement and the design assumption.
- FR-005 defines the response variable as the **Aitchison distance** (Euclidean after CLR transformation), whereas the Idea section’s Methodology Sketch states the response is the **Euclidean distance** on raw genus‑level abundances. This contradictory definition creates an internal inconsistency in how the response metric is computed.
- The Assumptions section still refers to **[deferred] reads per sample** for subsampling depth, while the Standardized Microbiome Processing principle (VI) and the revised FR‑003 claim a concrete depth of 10,000 reads. The placeholder in Assumptions is unresolved, leading to conflicting specifications.
- Edge Cases still mention **[deferred] reads per sample** for the ‘Insufficient Reads’ scenario, which conflicts with the now‑specified 10,000‑read subsampling depth.
- FR-004 limits baseline predictor features to Shannon diversity and Faith’s Phylogenetic Diversity only, omitting baseline taxonomic (genus‑level) abundances that the original idea explicitly required for predicting response magnitude.
- FR-005 defines the model input as the two diversity metrics, whereas the idea’s research question emphasizes *baseline gut microbial composition* (i.e., taxa abundances) as the predictive signal. This constitutes an under‑reach and a subtle drift of the research question.
- [template_placeholder] unfilled [NNN-...] branch-name template placeholder in 'projects/PROJ-343-predicting-gut-microbiome-response-to-di/specs/001-predicting-gut-microbiome-response-to-di/spec.md': '[###-feature-name]'. A converged spec must not carry this; the reviser must resolve it before the spec advances.

## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about causal determinants of CTCF site selection across cell types—a substantive biological phenomenon about gene regulation. Mechanistic interpretability methods are positioned as the tool to reveal these determinants, not as the question itself. The core scientific question (what features drive selective CTCF engagement) is independent of any specific model architecture or interpretability technique.

### Circularity check

**Verdict**: pass

The predictor variables (DNA sequence motifs, ATAC-seq accessibility, histone modification profiles) come from independent experimental measurements. The predicted variable (CTCF binding probability) is derived from ChIP-seq data. These are distinct modalities; the predictors are not summaries of the binding signal itself, so the relationship is empirically testable rather than mechanically guaranteed.

### Triviality check

**Verdict**: pass

A positive result (identifying 3-5 interpretable latent features driving cell-type-specific CTCF engagement) would provide mechanistic insight into transcriptional regulation. A null result (no interpretable features explain cell-type differences) would be equally informative, suggesting CTCF selection depends on factors outside sequence/chromatin context (e.g., 3D genome structure, cooperative binding with other factors). Either outcome advances domain understanding.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (sequence and chromatin features → CTCF binding selectivity) rather than an implementation constraint. While the methodology involves transformers and sparse autoencoders, these are means to answer the biological question, not the question itself.

### Overall verdict

**Verdict**: validated

All four checks pass. The research question targets a substantive biological mechanism (CTCF site selection determinants) using interpretability methods as tools rather than as the object of study. The measurement modalities are independent, and either positive or null results would be informative for the field. The project can proceed to initialization.

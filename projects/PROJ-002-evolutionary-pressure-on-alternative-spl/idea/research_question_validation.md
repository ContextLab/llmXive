## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a biological relationship between transcriptomic divergence (alternative splicing) and genomic signatures of selection on regulatory elements, independent of any specific ML method or computational constraint. The methodology (STAR, SUPPA2, PAML) serves to answer the question but is not itself the question being tested.

### Circularity check

**Verdict**: pass

The predictor (alternative splicing divergence) is derived from RNA-seq data measuring transcript abundance and junction usage. The predicted variable (positive selection on regulatory elements) is derived from genomic alignments and phyloP conservation scores from UCSC. These are independent measurement modalities—transcriptomic and genomic—computed from different primary data sources.

### Triviality check

**Verdict**: pass

A positive correlation would provide evidence for adaptive evolution driving splicing regulatory changes, supporting the hypothesis that splicing divergence is functionally selected. A null result would suggest splicing divergence is largely neutral drift rather than adaptive, which is also scientifically informative and publishable. Neither outcome is predetermined by existing domain knowledge.

### Question-narrowing check

**Verdict**: pass

The question names a clear domain relationship (splicing divergence ↔ selection pressure on regulatory elements) rather than an implementation constraint. It asks "to what extent" a biological phenomenon exists, not "can method M achieve accuracy X within budget Y."

### Overall verdict

**Verdict**: validated

All four checks pass. The research question is well-formulated as a substantive biological inquiry using independent data modalities, with both positive and null outcomes being scientifically informative. No reframing is necessary.

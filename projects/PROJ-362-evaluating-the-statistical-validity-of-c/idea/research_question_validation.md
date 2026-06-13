## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about the statistical properties of measurement tools (NDCG, MAP) in information retrieval evaluation, specifically their power to distinguish signal from noise. This is a substantive question about metric validity, not about whether a specific algorithm or implementation can perform a task under constraints.

### Circularity check

**Verdict**: pass

The predictor (metric scores on original rankings) and the comparison baseline (metric scores on permuted/shuffled relevance labels) are derived from the same data source but represent distinct conditions: signal vs. null. The relationship is not mechanically guaranteed—some metrics may fail to show significant differences even with shuffled data, which is precisely what the test measures.

### Triviality check

**Verdict**: pass

Either outcome is informative: confirming adequate power would validate current IR evaluation practices, while finding insufficient power would expose widespread risk of spurious claims in published literature. Both results would meaningfully influence evaluation methodology and publication standards in the field.

### Question-narrowing check

**Verdict**: pass

Names a domain relationship (statistical properties of ranking metrics in information retrieval evaluation) rather than an implementation constraint. The question asks about metric behavior under controlled conditions, not whether a specific method can run within a budget or hardware limit.

### Overall verdict

**Verdict**: validated

All four checks pass. The research question addresses a genuine gap in information retrieval methodology by empirically quantifying the statistical power of standard evaluation metrics. The permutation-test methodology is appropriate for this question, and either outcome would produce publishable, field-informing results.

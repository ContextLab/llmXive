## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a biological relationship between specific genetic variants (SNPs in stress-response pathways) and survival phenotypes under thermal stress. It is framed as a genotype-phenotype correlation inquiry independent of any specific computational method's performance, even though PLINK is the tool chosen for analysis.

### Circularity check

**Verdict**: pass

The predictor (SNPs from VCF/FASTQ genomic sequencing data) and predicted variable (survival status from metadata/exposure records) come from independent measurement modalities. Genotypes are derived from DNA sequencing while phenotypes are derived from experimental survival observations, so the relationship is not mechanically guaranteed by construction.

### Triviality check

**Verdict**: pass

A positive result identifying specific resilience markers would enable targeted conservation strategies and inform assisted evolution programs. A null result would be equally informative, suggesting thermal resilience is polygenic or environmentally plastic rather than controlled by simple genetic variants. Both outcomes would contribute meaningfully to the field.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (genotype-phenotype correlation in coral thermal tolerance) rather than an implementation constraint. It does not ask whether a specific method can handle the data within budget limits, but instead asks about a biological mechanism that the method will help uncover.

### Overall verdict

**Verdict**: validated

All four validation checks pass. The research question is well-framed as a substantive scientific inquiry about coral thermal tolerance genetics, with independent data sources for predictors and outcomes, and both positive and null results would be scientifically informative. The project can proceed to initialization.

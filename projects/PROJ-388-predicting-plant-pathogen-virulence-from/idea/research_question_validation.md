## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question asks about a biological relationship between genomic features (virulence genes, TF binding sites, sequence variation) and phenotypic virulence measures (disease severity scores). This is independent of any specific ML method—the correlation analysis is a tool to answer the question, not the question itself.

### Circularity check

**Verdict**: pass

The predictor (genomic features from NCBI genome assemblies) and the predicted variable (disease severity scores from BioProject/OpenML) are independent measurement modalities. Genomic sequence data and phenotypic disease measurements are not derived from the same primary signal.

### Triviality check

**Verdict**: pass

Either outcome is scientifically informative: positive results identify specific genomic markers for breeding programs and functional validation; null results suggest virulence is polygenic or that current public datasets lack phenotypic resolution. The relationship is not predetermined by domain knowledge.

### Question-narrowing check

**Verdict**: pass

The question names a domain relationship (genomic features → phenotypic virulence across isolates) rather than implementation constraints. It asks "what genomic features predict virulence" not "can method M achieve accuracy X within budget Y."

### Overall verdict

**Verdict**: validated

All four checks pass. The research question is well-formulated as a substantive biological inquiry about genomic determinants of virulence, with independent predictor and outcome modalities, and outcomes that would be informative regardless of direction. The project can proceed to initialization.

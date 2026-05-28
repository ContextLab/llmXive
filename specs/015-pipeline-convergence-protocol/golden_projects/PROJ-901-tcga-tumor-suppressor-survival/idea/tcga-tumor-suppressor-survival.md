# Idea — Cross-cancer-type consistency of survival associations for the most-cited tumor-suppressor genes (biology)

Data source: NCI Genomic Data Commons (TCGA open-access mutation + clinical data) (https://portal.gdc.cancer.gov/); publicly accessible under an open-access policy.

Research question: Across the 5 most-cited tumor-suppressor genes (TP53, RB1, PTEN, CDKN2A, BRCA1), how consistent are per-gene overall-survival associations across the 32 TCGA primary-cancer types, and how do the associations depend on tumor stage and somatic-mutation burden?

Hypothesis: TP53-mutation impact on overall survival is negative across most cancer types but loses significance (or reverses) in 3-5 cancer types where TP53 mutations are near-universal (loss of dynamic range); the other 4 genes show cancer-type-specific patterns.

Methods: Pull open-access mutation + clinical data from the NCI Genomic Data Commons; per-gene Kaplan-Meier + Cox proportional-hazards analysis stratified by cancer type; multiple-testing correction via Benjamini-Hochberg.

Feasibility: implementable with free open-source tooling + the publicly-accessible dataset cited above.

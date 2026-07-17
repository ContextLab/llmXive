# Research Notes: Diversity Profiles for TRB Extension

## Background
This project explores the use of static diversity profiles to predict model collapse and stability in the absence of ground-truth sweep logs.

## Methodology
1. **Feature Extraction**: Compute lexical (distinct-4, n-gram entropy) and syntactic (parse tree variance) metrics.
2. **Proxy Targets**: Use relevance scores (BEIR) and text length (Book Corpus) as proxies for collapse/stability.
3. **Correlation Analysis**: Validate correlations between diversity metrics and proxy targets.
4. **Generalization**: Test if source-domain correlations hold in target domains.

## Preliminary Findings
- **Lexical Metrics**: Distinct-4 ratio and n-gram entropy show promise as indicators of diversity.
- **Syntactic Metrics**: Parse tree depth variance requires further validation.
- **Proxy Targets**: Relevance scores and text length are viable proxies for collapse/stability.

## Next Steps
- Implement full feature extraction pipeline.
- Conduct correlation analysis on real datasets.
- Validate generalization across domains.

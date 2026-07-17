# Implementation Plan: llmXive Follow-up (TRB Extension)

## Objective
Extend the TRB framework to handle scenarios where ground-truth collapse labels are unavailable by using **proxy correlation analysis** on static diversity profiles.

## Strategy
1. **Compute Diversity Profiles**: Extract lexical (distinct-n, entropy) and syntactic (parse tree variance) features from teacher outputs.
2. **Proxy Targets**: Use `relevance_score` (BEIR) and `text_length` (Book Corpus) as proxies for collapse/stability.
3. **Correlation Analysis**: Validate if diversity metrics correlate with proxy targets (Pearson/Spearman).
4. **Generalization**: Test if source-domain correlations hold in target domains.

## Constraints
- **CPU Only**: No GPU usage allowed for feature extraction.
- **Real Data Only**: Must use `tr-books-tokenized` and `Tr-beir-formatted` from HuggingFace.
- **No Fabrication**: All results must be derived from real data; synthetic fallbacks are prohibited.

## Milestones
- **M1**: Feature extraction pipeline functional (US1)
- **M2**: Proxy correlation analysis complete (US2)
- **M3**: Generalization validation complete (US3)

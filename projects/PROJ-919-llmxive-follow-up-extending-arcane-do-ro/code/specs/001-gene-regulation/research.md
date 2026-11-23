# Research Background: ArcANE

## Motivation

Evaluating the consistency of character behavior in literature is a complex task often reliant on subjective human judgment. This project aims to automate this process using Large Language Models to generate and evaluate "character arcs".

## Methodology

1. **Axis Definition**: Define psychological traits (Coarse) and specific behavioral observations (Fine) for a character.
2. **Probe Generation**: Create scenarios that are semantically distant from the original text but relevant to the defined axes.
3. **Evaluation**: Use a Judge LLM to score the target model's responses for consistency with the character's defined axes.
4. **Statistical Analysis**: Compare consistency scores across Coarse, Fine, and Hybrid conditions using ANOVA or Friedman tests.

## Data Sources

- **Source Text**: Public domain texts from Project Gutenberg (e.g., *A Christmas Carol*, *Pride and Prejudice*).
- **Gold Standard**: Human-annotated consistency scores for a subset of probes.

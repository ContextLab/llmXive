# Associational Framing Guidelines

## Purpose

This document establishes guidelines for framing all project results, reports, and communications as **associational relationships** rather than causal claims. This ensures scientific rigor and prevents misinterpretation of statistical correlations as physical mechanisms.

## Core Principle

**All findings from this project describe statistical associations, not causal relationships.**

The predictive models identify patterns in the data between cold-rolling reduction and texture descriptors. These patterns reflect observed correlations but do not prove that reduction **causes** specific texture changes. Physical mechanisms (e.g., dislocation slip, twinning) are inferred from crystallographic theory and external literature, not from the models themselves.

## Language Guidelines

### ✅ Use These Phrases

- "associated with"
- "correlated with"
- "predicted by"
- "statistical relationship"
- "observed trend"
- "data suggests"
- "consistent with"
- "aligns with"
- "modeled relationship"
- "empirical association"

### ❌ Avoid These Phrases

- "causes"
- "drives"
- "leads to" (without qualification)
- "mechanism of"
- "due to" (without qualification)
- "results in" (without qualification)
- "determines"
- "forces"
- "induces" (in a causal sense)

## Examples

### Correct Framing

> "The model identifies a **statistical association** between cold-rolling reduction and Brass texture component volume fraction. Higher reductions are **associated with** increased Brass fractions in Aluminum samples."

> "Polynomial regression **predicts** that Goss component intensity **correlates with** reduction levels, consistent with standard FCC texture evolution trends."

> "The observed **relationship** between reduction and Texture Index is **consistent with** established crystallographic theory, though the model does not establish causality."

### Incorrect Framing

> "Cold rolling **causes** an increase in Brass texture components."

> "Reduction **drives** the evolution of Copper and S components."

> "The model **demonstrates** that reduction **determines** texture development."

## Report Structure Guidelines

### 1. Results Sections

- Present model predictions as **associations**.
- Include uncertainty estimates (confidence intervals, standard errors).
- Flag extrapolated predictions with reduced confidence.
- Note any outliers or deviant samples.

### 2. Discussion Sections

- Compare observed associations with **established physical theory** from literature.
- Clearly distinguish between **model predictions** and **physical mechanisms**.
- Acknowledge limitations (missing variables, data quality).
- Avoid over-interpreting statistical significance as physical significance.

### 3. Conclusions

- Summarize **associational findings**.
- Recommend **experimental validation** for causal claims.
- Highlight areas where **further research** is needed to understand mechanisms.

## Model Output Framing

When generating reports or visualizations from model outputs:

### Titles and Captions

- ✅ "Association between Reduction and Brass Volume Fraction"
- ❌ "Effect of Reduction on Brass Volume Fraction"

### Axis Labels

- ✅ "Predicted Brass Fraction (Association)"
- ❌ "Brass Fraction Caused by Reduction"

### Legend Text

- ✅ "Model-predicted trend (associational)"
- ❌ "Causal trend"

## Handling Exceptions and Outliers

When discussing samples that deviate from standard trends:

- ✅ "This sample **deviates from** the typical association, possibly due to unmeasured factors."
- ❌ "This sample **fails to respond** to reduction as expected."

- ✅ "The **observed association** in this case is weaker than average."
- ❌ "Reduction **failed to cause** the expected texture change."

## Integration with Physics Checks

The `code/analysis/physics_check.py` module validates that observed trends align with known physics (T029). When reporting these checks:

- ✅ "The observed **association** between reduction and Brass fraction **aligns with** expected FCC texture evolution."
- ❌ "The model **confirms** that reduction **causes** Brass texture development."

- ✅ "Trend validation **supports** the physical plausibility of the **statistical relationship**."
- ❌ "Trend validation **proves** the causal mechanism."

## Communication with Stakeholders

When discussing results with non-technical stakeholders:

1. **Emphasize Predictive Utility**: "The model can **predict** texture trends based on reduction levels."
2. **Clarify Limitations**: "These are **statistical patterns**, not proven physical laws."
3. **Avoid Over-Promise**: "The model **associates** reduction with texture changes; the underlying **mechanisms** require further study."

## Documentation Requirements

All project documentation must include:

1. **Explicit Statement**: A clear declaration that findings are associational.
2. **Limitations Section**: Discussion of missing variables and data constraints.
3. **Framing Examples**: Illustrative examples of correct vs. incorrect language.
4. **Reference to Guidelines**: This document should be cited in all reports.

## Review Checklist

Before publishing any report or presentation:

- [ ] All claims use associational language (no causal verbs).
- [ ] Uncertainty and limitations are clearly stated.
- [ ] Physical mechanisms are attributed to literature/theory, not the model.
- [ ] Extrapolated predictions are flagged.
- [ ] Outliers are discussed as deviations, not failures.
- [ ] The "Associational Framing Guidelines" document is referenced.

## Enforcement

- **Code Comments**: All model output functions include comments reinforcing associational framing.
- **Automated Checks**: Future versions may include text analysis to flag causal language in generated reports.
- **Peer Review**: All reports must be reviewed against these guidelines before release.

---
*Adherence to these guidelines is mandatory for all project communications to maintain scientific integrity and prevent misinterpretation.*

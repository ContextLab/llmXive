# Study Protocol: Mindfulness Interventions for ASD Social Skills

## Protocol Version
1.0 (Initial)

## Registration
This protocol is registered on the Open Science Framework (OSF) prior to data
extraction to ensure transparency and prevent outcome reporting bias.

## Objectives
1. Estimate the overall efficacy of mindfulness-based interventions for social
 skill improvement in children aged 6-12 with ASD.
2. Examine whether efficacy varies by mindfulness component (breathing, body scan,
 mindful movement).
3. Examine whether efficacy varies by delivery format (individual, group, parent-mediated).
4. Assess heterogeneity and explore potential moderators.

## Search Strategy
- **Databases**: ClinicalTrials.gov, Open Science Framework (OSF)
- **Search Terms**: "mindfulness", "autism", "ASD", "social skills", "intervention"
- **Date Range**: All available records up to analysis date
- **Language**: English only (due to resource constraints)

## Eligibility Criteria
- **Population**: Children aged 6-12 with ASD diagnosis
- **Intervention**: Mindfulness-based (any component)
- **Comparator**: Waitlist, TAU, or active control
- **Outcome**: Validated social skill measure
- **Design**: RCT or quasi-experimental with control group

## Data Extraction
- **Variables**: Study ID, sample size, intervention details, outcome means/SDs,
 follow-up duration, registry source
- **Process**: Dual extraction (if feasible) or single extraction with verification
- **Software**: Custom Python pipeline (code/data/extractor.py)

## Quality Assessment
- **Risk of Bias**: Cochrane RoB 2.0 tool (adapted for registry data)
- **Domains**: Randomization, blinding, incomplete outcome data, selective reporting
- **Application**: Used as sensitivity analysis, not exclusion criterion

## Statistical Analysis
- **Effect Size**: Hedges' g with small-sample correction
- **Model**: Random-effects (if I² > 50%) or fixed-effects
- **Heterogeneity**: I², Q statistic, p-value
- **Subgroup Analysis**: By component, format, domain
- **Publication Bias**: Funnel plot, Egger's test (N ≥ 10 only)

## Ethical Considerations
- **IRB Status**: Exempt (secondary analysis of de-identified public data)
- **Data Privacy**: No identifiable information collected
- **Compliance**: Constitution Principle III (Ethical Compliance)

## Limitations
- Abstract-only extraction may miss methodological details
- Limited to English-language studies
- Potential for small-study effects
- Heterogeneity in outcome measures

## Dissemination
- Results will be published in a peer-reviewed journal
- Data and code will be shared on OSF (per Constitution Principle II)
- Findings will inform clinical practice and future research

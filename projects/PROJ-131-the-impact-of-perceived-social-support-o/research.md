# Research Notes: The Impact of Perceived Social Support on Resilience to Online Harassment

## Methodology and Data Strategy

### Single-Dataset Approach
This research project adopts a **single-dataset approach** using the **Cyberbullying Survey 2021** as the sole data source. This decision was made after a methodological review (see `specs/001-social-support-resilience/spec.md` and `plan.md`) to ensure the validity of the interaction analysis between perceived social support and harassment exposure.

### Exclusion of GSS 2022 Dataset
The **General Social Survey (GSS) 2022** dataset has been explicitly **excluded** from this analysis for the following reasons:

1. **Methodological Invalidity for Interaction Analysis**: Combining the GSS 2022 with the Cyberbullying Survey 2021 would introduce severe confounding. In a two-dataset design, "Dataset Source" would be perfectly collinear with "Harassment Exposure" (as GSS respondents are not sampled for online harassment exposure in the same manner as the Cyberbullying Survey). This makes it statistically impossible to disentangle the effect of social support on resilience from the effect of the dataset source itself.

2. **Lack of Verified PCL-5 Items**: The GSS 2022 does not contain the full set of items required to calculate the PTSD Checklist for DSM-5 (PCL-5) scores, which is a key outcome variable in this study. The Cyberbullying Survey 2021 includes the necessary items to derive valid PCL-5 scores.

3. **Harmonization Impossibility**: The measurement scales for "Perceived Social Support" and "Harassment Severity" differ significantly between the two surveys. Harmonizing these constructs without introducing measurement error is not feasible.

### Reference
For the full methodological justification, refer to the "Methodological Rationale" section in `specs/001-social-support-resilience/plan.md`.

## Analysis Plan
The analysis will proceed with the Cyberbullying Survey 2021 data only, focusing on:
- The main effect of harassment exposure on mental health outcomes (Depression, Anxiety, PTSD).
- The moderating effect of perceived social support on the relationship between harassment and mental health.
- Sensitivity analyses using continuous harassment severity and platform stratification.

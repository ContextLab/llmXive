---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Traffic Accident Data

**Field**: statistics

## Research question

How do specific weather conditions (precipitation, visibility, temperature) statistically influence traffic accident severity (property damage, injury, fatality) after controlling for temporal and infrastructural variables?

## Motivation

Understanding weather-severity correlations allows for targeted safety interventions and resource allocation for emergency services. While much recent work focuses on automated accident detection or regional policy, there is a gap in rigorous statistical modeling quantifying environmental risk factors using public municipal data.

## Related work

- [Statistical and Multivariate Analysis of the IoT-23 Dataset: A Comprehensive Approach to Network Traffic Pattern Discovery (2025)](https://www.semanticscholar.org/paper/d4d4cc113ae5fe1c09353fb0825b14a162e292d2) — Demonstrates multivariate analysis techniques applicable to complex traffic datasets, though focused on network rather than road traffic.
- [Review On Development Of An Accident Detection System Utilizing Traffic Imaging And Machine Learning Techniques (2025)](https://www.semanticscholar.org/paper/5e89ce270299ab06fc5bff7f209fad2b3541321b) — Highlights the prevalence of machine learning in accident analysis, contrasting with this project's focus on interpretable statistical modeling.
- [Spatiotemporal analysis of traffic accidents hotspots using Twitter data: the case of Quezon City (2024)](https://www.semanticscholar.org/paper/b52ba559fa1da5d133a771ae4f0a277f64ffaede) — Illustrates the use of public, non-traditional data sources for mapping accident hotspots in urban environments.
- [Development of an Approach to Analysing Regional Road Traffic Accident Rates (2024)](https://www.semanticscholar.org/paper/d028eadecfec859e890add02e1d72407389e1087) — Provides a framework for long-term statistical review of accident rates over a decade, similar to the temporal scope planned here.
- [Big Data Analytics on Road Traffic Accidents in India: A Critical Statistical Review on Safety Measures and Awareness on Accidents (2024)](https://www.semanticscholar.org/paper/1ab3be60c50ed7d1e039a9867aee1adbfd7eb8a6) — Offers a critical statistical review of safety measures, reinforcing the need for data-driven awareness campaigns.
- [Expected effects of accident data recording technology evolution on the identification of accident causes and liability (2023)](https://www.semanticscholar.org/paper/a3be4798254a03ab9feabd7ac01b12e670eb9240) — Discusses how data quality and recording methods impact cause identification, relevant to handling missing weather variables.
- [Analysis of the Implementation of the General National Safety Plan (RUNK) Policy on National Road Traffic in East Java Province (2026)](https://www.semanticscholar.org/paper/0a9025a52faea3727b2b26b65e86855178117ff8) — Analyzes policy effectiveness using accident data, demonstrating the link between statistical findings and safety planning.
- [A Modular Zero-Shot Pipeline for Accident Detection, Localization, and Classification in Traffic Surveillance Video (2026)](http://arxiv.org/abs/2604.09685v1) — Represents state-of-the-art computer vision approaches to classification, serving as a contrast to regression-based severity analysis.

## Expected results

The analysis is expected to identify precipitation and low visibility as statistically significant predictors of increased injury/fatality severity compared to property damage. Coefficients from the generalized linear model will quantify the risk increase (odds ratios), providing evidence sufficient to inform local safety campaigns.

## Methodology sketch

- Download the US Fatality Analysis Reporting System (FARS) dataset (public CSV) via `wget` from NHTSA.
- Download corresponding historical weather data (NOAA GHCN-Daily) for accident locations and times.
- Clean and merge datasets using Python (pandas), filtering for records with complete weather and severity fields.
- Encode accident severity as an ordinal variable (0=Property, 1=Injury, 2=Fatality).
- Fit an Ordinal Logistic Regression model (GLM) using `statsmodels` on the 7GB RAM runner.
- Include control variables: hour of day, day of week, road type, and vehicle type.
- Perform model diagnostics (VIF for multicollinearity, Hosmer-Lemeshow test for fit).
- Generate coefficient plots and odds ratio tables to visualize weather impact.
- Ensure all scripts run within a single 6-hour GitHub Actions job by processing data in chunks if necessary.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: No exact match found in literature or session context.
- Verdict: NOT a duplicate

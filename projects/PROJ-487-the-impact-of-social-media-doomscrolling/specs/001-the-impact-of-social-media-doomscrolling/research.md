# Research Document: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Summary

This research investigates the relationship between aggregate negative news publication volume and anticipatory anxiety levels in the general population. The study aims to determine if there is a statistically significant correlation between the volume of negative news events and search trends related to anxiety, with a specific focus on the impact of social media doomscrolling behaviors.

## Technical Context

The analysis utilizes time-series data from two primary sources: the GDELT 2.0 Event Database for negative news publication volume and Google Trends for anxiety-related search queries. The methodology involves:

1. **Data Acquisition**: Retrieving historical time-series data for aggregate negative news publication volume from GDELT and anxiety-related search trends from Google Trends for the period 2020-01-01 to 2023-12-31.

2. **Preprocessing**: Cleaning, normalizing, and aligning the retrieved time-series data to daily resolution, ensuring stationarity through differencing and z-score normalization.

3. **Statistical Analysis**: Computing Pearson and Spearman correlation coefficients, performing Granger causality tests with a fixed lag window of {1, 2, 3, 7, 14} days, and conducting sensitivity analysis with Bonferroni correction (α=0.05/5=0.01).

4. **Reporting**: Generating statistical validity reports and final analysis PDFs that document the findings, including proxy acknowledgments and causality disclaimers.

The project adheres to strict CPU feasibility constraints (2-core CPU, ≤7GB RAM, ≤6h runtime) and requires all data to be sourced from real, programmatically-accessible sources (GDELT API, Google Trends via pytrends). No synthetic data generation is permitted.
# Specification: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## User Stories

### US1: Data Acquisition and Preprocessing
As a researcher, I want to download and preprocess resting-state fMRI data from OpenNeuro ds004285 so that I can extract BOLD time series for network analysis.

### US2: Network Topology Metric Computation
As a researcher, I want to compute functional connectivity matrices and derive five graph theory metrics (modularity, path length, clustering, efficiency, small-worldness) so that I can quantify the topological properties of brain networks.

### US3: Correlation Analysis and Statistical Reporting
As a researcher, I want to correlate topology metrics with illusion scores and apply FDR correction so that I can identify significant associations between network structure and behavioral susceptibility.

### US4: Behavioral Data Extraction
As a researcher, I want to extract existing visual illusion susceptibility scores from the OpenNeuro dataset and link them to Subject IDs so that I can perform correlational analysis.

## Data Model
- **Subject**: Unique identifier, demographic info.
- **ConnectivityMatrix**: T x N matrix of BOLD correlations.
- **TopologyMetrics**: JSON object with modularity, path length, clustering, efficiency, small-worldness.
- **IllusionScore**: Müller-Lyer and Ponzo error magnitudes.

## Constraints
- Use real data only (OpenNeuro ds004285).
- All analyses must be reproducible (fixed seeds, versioned code).
- Exclusion criteria: Motion (FD > 0.5mm), missing data.
- Report findings as "associational" only.

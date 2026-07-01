# PROJ-450: Predicting Species-Specific Responses to Climate Change

## Overview
This project analyzes museum collection data to predict species-specific responses to climate change,
focusing on niche shifts and regional warming correlations.

## Project Structure
- `code/`: R scripts for data fetching, processing, analysis, and visualization
- `data/`:
 - `raw/`: Raw data from GBIF and WorldClim
 - `processed/`: Cleaned and aggregated data
 - `interim/`: Intermediate data files
- `results/`: Final analysis outputs, reports, and statistical summaries
- `figures/`: Publication-quality plots and visualizations
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Setup
1. Ensure R 4.3+ is installed.
2. Install dependencies:
 ```r
 install.packages(c("rgbif", "raster", "sf", "ggplot2", "dplyr", "tidyr",
 "caper", "phylolm", "pwr", "tibble", "lubridate", "here", "testthat"))
 ```
3. Run the setup script to initialize directory structure:
 ```r
 Rscript code/setup_project_structure.R
 ```

## Execution
Follow the tasks in `tasks.md` to implement the pipeline incrementally.
Start with Phase 1 (Setup) and Phase 2 (Foundational) before proceeding to user stories.

## Data Sources
- GBIF (Global Biodiversity Information Facility) for occurrence records
- WorldClim v2 for climate data (1970-2000 and 1991-2020)

## License
MIT License
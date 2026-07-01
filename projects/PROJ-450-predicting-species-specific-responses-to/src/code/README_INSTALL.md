# R Project Setup Instructions

## Prerequisites
- R version 4.3.0 or higher
- Internet connection (for downloading packages)

## Initialization Steps

1. **Navigate to the project root**:
 ```bash
 cd /path/to/project
 ```

2. **Run the installation script**:
 ```bash
 Rscript src/code/install_deps.R
 ```
 This will:
 - Initialize `renv` in the project root.
 - Install all required dependencies listed in `install_deps.R`.
 - Generate `renv.lock` for reproducibility.

3. **Configure the environment**:
 The `.Rprofile` file in `src/code/` is configured to set `stringsAsFactors = FALSE` and initialize the `here` package context.
 To use this configuration in an interactive session:
 ```R
 # Option A: Start R from the project root
 R
 # The.Rprofile in src/code will not auto-load unless src/code is the working directory.
 # Recommended: Source it explicitly or move the logic to the project root.Rprofile.
 source("src/code/.Rprofile")

 # Option B: Set the working directory to src/code before starting R
 setwd("src/code")
 R
 ```

## Dependencies Installed
- `rgbif`: GBIF occurrence data
- `raster`: Raster data handling
- `sf`: Spatial vector data
- `ggplot2`: Visualization
- `dplyr`, `tidyr`, `tibble`: Data manipulation
- `caper`, `phylolm`: Phylogenetic comparative methods
- `pwr`: Power analysis
- `lubridate`: Date handling
- `here`: Project root path resolution
- `testthat`: Testing framework

## Verification
After running the script, verify the environment:
```R
library(rgbif)
library(ggplot2)
library(phylolm)
# Check if renv is active
renv::status()
```

## Notes
- If you encounter SSL errors when installing packages, ensure your system's CA certificates are up to date.
- The `here` package assumes the project root is the directory containing `renv.lock`.
- For T003, the `.Rprofile` settings are applied when sourcing the file or when R is started in the `src/code` directory.

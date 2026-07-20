#!/usr/bin/env Rscript
# T044: Data Acquisition Strategy & Execution
# Implements logic to fetch real data or generate a structured data request template.
#
# Usage: Rscript code/04_fetch_data.R
# Note: This script is OPTIONAL/Manual. It does not run in CI unless data is present.

# Load required libraries
if (!requireNamespace("yaml", quietly = TRUE)) {
  stop("Package 'yaml' is required. Please install it via renv: renv::install('yaml')")
}
library(yaml)

# Define paths
project_root <- getwd()
raw_data_dir <- file.path(project_root, "data", "raw")
raw_data_file <- file.path(raw_data_dir, "study_data.csv")
config_file <- file.path(raw_data_dir, "data_source_config.yaml")
readme_template <- file.path(raw_data_dir, "README_DATA_NEEDED.md")

# Required columns per FR-001
required_cols <- c(
  "MEQ_score", 
  "MFQ_care", "MFQ_fairness", "MFQ_loyalty", "MFQ_authority", "MFQ_sanctity",
  "PSQI", "age", "sex", "acute_sleepiness"
)

# Helper: Check if data exists
data_exists <- file.exists(raw_data_file)

if (data_exists) {
  message("Found existing data file: ", raw_data_file)
  
  # Validate columns
  tryCatch({
    df <- read.csv(raw_data_file, stringsAsFactors = FALSE, nrows = 1)
    missing_cols <- setdiff(required_cols, names(df))
    
    if (length(missing_cols) > 0) {
      warning("Data file exists but is missing required columns: ", 
              paste(missing_cols, collapse = ", "))
      message("Please update the data file or provide a valid source.")
      quit(status = 1)
    } else {
      message("Data validation passed: All required columns present.")
      quit(status = 0)
    }
  }, error = function(e) {
    message("Error reading data file: ", e$message)
    quit(status = 1)
  })
} else {
  message("No data file found at: ", raw_data_file)
  message("Checking for data source configuration...")
  
  if (file.exists(config_file)) {
    message("Configuration file found: ", config_file)
    tryCatch({
      config <- read_yaml(config_file)
      source_type <- config$source_type
      source_id <- config$source_id
      access_method <- config$access_method
      
      message("Attempting to fetch data from: ", source_id, " (Type: ", source_type, ")")
      
      if (source_type == "url" && access_method == "download") {
        if (is.null(source_id) || source_id == "") {
          stop("Configuration error: 'source_id' (URL) is missing in config file.")
        }
        
        # Attempt download
        temp_file <- tempfile(fileext = ".csv")
        tryCatch({
          download.file(url = source_id, destfile = temp_file, mode = "wb")
          
          # Validate downloaded file
          df <- read.csv(temp_file, stringsAsFactors = FALSE, nrows = 1)
          missing_cols <- setdiff(required_cols, names(df))
          
          if (length(missing_cols) > 0) {
            stop("Downloaded data missing columns: ", paste(missing_cols, collapse = ", "))
          }
          
          # Move to final location
          dir.create(raw_data_dir, recursive = TRUE, showWarnings = FALSE)
          file.copy(temp_file, raw_data_file, overwrite = TRUE)
          unlink(temp_file)
          
          message("Successfully downloaded and validated data.")
          quit(status = 0)
          
        }, error = function(e) {
          unlink(temp_file)
          stop("Download failed: ", e$message)
        })
        
      } else {
        stop("Unsupported source_type or access_method in config. 
             Supported: source_type='url', access_method='download'.")
      }
      
    }, error = function(e) {
      message("Error reading or processing config file: ", e$message)
      message("Falling back to generating Data Request Template.")
    })
  } else {
    message("No configuration file found.")
  }
  
  # Fallback: Generate Data Request Template
  message("Generating Data Request Template: ", readme_template)
  
  readme_content <- paste0(
    "# Data Acquisition Required\n\n",
    "## Status\n",
    "The pipeline requires a specific merged CSV file to proceed. No public dataset currently contains all required variables.\n\n",
    "## Required Columns\n",
    "The file `data/raw/study_data.csv` must contain the following columns:\n",
    paste0("- `", required_cols, "`\n", collapse = ""),
    "\n",
    "## Why this is needed\n",
    "No single public dataset contains the combination of MEQ (Morningness-Eveningness Questionnaire), \n",
    "MFQ (Moral Foundations Questionnaire), PSQI (Pittsburgh Sleep Quality Index), and Acute Sleepiness \n",
    "measures alongside demographic data required for this analysis.\n\n",
    "## How to proceed\n",
    "1. **Contact your data source**: If you collected this data via Prolific, Qualtrics, or a lab study, \n",
    "   merge the responses into a single CSV.\n",
    "2. **Manual Merge**: If you have separate datasets (e.g., OSF for MFQ, local logs for MEQ), \n",
    "   perform a join on participant ID and export to `data/raw/study_data.csv`.\n",
    "3. **Template**: Use `data/raw/template_data.csv` as a schema reference.\n\n",
    "## Template Configuration\n",
    "If you wish to automate fetching, create `data/raw/data_source_config.yaml` with:\n",
    "```yaml\n",
    "source_type: url\n",
    "source_id: \"https://example.com/your_dataset.csv\"\n",
    "access_method: download\n",
    "```\n",
    "Then re-run `code/04_fetch_data.R`.\n"
  )
  
  writeLines(readme_content, readme_template)
  
  # Also create a template CSV with headers only
  template_path <- file.path(raw_data_dir, "template_data.csv")
  template_df <- data.frame(matrix(ncol = length(required_cols), nrow = 0))
  colnames(template_df) <- required_cols
  write.csv(template_df, template_path, row.names = FALSE)
  message("Created template file: ", template_path)
  
  message("Data acquisition failed. Please provide data manually as described in ", readme_template)
  quit(status = 1)
}
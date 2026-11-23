# code/08_low_balance_alert.R
# Task: T036 - Low Balance Alert
# Description: Read classified data, check proportion of intermediate chronotype,
#              and generate a warning file if > 70%.

library(dplyr)
library(readr)
library(jsonlite)

# Source configuration
source("code/00_config.R")

main <- function() {
  # Define paths
  input_file <- file.path(PROCESSED_DATA_DIR, "classified_data.csv")
  alert_file <- file.path(DERIVED_DATA_DIR, "low_balance_alert.txt")
  
  # Check if input file exists
  if (!file.exists(input_file)) {
    stop("Input file not found: ", input_file)
  }
  
  # Load data
  cat("Loading classified data from:", input_file, "\n")
  data <- tryCatch({
    read_csv(input_file)
  }, error = function(e) {
    stop("Failed to load data: ", e$message)
  })
  
  # Verify required column exists
  if (!"chronotype" %in% names(data)) {
    stop("Missing 'chronotype' column in input data.")
  }
  
  # Calculate proportions
  total_n <- nrow(data)
  intermediate_n <- sum(data$chronotype == "intermediate", na.rm = TRUE)
  intermediate_prop <- intermediate_n / total_n
  
  cat("Total participants:", total_n, "\n")
  cat("Intermediate chronotype count:", intermediate_n, "\n")
  cat("Intermediate proportion:", round(intermediate_prop, 3), "\n")
  
  # Check threshold
  threshold <- 0.70
  if (intermediate_prop > threshold) {
    alert_msg <- paste0(
      "WARNING: Low Group Balance Detected\n",
      "----------------------------------\n",
      "The proportion of participants in the 'intermediate' chronotype group is ",
      round(intermediate_prop * 100, 1), "% (", intermediate_n, "/", total_n, ").\n",
      "This exceeds the 70% threshold.\n",
      "\n",
      "RECOMMENDATION:\n",
      "Future recruitment should aim to include more participants with extreme\n",
      "chronotypes (morning or evening) to improve the statistical power and\n",
      "generalizability of the analysis.\n",
      "\n",
      "This warning has been flagged for inclusion in the final report."
    )
    
    # Write alert file
    writeLines(alert_msg, alert_file)
    cat("Alert file generated:", alert_file, "\n")
    cat(alert_msg, "\n")
  } else {
    cat("Group balance is acceptable. No alert generated.\n")
    # Ensure alert file does not exist if balance is OK
    if (file.exists(alert_file)) {
      file.remove(alert_file)
    }
  }
  
  return(invisible(NULL))
}

# Execute if run directly
if (!interactive()) {
  main()
}

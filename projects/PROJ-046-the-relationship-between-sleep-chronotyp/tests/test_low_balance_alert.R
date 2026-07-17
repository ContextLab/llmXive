# tests/test_low_balance_alert.R
# Unit tests for code/08_low_balance_alert.R
#
# Tests:
# 1. Correctly identifies high intermediate proportion (>70%) and creates alert file.
# 2. Correctly identifies low intermediate proportion (<=70%) and does NOT create alert file.
# 3. Handles missing input file gracefully.
# 4. Handles empty dataset gracefully.

library(testthat)
library(dplyr)
library(readr)
library(jsonlite)

# Helper to run the R script
run_alert_script <- function(input_data, temp_dir) {
  input_file <- file.path(temp_dir, "classified_data.csv")
  alert_file <- file.path(temp_dir, "low_balance_alert.txt")
  log_file <- file.path(temp_dir, "low_balance_alert.log")

  # Write test data
  write_csv(input_data, input_file)

  # Prepare command to run the script
  # We need to set the working directory to the project root or adjust paths in the script
  # For simplicity in unit tests, we assume the script is run from the project root
  # and the temp_dir is the data/derived directory.
  # However, the script uses relative paths based on getwd().
  # To simulate this, we will create a temporary project structure.

  # Create a minimal project structure for the test
  proj_root <- temp_dir
  code_dir <- file.path(proj_root, "code")
  data_dir <- file.path(proj_root, "data", "derived")
  log_dir <- file.path(proj_root, "logs")

  dir.create(code_dir, recursive = TRUE)
  dir.create(data_dir, recursive = TRUE)
  dir.create(log_dir, recursive = TRUE)

  # Copy the script to the temp code dir (or just run it directly if paths are absolute)
  # The script uses relative paths from getwd(), so we change directory to proj_root
  script_path <- file.path(code_dir, "08_low_balance_alert.R")
  file.copy("code/08_low_balance_alert.R", script_path)

  # Run the script
  result <- tryCatch({
    system2("Rscript", args = c(script_path), 
            stdout = TRUE, stderr = TRUE, 
            wd = proj_root)
  }, error = function(e) {
    return(list(status = 1, output = e$message))
  })

  return(list(
    status = result$status,
    output = result$output,
    alert_exists = file.exists(file.path(data_dir, "low_balance_alert.txt")),
    log_content = if (file.exists(file.path(log_dir, "low_balance_alert.log"))) {
      readLines(file.path(log_dir, "low_balance_alert.log"))
    } else {
      NULL
    }
  ))
}

test_that("High intermediate proportion triggers alert", {
  temp_dir <- tempfile()
  on.exit(unlink(temp_dir, recursive = TRUE))

  # Create data with >70% intermediate
  test_data <- data.frame(
    chronotype = c(rep("intermediate", 80), rep("morning", 10), rep("evening", 10)),
    stringsAsFactors = FALSE
  )

  result <- run_alert_script(test_data, temp_dir)

  expect_true(result$alert_exists, info = "Alert file should be created for >70% intermediate")
  expect_true(any(grepl("LOW BALANCE ALERT", result$log_content)), info = "Log should contain alert message")
})

test_that("Low intermediate proportion does not trigger alert", {
  temp_dir <- tempfile()
  on.exit(unlink(temp_dir, recursive = TRUE))

  # Create data with <=70% intermediate (e.g., 50%)
  test_data <- data.frame(
    chronotype = c(rep("intermediate", 50), rep("morning", 25), rep("evening", 25)),
    stringsAsFactors = FALSE
  )

  result <- run_alert_script(test_data, temp_dir)

  expect_false(result$alert_exists, info = "Alert file should NOT be created for <=70% intermediate")
  expect_true(any(grepl("Balance check passed", result$log_content)), info = "Log should indicate passed check")
})

test_that("Missing input file raises error", {
  temp_dir <- tempfile()
  on.exit(unlink(temp_dir, recursive = TRUE))

  # Do not create input file
  result <- run_alert_script(data.frame(), temp_dir) # Pass empty data, script will fail to find file

  expect_equal(result$status, 1, info = "Script should exit with error code")
  expect_true(any(grepl("ERROR", result$output)), info = "Output should contain error message")
})

test_that("Empty dataset raises error", {
  temp_dir <- tempfile()
  on.exit(unlink(temp_dir, recursive = TRUE))

  # Create empty data frame
  test_data <- data.frame(chronotype = character(0))

  result <- run_alert_script(test_data, temp_dir)

  expect_equal(result$status, 1, info = "Script should exit with error code for empty dataset")
})
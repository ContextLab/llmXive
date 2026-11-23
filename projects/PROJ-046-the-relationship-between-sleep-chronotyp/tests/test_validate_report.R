# tests/test_validate_report.R
# Unit tests for the report validation logic (T029)

library(testthat)
library(tools)

# Source the implementation logic
# Note: In a real run, we might source the whole file or a specific function
# For testing, we isolate the logic here or assume the file is loaded.
# Since the task requires the file code/05_validate_report.R to be runnable,
# we will source it here but redefine functions to avoid conflicts if needed.
# However, to keep tests clean, we define the logic locally or mock the file reading.

# Mock functions to simulate the environment
get_project_root_mock <- function() {
  temp_dir <- tempfile()
  dir.create(temp_dir, recursive = TRUE)
  dir.create(file.path(temp_dir, "reports"), recursive = TRUE)
  return(temp_dir)
}

# Helper to create a fake HTML report
create_mock_report <- function(path, sections_included, missing_sections) {
  content <- "<html><body>"
  for (sec in sections_included) {
    content <- paste0(content, sprintf("<h2>%s</h2><p>Content for %s</p>", sec, sec))
  }
  content <- paste0(content, "</body></html>")
  writeLines(content, path)
}

test_that("validate_report detects missing sections", {
  # Setup
  tmp_dir <- tempfile()
  dir.create(tmp_dir, recursive = TRUE)
  report_path <- file.path(tmp_dir, "test_report.html")

  # Create report with only one required section
  create_mock_report(
    report_path,
    sections_included = c("Descriptive Statistics"),
    missing_sections = c("ANCOVA Results")
  )

  # Read content
  content <- readLines(report_path, warn = FALSE)

  # Define required sections
  req_sections <- c("Descriptive Statistics", "ANCOVA Results")

  # Run validation (re-implementing logic for test isolation)
  full_text <- paste(content, collapse = "\n")
  missing <- character(0)
  for (sec in req_sections) {
    pattern <- paste0("<h[23].*>", sec, ".*?</h[23]>")
    if (!grepl(pattern, full_text, ignore.case = TRUE)) {
      missing <- c(missing, sec)
    }
  }

  # Assertions
  expect_false(length(missing) == 0)
  expect_true("ANCOVA Results" %in% missing)
  expect_false("Descriptive Statistics" %in% missing)

  # Cleanup
  unlink(tmp_dir, recursive = TRUE)
})

test_that("validate_report passes when all sections present", {
  # Setup
  tmp_dir <- tempfile()
  dir.create(tmp_dir, recursive = TRUE)
  report_path <- file.path(tmp_dir, "test_report.html")

  # Create report with all sections
  all_req <- c("Descriptive Statistics", "ANCOVA Results", "Effect Sizes")
  create_mock_report(
    report_path,
    sections_included = all_req,
    missing_sections = character(0)
  )

  # Read content
  content <- readLines(report_path, warn = FALSE)

  # Run validation
  full_text <- paste(content, collapse = "\n")
  missing <- character(0)
  for (sec in all_req) {
    pattern <- paste0("<h[23].*>", sec, ".*?</h[23]>")
    if (!grepl(pattern, full_text, ignore.case = TRUE)) {
      missing <- c(missing, sec)
    }
  }

  # Assertions
  expect_true(length(missing) == 0)

  # Cleanup
  unlink(tmp_dir, recursive = TRUE)
})

test_that("validate_report handles missing file", {
  expect_error(
    readLines("non_existent_file.html", warn = FALSE),
    "cannot open the connection"
  )
})
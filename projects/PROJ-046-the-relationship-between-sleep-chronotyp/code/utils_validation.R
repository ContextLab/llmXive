#' Base Data Validation Utilities
#'
#' This module provides core validation functions used across the pipeline
#' to ensure data integrity, column presence, and value ranges.
#'
#' @importFrom dplyr filter select mutate
#' @importFrom tidyr pivot_longer
#' @importFrom lubridate ymd
#' @importFrom stats na.omit sd var

# Ensure required packages are available
if (!require("tidyverse", quietly = TRUE)) {
  stop("Package 'tidyverse' is required but not installed.")
}
if (!require("lme4", quietly = TRUE)) {
  stop("Package 'lme4' is required but not installed.")
}

# Constants for validation
VALID_CHRONOTYPE_LABELS <- c("morning", "intermediate", "evening")
MEQ_MIN <- 0
MEQ_MAX <- 72
MFQ_MIN <- 0
MFQ_MAX <- 25  # Typical max per subscale, adjusted if specific scale differs

# ---------------------------------------------------------------------------
# Validation: Column Presence
# ---------------------------------------------------------------------------

#' Check for required columns in a data frame
#'
#' @param df A data frame to validate.
#' @param required_cols A character vector of required column names.
#' @param abort_if_missing Logical. If TRUE, stops execution with an error.
#' @return A logical vector indicating which columns are missing.
check_columns <- function(df, required_cols, abort_if_missing = TRUE) {
  if (!is.data.frame(df)) {
    stop("Input 'df' must be a data frame.")
  }

  existing_cols <- colnames(df)
  missing_cols <- setdiff(required_cols, existing_cols)

  if (length(missing_cols) > 0) {
    msg <- sprintf("Missing required columns: %s", paste(missing_cols, collapse = ", "))
    if (abort_if_missing) {
      stop(msg, call. = FALSE)
    } else {
      warning(msg)
    }
  }
  return(missing_cols)
}

# ---------------------------------------------------------------------------
# Validation: Value Ranges
# ---------------------------------------------------------------------------

#' Validate numeric columns are within expected bounds
#'
#' @param df A data frame.
#' @param col_name The column name to check.
#' @param min_val Minimum allowed value.
#' @param max_val Maximum allowed value.
#' @param allow_na Logical. If TRUE, NA values are ignored for range checking.
#' @return A logical vector (TRUE if valid, FALSE if out of range or non-numeric).
validate_range <- function(df, col_name, min_val, max_val, allow_na = TRUE) {
  if (!col_name %in% colnames(df)) {
    stop(sprintf("Column '%s' not found in data frame.", col_name))
  }

  col_data <- df[[col_name]]

  # Check if numeric
  if (!is.numeric(col_data)) {
    return(rep(FALSE, length(col_data)))
  }

  if (allow_na) {
    valid <- !is.na(col_data) & (col_data >= min_val) & (col_data <= max_val)
  } else {
    valid <- (col_data >= min_val) & (col_data <= max_val)
  }
  return(valid)
}

#' Validate MEQ score specifically
#'
#' @param df A data frame.
#' @return A logical vector indicating valid MEQ scores.
validate_meq <- function(df) {
  validate_range(df, "MEQ_score", MEQ_MIN, MEQ_MAX)
}

# ---------------------------------------------------------------------------
# Validation: Chronotype Labels
# ---------------------------------------------------------------------------

#' Validate chronotype classification labels
#'
#' @param df A data frame containing a 'chronotype' column.
#' @return A logical vector indicating valid labels.
validate_chronotype_labels <- function(df) {
  if (!"chronotype" %in% colnames(df)) {
    return(rep(FALSE, nrow(df)))
  }
  return(df$chronotype %in% VALID_CHRONOTYPE_LABELS)
}

# ---------------------------------------------------------------------------
# Validation: Missing Data Patterns
# ---------------------------------------------------------------------------

#' Count missing values in specific columns
#'
#' @param df A data frame.
#' @param cols Vector of column names to check.
#' @return A named integer vector of missing counts.
count_missing <- function(df, cols) {
  if (!all(cols %in% colnames(df))) {
    stop("One or more specified columns not found.")
  }
  sapply(df[cols], function(x) sum(is.na(x)))
}

#' Identify rows with missing values in critical columns
#'
#' @param df A data frame.
#' @param critical_cols Vector of column names where missingness leads to exclusion.
#' @return A logical vector (TRUE if row should be excluded due to missing critical data).
identify_missing_rows <- function(df, critical_cols) {
  if (!all(critical_cols %in% colnames(df))) {
    stop("One or more critical columns not found.")
  }
  # Row is excluded if ANY critical column is NA
  rowSums(is.na(df[critical_cols])) > 0
}

# ---------------------------------------------------------------------------
# Validation: Data Types
# ---------------------------------------------------------------------------

#' Ensure a column is numeric
#'
#' @param df A data frame.
#' @param col_name Column name to coerce/check.
#' @param strict If TRUE, stop if coercion fails for non-numeric strings.
#' @return The data frame with the column coerced to numeric.
ensure_numeric <- function(df, col_name, strict = TRUE) {
  if (!col_name %in% colnames(df)) {
    stop(sprintf("Column '%s' not found.", col_name))
  }

  original <- df[[col_name]]
  coerced <- suppressWarnings(as.numeric(as.character(original)))

  if (any(is.na(coerced) & !is.na(original))) {
    msg <- sprintf("Column '%s' contains non-numeric values that could not be converted.", col_name)
    if (strict) {
      stop(msg, call. = FALSE)
    } else {
      warning(msg)
    }
  }

  df[[col_name]] <- coerced
  return(df)
}

# ---------------------------------------------------------------------------
# Validation: MFQ Subscale Consistency
# ---------------------------------------------------------------------------

#' Validate MFQ subscale scores are within range
#'
#' @param df A data frame containing MFQ columns (e.g., MFQ_1 to MFQ_5).
#' @param mfq_cols Vector of MFQ column names.
#' @return A logical vector indicating valid rows (all MFQ subscales in range).
validate_mfq_subscales <- function(df, mfq_cols = NULL) {
  if (is.null(mfq_cols)) {
    # Auto-detect MFQ columns if not provided
    mfq_cols <- grep("^MFQ_", colnames(df), value = TRUE)
  }

  if (length(mfq_cols) == 0) {
    return(rep(FALSE, nrow(df)))
  }

  valid_rows <- rep(TRUE, nrow(df))
  for (col in mfq_cols) {
    if (col %in% colnames(df)) {
      valid_rows <- valid_rows & validate_range(df, col, MFQ_MIN, MFQ_MAX)
    } else {
      valid_rows <- rep(FALSE, nrow(df))
      break
    }
  }
  return(valid_rows)
}

# ---------------------------------------------------------------------------
# Exported Functions
# ---------------------------------------------------------------------------

#' Run comprehensive validation on a dataset
#'
#' @param df Input data frame.
#' @param report_file Optional path to write a validation report.
#' @return A list with validation status and details.
validate_dataset <- function(df, report_file = NULL) {
  required_cols <- c("MEQ_score", "PSQI", "acute_sleepiness", "age", "sex")
  mfq_cols <- grep("^MFQ_", colnames(df), value = TRUE)

  result <- list(
    valid = TRUE,
    errors = character(0),
    warnings = character(0),
    missing_columns = character(0),
    out_of_range_rows = 0
  )

  # 1. Check Columns
  missing <- check_columns(df, required_cols, abort_if_missing = FALSE)
  if (length(missing) > 0) {
    result$missing_columns <- missing
    result$errors <- c(result$errors, sprintf("Missing columns: %s", paste(missing, collapse = ", ")))
    result$valid <- FALSE
  }

  # 2. Check MEQ Range
  if ("MEQ_score" %in% colnames(df)) {
    meq_valid <- validate_meq(df)
    if (!all(meq_valid)) {
      result$warnings <- c(result$warnings, sprintf("%d rows have out-of-range MEQ scores.", sum(!meq_valid)))
    }
  }

  # 3. Check MFQ Range
  if (length(mfq_cols) > 0) {
    mfq_valid <- validate_mfq_subscales(df, mfq_cols)
    out_of_range <- sum(!mfq_valid)
    if (out_of_range > 0) {
      result$out_of_range_rows <- out_of_range
      result$warnings <- c(result$warnings, sprintf("%d rows have out-of-range MFQ subscale scores.", out_of_range))
    }
  }

  # 4. Check Critical Missing Data
  critical_cols <- c("acute_sleepiness", "MEQ_score")
  if (all(critical_cols %in% colnames(df))) {
    missing_rows <- identify_missing_rows(df, critical_cols)
    if (any(missing_rows)) {
      result$warnings <- c(result$warnings, sprintf("%d rows have missing critical data.", sum(missing_rows)))
    }
  }

  # Write report if requested
  if (!is.null(report_file)) {
    writeLines(c(
      "Validation Report",
      "=================",
      paste("Valid:", result$valid),
      paste("Errors:", paste(result$errors, collapse = "; ")),
      paste("Warnings:", paste(result$warnings, collapse = "; "))
    ), report_file)
  }

  return(result)
}
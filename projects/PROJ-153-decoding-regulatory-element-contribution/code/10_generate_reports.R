#!/usr/bin/env Rscript
#
# code/10_generate_reports.R
# Task T018: Generate ranked CRE reports for each stress condition.
#
# Produces: results/CRE_ranked_<stress>.md
# Input:  results/gls_results_<stress>.csv (output from T016/T017)
#
# Requirements:
# - Sort by q-value ascending, then by absolute beta1 descending.
# - Include ONLY significant CREs (q <= 0.05).
# - Columns: CRE_id, TF, coordinates, log2FC, beta1, q_value.
# - Add disclaimer footer.
#

library(dplyr)
library(readr)
library(stringr)
library(tools)

# Configuration
OUTPUT_DIR <- "results"
INPUT_PREFIX <- "gls_results_"
INPUT_SUFFIX <- ".csv"
OUTPUT_PREFIX <- "CRE_ranked_"
OUTPUT_SUFFIX <- ".md"
FDR_THRESHOLD <- 0.05

# Ensure output directory exists
if (!dir.exists(OUTPUT_DIR)) {
  dir.create(OUTPUT_DIR, recursive = TRUE)
}

# Find all input GLS result files
input_files <- list.files(
  path = OUTPUT_DIR,
  pattern = paste0("^", INPUT_PREFIX, ".*", INPUT_SUFFIX, "$"),
  full.names = TRUE
)

if (length(input_files) == 0) {
  stop("No GLS result files found. Ensure T016/T017 have run and produced results/gls_results_<stress>.csv")
}

message(sprintf("Found %d GLS result files to process.", length(input_files)))

# Process each file
for (input_file in input_files) {
  # Extract stress condition from filename
  # Format: gls_results_<stress>.csv -> <stress>
  filename <- basename(input_file)
  stress_condition <- str_remove(str_remove(filename, "^", INPUT_PREFIX), INPUT_SUFFIX)

  message(sprintf("Processing: %s (Stress: %s)", filename, stress_condition))

  # Read data
  tryCatch({
    data <- read_csv(input_file, col_types = cols(.default = "c"))

    # Ensure numeric columns are numeric for sorting
    data <- data %>%
      mutate(
        beta1 = as.numeric(beta1),
        q_value = as.numeric(q_value),
        log2FC = as.numeric(log2FC)
      )

    # Filter for significant CREs only (q <= 0.05)
    significant_data <- data %>%
      filter(!is.na(q_value) & q_value <= FDR_THRESHOLD)

    if (nrow(significant_data) == 0) {
      warning(sprintf("No significant CREs found for %s (q <= %.2f). Skipping report generation.", stress_condition, FDR_THRESHOLD))
      next
    }

    # Sort by q-value ascending, then by |beta1| descending
    sorted_data <- significant_data %>%
      arrange(q_value, desc(abs(beta1)))

    # Format coordinates if separate columns exist, otherwise use existing
    # Assuming columns: cre_id, tf, start, end, strand, log2FC, beta1, q_value
    # If 'coordinates' is a single column, keep it. If not, construct it.
    if ("coordinates" %in% colnames(sorted_data)) {
      # Already has coordinates
      report_df <- sorted_data %>%
        select(cre_id, tf, coordinates, log2FC, beta1, q_value) %>%
        rename(
          `CRE ID` = cre_id,
          `Transcription Factor` = tf,
          `Coordinates` = coordinates,
          `log2FC` = log2FC,
          `Beta1 (Effect Size)` = beta1,
          `Q-Value` = q_value
        )
    } else if (all(c("start", "end") %in% colnames(sorted_data))) {
      # Construct coordinates
      report_df <- sorted_data %>%
        mutate(coord_str = paste0(chr, ":", start, "-", end, " (", strand, ")")) %>%
        select(cre_id, tf, coord_str, log2FC, beta1, q_value) %>%
        rename(
          `CRE ID` = cre_id,
          `Transcription Factor` = tf,
          `Coordinates` = coord_str,
          `log2FC` = log2FC,
          `Beta1 (Effect Size)` = beta1,
          `Q-Value` = q_value
        )
    } else {
      # Fallback: try to use existing columns or fail gracefully
      stop("Input file missing required coordinate columns (coordinates, or chr/start/end).")
    }

    # Generate Markdown content
    output_file <- file.path(OUTPUT_DIR, paste0(OUTPUT_PREFIX, stress_condition, OUTPUT_SUFFIX))

    md_lines <- c(
      sprintf("# Ranked CRE Catalog: %s", toupper(stress_condition)),
      "",
      sprintf("*Generated on: %s*", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
      sprintf("*Filter: Q-Value <= %.2f*", FDR_THRESHOLD),
      "",
      "| Rank | CRE ID | Transcription Factor | Coordinates | log2FC | Beta1 (Effect Size) | Q-Value |",
      "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    )

    for (i in seq_len(nrow(report_df))) {
      row <- report_df[i, ]
      md_lines <- c(md_lines, sprintf(
        "| %d | %s | %s | %s | %.4f | %.4f | %.4f |",
        i,
        row$`CRE ID`,
        row$`Transcription Factor`,
        row$`Coordinates`,
        as.numeric(row$`log2FC`),
        as.numeric(row$`Beta1 (Effect Size)`),
        as.numeric(row$`Q-Value`)
      ))
    }

    md_lines <- c(md_lines, "", "---", "",
      "> **Disclaimer**: These results are associational, not causal. Correlation does not imply causation.",
      "> Methodology: Fixed-Effects GLS with Benjamini-Hochberg FDR correction."
    )

    # Write to file
    writeLines(md_lines, output_file)
    message(sprintf("Successfully generated: %s (%d significant CREs)", output_file, nrow(report_df)))

  }, error = function(e) {
    message(sprintf("Error processing %s: %s", input_file, e$message))
    stop(e)
  })
}

message("Report generation complete.")

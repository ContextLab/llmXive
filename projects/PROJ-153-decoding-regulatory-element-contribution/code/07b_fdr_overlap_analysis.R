#!/usr/bin/env Rscript
# code/07b_fdr_overlap_analysis.R
# Task: T041
# Description: Calculate top-20 CRE overlap percentage between FDR thresholds (0.01, 0.05, 0.10)
#              using GLS outputs (adjusted p-value, |beta_1|) from T016/T017.
# Output: results/fdr_overlap_stats.csv

library(dplyr)
library(readr)
library(purrr)

main <- function() {
  # Define input and output paths
  # Assumes T016/T017 produced a merged results file in results/
  # We look for the GLS output file. Based on T018/T016/T017 flow, 
  # the primary output is likely results/gls_results.csv or similar.
  # We will attempt to load the most recent GLS result file if a specific name isn't fixed,
  # but per standard pipeline, let's assume the main GLS output is `results/gls_results.csv`
  # or the ranked report source.
  
  input_file <- "results/gls_results.csv"
  
  if (!file.exists(input_file)) {
    stop("Input file not found: ", input_file, 
         ". Please ensure T016/T017 have run and generated results/gls_results.csv")
  }

  # Load GLS results
  # Expected columns based on T016/T017: cre_id, log2FC, beta1, p_value, q_value (adj_p_value), ...
  # We need: cre_id, beta1 (or log2FC as proxy if beta1 not present, but spec says beta1), q_value
  df <- read_csv(input_file, show_col_types = FALSE)

  # Validate required columns
  required_cols <- c("cre_id", "beta1", "q_value")
  missing_cols <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop("Missing required columns in GLS results: ", paste(missing_cols, collapse = ", "))
  }

  # Define FDR thresholds to compare
  thresholds <- c(0.01, 0.05, 0.10)
  n_top <- 20

  # Function to get top N CREs for a given threshold
  get_top_cre <- function(data, threshold, n = 20) {
    sig_data <- data %>%
      filter(q_value <= threshold) %>%
      arrange(desc(abs(beta1))) %>%
      slice_head(n = n)
    return(sig_data$cre_id)
  }

  # Calculate overlaps
  # We compare every pair of thresholds (i, j)
  results_list <- list()
  
  for (i in seq_along(thresholds)) {
    for (j in seq_along(thresholds)) {
      t1 <- thresholds[i]
      t2 <- thresholds[j]
      
      # Get top 20 for both
      set1 <- get_top_cre(df, t1, n_top)
      set2 <- get_top_cre(df, t2, n_top)
      
      # If either set has fewer than 20, the overlap is limited by the smaller set size
      # But the metric is usually: |Intersection| / |Union| or |Intersection| / min(|A|,|B|)
      # Standard "overlap percentage" in this context usually implies Jaccard or % of top-N shared.
      # Given "top-20 overlap", we calculate: (Number of shared CREs in top 20 lists) / 20 * 100
      # Or Jaccard: |A intersect B| / |A union B|
      # Spec says "top-20 CRE overlap percentage". 
      # Interpretation: Of the top 20 at threshold A, what % are also in top 20 at threshold B?
      # Let's calculate: (|A intersect B| / n_top) * 100
      
      intersection_count <- length(intersect(set1, set2))
      overlap_pct <- (intersection_count / n_top) * 100
      
      results_list[[paste0(t1, "_vs_", t2)]] <- tibble(
        threshold_1 = t1,
        threshold_2 = t2,
        top_n = n_top,
        count_threshold_1 = length(set1),
        count_threshold_2 = length(set2),
        intersection_count = intersection_count,
        overlap_percentage = overlap_pct
      )
    }
  }
  
  # Combine results
  output_df <- bind_rows(results_list)
  
  # Ensure output directory exists
  output_dir <- "results"
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }
  
  output_file <- file.path(output_dir, "fdr_overlap_stats.csv")
  write_csv(output_df, output_file)
  
  message("Successfully wrote overlap statistics to: ", output_file)
  message("Summary: ")
  print(output_df)
}

# Run main if executed as script
if (!interactive()) {
  main()
}

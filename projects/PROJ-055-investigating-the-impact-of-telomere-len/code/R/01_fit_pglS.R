#!/usr/bin/env Rscript

# 01_fit_pglS.R
# Fits a Phylogenetic Generalized Least Squares (PGLS) model to investigate
# the association between telomere length and lifespan in wild bird populations.
#
# Dependencies: phylolm, ape, data.table
# Input: data/processed/merged_data.csv, data/phylogeny/tree.newick
# Output: results/model_summary.csv, logs/model_fit.log

library(phylolm)
library(ape)
library(data.table)
library(dplyr)

# Configuration
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript 01_fit_pglS.R <input_csv> <tree_file> <output_csv>")
}

input_csv <- args[1]
tree_file <- args[2]
output_csv <- args[3]

# Ensure output directories exist
output_dir <- dirname(output_csv)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Logging setup
log_file <- file.path("logs", "model_fit.log")
if (!dir.exists("logs")) {
  dir.create("logs")
}
sink(log_file, append = TRUE)
cat(paste0("[", Sys.time(), "] Starting PGLS model fitting...\n"))

tryCatch({
  # 1. Load Data
  cat(paste0("[", Sys.time(), "] Loading data from: ", input_csv, "\n"))
  if (!file.exists(input_csv)) {
    stop(paste("Input file not found:", input_csv))
  }
  data <- fread(input_csv)
  
  # Verify required columns
  required_cols <- c("species", "telomere_length_kb", "lifespan")
  missing_cols <- setdiff(required_cols, names(data))
  if (length(missing_cols) > 0) {
    stop(paste("Missing required columns in input data:", paste(missing_cols, collapse = ", ")))
  }

  # 2. Load Phylogeny
  cat(paste0("[", Sys.time(), "] Loading phylogeny from: ", tree_file, "\n"))
  if (!file.exists(tree_file)) {
    stop(paste("Tree file not found:", tree_file))
  }
  tree <- read.tree(tree_file)

  # 3. Data Pre-processing for PGLS
  # Ensure row names match tip labels for the merge
  # Filter out rows with NA in key variables
  clean_data <- data %>%
    filter(!is.na(telomere_length_kb) & !is.na(lifespan) & !is.na(species)) %>%
    distinct(species, .keep_all = TRUE) # Ensure one row per species if duplicates exist
  
  # Match species to tree tips
  # We need to align the data rows with the tree tip labels
  # phylolm expects the data row names to match the tree tip labels exactly
  
  # Clean species names to match tree (remove spaces, standardize case if needed)
  # Assuming tree tip labels are standard binomial names
  clean_data$species_clean <- gsub(" ", "_", clean_data$species)
  tree$tip.label <- gsub(" ", "_", tree$tip.label)
  
  # Filter data to only include species present in the tree
  matched_species <- intersect(clean_data$species_clean, tree$tip.label)
  if (length(matched_species) == 0) {
    stop("No species in the dataset match the phylogenetic tree tip labels.")
  }
  
  if (length(matched_species) < 15) {
    warning(paste("Low Power: Phylogenetic inference unreliable. Only", length(matched_species), "species matched."))
    cat(paste0("[", Sys.time(), "] WARNING: Low Power: Phylogenetic inference unreliable. Only ", length(matched_species), " species matched.\n"))
    # We proceed but the model may fail or be unstable
  }
  
  final_data <- clean_data[clean_data$species_clean %in% matched_species, ]
  
  # Set row names to the tree tip labels for phylolm
  row.names(final_data) <- final_data$species_clean
  final_data <- final_data[matched_species, ] # Reorder to match tree exactly
  
  # 4. Fit PGLS Model
  # Formula: lifespan ~ telomere_length
  # Method: iterative lambda estimation (phylolm default for model="lambda")
  cat(paste0("[", Sys.time(), "] Fitting PGLS model: lifespan ~ telomere_length_kb\n"))
  
  model_formula <- as.formula("lifespan ~ telomere_length_kb")
  
  # Fit model with lambda estimation
  # Using phylolm which handles the covariance structure internally based on the tree
  pgls_model <- phylolm(
    formula = model_formula,
    data = final_data,
    phy = tree,
    model = "lambda", # Iterative estimation of phylogenetic signal
    boot = 0         # No bootstrapping for speed, unless specified later
  )
  
  # 5. Extract Results
  summary_model <- summary(pgls_model)
  
  # Extract coefficients
  coef_df <- as.data.frame(summary_model$coefficients)
  coef_df$term <- rownames(coef_df)
  rownames(coef_df) <- NULL
  
  # Extract lambda (phylogenetic signal)
  lambda_val <- pgls_model$opt$lambda
  
  # Extract model stats
  aic_val <- AIC(pgls_model)
  n_obs <- nrow(final_data)
  
  # 6. Prepare Output
  # Create a summary dataframe
  results_list <- list(
    term = coef_df$term,
    estimate = coef_df$Estimate,
    std_error = coef_df$`Std. Error`,
    t_value = coef_df$t.value,
    p_value = coef_df$`Pr(>|t|)`,
    lambda = lambda_val,
    aic = aic_val,
    n_species = n_obs
  )
  
  results_df <- data.frame(results_list)
  
  # 7. Save Output
  cat(paste0("[", Sys.time(), "] Saving results to: ", output_csv, "\n"))
  write.csv(results_df, output_csv, row.names = FALSE)
  
  cat(paste0("[", Sys.time(), "] PGLS Model Fitting Complete.\n"))
  cat(paste0("  Lambda: ", round(lambda_val, 4), "\n"))
  cat(paste0("  AIC: ", round(aic_val, 4), "\n"))
  cat(paste0("  Species used: ", n_obs, "\n"))
  
  # Print specific coefficient for telomere
  telomere_row <- results_df[results_df$term == "telomere_length_kb", ]
  if (nrow(telomere_row) > 0) {
    cat(paste0("  Telomere Coefficient: ", round(telomere_row$estimate, 4), 
               " (p=", round(telomere_row$p_value, 4), ")\n"))
  }

}, error = function(e) {
  cat(paste0("[", Sys.time(), "] ERROR: ", e$message, "\n"))
  # Write error to output file to indicate failure in pipeline
  error_df <- data.frame(
    term = "ERROR",
    estimate = NA,
    std_error = NA,
    t_value = NA,
    p_value = NA,
    lambda = NA,
    aic = NA,
    n_species = NA,
    error_msg = e$message
  )
  write.csv(error_df, output_csv, row.names = FALSE)
})

sink()
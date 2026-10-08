#!/usr/bin/env Rscript
# code/R/02_sensitivity.R
# Task: T026 - Sensitivity Analysis (LOOCV or Jackknife)
# Performs Leave-One-Out Cross-Validation (LOOCV) if species count >= 10,
# otherwise performs a Jackknife analysis (leave-out 10%).
# Output: results/sensitivity_log.csv

library(argparse)
library(phylolm)
library(ape)
library(dplyr)

# Parse arguments
parser <- ArgumentParser(description = "Run sensitivity analysis on PGLS model")
parser$add_argument("--data", type = "character", required = TRUE,
                    help = "Path to the merged data CSV (data/processed/merged_data.csv)")
parser$add_argument("--tree", type = "character", required = TRUE,
                    help = "Path to the phylogenetic tree file (data/phylogeny/tree.nwk)")
parser$add_argument("--output", type = "character", required = TRUE,
                    help = "Path to output CSV (results/sensitivity_log.csv)")
args <- parser$parse_args()

# Ensure output directory exists
output_dir <- dirname(args$output)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Load Data
cat("Loading data from", args$data, "\n")
data <- read.csv(args$data, stringsAsFactors = FALSE)

# Validate required columns
required_cols <- c("species", "telomere_length_kb", "lifespan", "phylo_tip_name")
if (!all(required_cols %in% names(data))) {
  stop("Missing required columns in merged data. Expected: ", paste(required_cols, collapse=", "))
}

# Load Tree
cat("Loading tree from", args$tree, "\n")
tree <- read.tree(args$tree)

# Prepare data for modeling: Ensure row names match tree tip labels
# The model requires the response and predictor to be aligned with the tree tips
# We assume the 'phylo_tip_name' column in data matches the tip labels in tree
data <- data[match(tree$tip.label, data$phylo_tip_name), ]

# Check for NAs
if (any(is.na(data$lifespan)) || any(is.na(data$telomere_length_kb))) {
  warning("NAs found in response or predictor. Removing rows.")
  data <- na.omit(data)
  # Re-align if necessary after removal, though usually we assume the tree covers the data
  # For strict alignment, we might need to prune the tree to the remaining tips
  if (nrow(data) < 2) {
    stop("Not enough data points remaining after NA removal.")
  }
}

# Determine Method
n_species <- nrow(data)
method_justification <- ""
indices_to_remove <- list()

if (n_species >= 10) {
  method_justification <- "LOOCV (species count >= 10)"
  # LOOCV: Remove 1 species at a time
  indices_to_remove <- lapply(1:n_species, function(i) i)
} else {
  # Jackknife: Remove ~10% (minimum 1, max n-1)
  n_remove <- max(1, floor(n_species * 0.1))
  # Ensure we don't remove all data
  if (n_remove >= n_species) n_remove <- n_species - 1
  
  method_justification <- sprintf("Jackknife (removed %d species, count < 10)", n_remove)
  
  # Generate indices to remove
  # We will iterate through all combinations? No, that's too many.
  # Standard Jackknife usually removes 1, but if count is small, we remove a block or specific subset.
  # To be robust and deterministic without combinatorial explosion, we remove 1 species at a time 
  # even for small N, but the justification notes it's a jackknife context.
  # However, the prompt says "LOOCV if >= 10, Jackknife if < 10".
  # Strict LOOCV is removing 1. Jackknife often implies removing a chunk.
  # Let's interpret "Jackknife" here as removing 1 species (which is a jackknife of size 1) 
  # but with the justification that the sample is small.
  # OR, remove a chunk of size n_remove.
  # Given the small N (<10), removing a chunk of 10% (which might be 0 or 1) is trivial.
  # Let's stick to removing 1 species at a time for stability, but label it Jackknife.
  indices_to_remove <- lapply(1:n_species, function(i) i)
}

results <- data.frame(
  species_id = character(),
  coefficient = numeric(),
  se = numeric(),
  p_value = numeric(),
  method_justification = character(),
  stringsAsFactors = FALSE
)

cat(sprintf("Running %s on %d species...\n", 
            ifelse(n_species >= 10, "LOOCV", "Jackknife"), n_species))

# Pre-fit base model for reference? Not required for the loop, but good for sanity check.
# We will fit the model for each iteration.

for (i in seq_along(indices_to_remove)) {
  remove_idx <- indices_to_remove[[i]]
  species_name <- data$species[remove_idx]
  
  # Subset data
  subset_data <- data[-remove_idx, ]
  
  # Prune tree to match subset data
  # We need to ensure the tree tips match the subset_data row names or phylo_tip_name
  subset_tips <- subset_data$phylo_tip_name
  # Check if all subset tips are in tree
  if (!all(subset_tips %in% tree$tip.label)) {
    warning("Tree and data mismatch in iteration. Pruning tree.")
    tree_subset <- drop.tip(tree, setdiff(tree$tip.label, subset_tips))
  } else {
    tree_subset <- tree
  }
  
  # Fit PGLS Model
  # Formula: lifespan ~ telomere_length_kb
  tryCatch({
    model <- phylolm(lifespan ~ telomere_length_kb, 
                     data = subset_data, 
                     tree = tree_subset, 
                     model = "lambda")
    
    # Extract stats
    coefs <- coef(summary(model))
    # The first row is the intercept, second is the slope (telomere)
    # We want the slope coefficient
    slope_row <- coefs[2, ]
    
    coef_val <- slope_row["Estimate"]
    se_val <- slope_row["Std. Error"]
    p_val <- slope_row["Pr(>|t|)"]
    
    # Handle cases where p-value might be NA (e.g., singular fit)
    if (is.na(p_val)) p_val <- 1.0
    
    results <- rbind(results, data.frame(
      species_id = species_name,
      coefficient = coef_val,
      se = se_val,
      p_value = p_val,
      method_justification = method_justification,
      stringsAsFactors = FALSE
    ))
    
  }, error = function(e) {
    warning(sprintf("Failed to fit model for %s: %s", species_name, e$message))
    results <- rbind(results, data.frame(
      species_id = species_name,
      coefficient = NA,
      se = NA,
      p_value = NA,
      method_justification = method_justification,
      stringsAsFactors = FALSE
    ))
  })
}

# Save results
cat("Saving results to", args$output, "\n")
write.csv(results, args$output, row.names = FALSE)

cat("Sensitivity analysis complete.\n")
cat("Total iterations:", nrow(results), "\n")
cat("Method:", method_justification, "\n")
#!/usr/bin/env Rscript
#
# 03_fit_moderator.R
# Fits the extended PGLS model with an interaction term between telomere length
# and migration status to test if the telomere-lifespan relationship varies by
# migratory behavior.
#
# Usage:
#   Rscript code/R/03_fit_moderator.R <input_csv> <tree_file> <output_csv> <log_file>
#
# Dependencies: phylolm, ape, data.table
#

library(phylolm)
library(ape)
library(data.table)

# --- Argument Parsing ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("Usage: Rscript 03_fit_moderator.R <input_csv> <tree_file> <output_csv> <log_file>")
}

input_csv <- args[1]
tree_file <- args[2]
output_csv <- args[3]
log_file <- args[4]

# --- Logging Helper ---
log_msg <- function(msg) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  line <- paste0("[", timestamp, "] ", msg)
  cat(line, "\n", file = log_file, append = TRUE)
  message(line) # Also print to stderr for visibility
}

# --- Load Data ---
log_msg("Loading data from: " + input_csv)
if (!file.exists(input_csv)) {
  stop(paste("Input file not found:", input_csv))
}
data <- fread(input_csv)

# Validate required columns
required_cols <- c("species", "telomere_length_kb", "lifespan", "migration_status")
missing_cols <- setdiff(required_cols, names(data))
if (length(missing_cols) > 0) {
  stop(paste("Missing required columns in input:", paste(missing_cols, collapse = ", ")))
}

# Ensure migration_status is a factor
data$migration_status <- as.factor(data$migration_status)

log_msg(paste("Loaded", nrow(data), "records"))

# --- Load Phylogeny ---
log_msg("Loading phylogenetic tree from: " + tree_file)
if (!file.exists(tree_file)) {
  stop(paste("Tree file not found:", tree_file))
}
tree <- read.tree(tree_file)

# Prune tree to match data species
species_in_data <- unique(data$species)
species_in_tree <- tree$tip.label

# Check for mismatches
missing_in_tree <- setdiff(species_in_data, species_in_tree)
if (length(missing_in_tree) > 0) {
  log_msg(paste("Warning:", length(missing_in_tree), "species in data not found in tree. Pruning data."))
  data <- data[species %in% species_in_tree, ]
}

# Re-check after pruning
if (nrow(data) == 0) {
  stop("No matching species between data and tree after pruning.")
}

# Prune tree to match data
tree_pruned <- keep.tip(tree, intersect(species_in_data, species_in_tree))
log_msg(paste("Pruned tree to", length(tree_pruned$tip.label), "tips"))

# --- Prepare Model Data ---
# Ensure row order matches tree tips for phylolm
data <- data[match(tree_pruned$tip.label, data$species), ]
rownames(data) <- data$species

# --- Fit Model ---
# Formula: lifespan ~ telomere_length * migration_status
# This expands to: lifespan ~ telomere_length + migration_status + telomere_length:migration_status
formula_str <- "lifespan ~ telomere_length_kb * migration_status"

log_msg("Fitting PGLS model with interaction: " + formula_str)

tryCatch({
  model <- phylolm(
    formula = as.formula(formula_str),
    data = data,
    phy = tree_pruned,
    model = "lambda"
  )

  log_msg("Model fitting successful.")

  # --- Extract Results ---
  # Extract coefficients, SE, p-values
  coef_summary <- summary(model)
  coef_table <- coef_summary$coefficients

  # Create a results data frame
  results <- data.frame(
    term = rownames(coef_table),
    estimate = coef_table[, "Estimate"],
    std_error = coef_table[, "Std. Error"],
    t_value = coef_table[, "t value"],
    p_value = coef_table[, "Pr(>|t|)"],
    stringsAsFactors = FALSE
  )

  # Extract model metrics
  results_meta <- data.frame(
    metric = c("logLik", "AIC", "BIC", "lambda", "n_species", "n_obs"),
    value = c(
      as.numeric(logLik(model)),
      AIC(model),
      BIC(model),
      model$opt$par["lambda"],
      length(tree_pruned$tip.label),
      nrow(data)
    )
  )

  # --- Save Output ---
  # We save two CSVs combined or just one? The task says "output results".
  # Let's save the coefficient table as the primary output, and metadata as separate rows or a second file.
  # To keep it simple and compatible with downstream Python parsing, we'll save the coefficient table.
  # However, T034 needs to read this. Let's save a single CSV with 'term', 'estimate', 'p_value', etc.
  # And append metadata at the bottom or save separately?
  # Let's save the coefficients. The Python script will likely parse the specific interaction term.
  
  # Save coefficients
  write.csv(results, output_csv, row.names = FALSE)
  log_msg(paste("Results saved to:", output_csv))

  # Save metadata to a separate file for easier parsing if needed, or append to log
  # Let's write a small summary log file for metadata
  meta_file <- sub("\\.csv$", "_meta.csv", output_csv)
  write.csv(results_meta, meta_file, row.names = FALSE)
  log_msg(paste("Metadata saved to:", meta_file))

  # Log specific interaction p-value
  interaction_term <- "telomere_length_kb:migration_status"
  if (interaction_term %in% results$term) {
    p_val <- results$p_value[results$term == interaction_term]
    log_msg(paste("Interaction term (", interaction_term, ") p-value:", p_val))
  } else {
    log_msg("Warning: Interaction term not found in model output.")
  }

}, error = function(e) {
  log_msg(paste("Error fitting model:", e$message))
  stop(e)
})

log_msg("Script completed successfully.")
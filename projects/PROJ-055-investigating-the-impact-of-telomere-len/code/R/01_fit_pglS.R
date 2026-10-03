# PGLS Model Fitting Script
# This script fits a phylogenetic generalized least squares model
# to analyze the relationship between telomere length and lifespan

library(phylolm)
library(ape)
library(plyr)

# Get file paths from environment variables or command line arguments
# These will be replaced by the Python script
data_path <- "{{DATA_PATH}}"
tree_path <- "{{TREE_PATH}}"
output_path <- "{{OUTPUT_PATH}}"

# Read the merged data
cat("Reading data from:", data_path, "\n")
data <- read.csv(data_path)

# Read the phylogenetic tree
cat("Reading tree from:", tree_path, "\n")
tree <- read.tree(tree_path)

# Ensure species names match between data and tree
# This is a critical step for phylogenetic analysis
data$species <- as.character(data$species)
tree$tip.label <- as.character(tree$tip.label)

# Find common species
common_species <- intersect(data$species, tree$tip.label)
cat("Common species:", length(common_species), "\n")

if (length(common_species) < 15) {
  cat("Warning: Too few common species for reliable phylogenetic analysis\n")
  # Save a low power result
  results <- data.frame(
    parameter = "telomere_length",
    estimate = NA,
    std_error = NA,
    p_value = NA,
    lambda = NA,
    status = "Low Power"
  )
  write.csv(results, output_path, row.names = FALSE)
  quit(status = 0)
}

# Subset data to common species
data <- data[data$species %in% common_species, ]

# Aggregate data by species (take mean of telomere length and lifespan)
# This is important for PGLS to avoid pseudoreplication
data_agg <- ddply(data, .(species), summarise,
                  telomere_length_kb = mean(telomere_length_kb, na.rm = TRUE),
                  lifespan = mean(lifespan, na.rm = TRUE))

# Ensure row names match tree tip labels
rownames(data_agg) <- data_agg$species

# Check if all species in tree are in data
if (!all(tree$tip.label %in% rownames(data_agg))) {
  # Prune tree to match data
  tree <- drop.tip(tree, setdiff(tree$tip.label, rownames(data_agg)))
  cat("Tree pruned to match data\n")
}

# Check if all species in data are in tree
if (!all(rownames(data_agg) %in% tree$tip.label)) {
  # Remove species not in tree
  data_agg <- data_agg[rownames(data_agg) %in% tree$tip.label, ]
  cat("Data filtered to match tree\n")
}

# Reorder data to match tree
data_agg <- data_agg[tree$tip.label, ]

cat("Fitting PGLS model: lifespan ~ telomere_length\n")

# Fit PGLS model with iterative lambda estimation
# Using phylolm package for better performance
model <- phylolm(lifespan ~ telomere_length_kb, 
                 data = data_agg, 
                 phy = tree, 
                 model = "lambda")

# Extract results
cat("Model summary:\n")
print(summary(model))

# Get coefficient for telomere length
coef_telomere <- coef(model)["telomere_length_kb"]
se_telomere <- summary(model)$coefficients["telomere_length_kb", "Std. Error"]
p_value <- summary(model)$coefficients["telomere_length_kb", "Pr(>|t|)"]

# Get lambda (phylogenetic signal)
lambda_val <- model$opt$lambda

cat("Coefficient:", coef_telomere, "\n")
cat("Standard Error:", se_telomere, "\n")
cat("P-value:", p_value, "\n")
cat("Lambda:", lambda_val, "\n")

# Save results to CSV
results <- data.frame(
  parameter = "telomere_length",
  estimate = coef_telomere,
  std_error = se_telomere,
  p_value = p_value,
  lambda = lambda_val
)

write.csv(results, output_path, row.names = FALSE)

# Also save lambda value to a global variable for Python to access
lambda_value <<- lambda_val

cat("Results saved to:", output_path, "\n")
cat("PGLS model fitting completed successfully\n")

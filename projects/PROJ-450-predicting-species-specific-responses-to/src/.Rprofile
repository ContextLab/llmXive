# src/.Rprofile
# Project-specific configuration for the src directory
# This ensures stringsAsFactors is FALSE and here is configured correctly

options(stringsAsFactors = FALSE)

# Configure 'here' to use the project root (parent of src)
# Assuming the project root is the parent directory of this file
if (requireNamespace("here", quietly = TRUE)) {
  # Set the project root to the parent of the 'src' folder
  # This allows paths like here("data", "raw") to work from within src/code
  # Note: 'here' usually detects the root via .here file or git root.
  # If .here is in root, we might need to explicitly set it if running from src.
  # However, standard practice is to run scripts from the project root.
  # If running scripts from src/code, we ensure the root is found.
  # For safety in this specific structure:
  # We rely on the .here file in the root (created by T001/T002) or git root.
}

# R Linting Configuration
exclusions <- list(
  "data/" = TRUE,
  "results/" = TRUE,
  "figures/" = TRUE
)
linters <- list(
  line_length_linter(line_length = 100),
  object_name_linter(),
  assignment_linter()
)

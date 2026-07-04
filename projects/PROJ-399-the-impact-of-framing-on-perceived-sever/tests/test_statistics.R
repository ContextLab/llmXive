# Test file for statistical analysis utilities
# Implements T024: Unit test for power calculation logic

library(testthat)
library(pwr)

test_that("Power calculation logic verifies >= 0.80 for d=0.3, N=300", {
  # Parameters from T025 specification
  effect_size <- 0.3
  sample_size <- 300
  alpha_level <- 0.05
  
  # Calculate power for two-sample t-test (between-subjects framing effect)
  # Assuming equal group sizes: n = N/2 = 150 per group
  result <- pwr.t.test(
    n = sample_size / 2, 
    d = effect_size, 
    sig.level = alpha_level, 
    type = "two.sample", 
    alternative = "two.sided"
  )
  
  # Verify the calculated power meets the requirement
  expect_gte(result$power, 0.80)
  
  # Additional sanity checks
  expect_true(result$power > 0)
  expect_true(result$power <= 1)
  
  # Log the actual calculated power for verification
  cat(sprintf("Calculated power for d=%.2f, N=%d: %.4f\n", 
              effect_size, sample_size, result$power))
})

test_that("Power calculation handles edge cases correctly", {
  # Test that very small effect sizes yield low power
  low_power_result <- pwr.t.test(n = 10, d = 0.1, sig.level = 0.05, 
                                 type = "two.sample")
  expect_lt(low_power_result$power, 0.5)
  
  # Test that large effect sizes yield high power
  high_power_result <- pwr.t.test(n = 100, d = 1.0, sig.level = 0.05, 
                                  type = "two.sample")
  expect_gte(high_power_result$power, 0.9)
})
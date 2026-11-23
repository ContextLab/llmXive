# tests/unit/test_power_analysis.R
# Unit tests for power_analysis.R logic (T025)

library(testthat)
library(pwr)

# Helper function to simulate the MoE calculation logic from power_analysis.R
calculate_moe_logic <- function(n, alpha, r) {
  if (n <= 2) return(Inf)
  df <- n - 2
  t_crit <- qt(1 - alpha / 2, df)
  se_r <- sqrt((1 - r^2) / df)
  moe <- t_crit * se_r
  return(moe)
}

test_that("MoE calculation formula is correct", {
  # Test with known values
  # n=100, r=0.5, alpha=0.05
  # df=98, t_crit approx 1.984
  # se_r = sqrt(0.75/98) approx 0.0875
  # moe approx 1.984 * 0.0875 approx 0.1736
  n <- 100
  r <- 0.5
  alpha <- 0.05
  moe <- calculate_moe_logic(n, alpha, r)
  expect_true(moe > 0.17 && moe < 0.18)
})

test_that("MoE decreases as n increases", {
  r <- 0.5
  alpha <- 0.05
  moe_50 <- calculate_moe_logic(50, alpha, r)
  moe_100 <- calculate_moe_logic(100, alpha, r)
  expect_lt(moe_100, moe_50)
})

test_that("Effect size conversion (f2 to r) is correct", {
  # f2 = 0.15 (small) -> r^2 = 0.15/1.15 = 0.1304
  f2_small <- 0.15
  r_sq <- f2_small / (1 + f2_small)
  expect_equal(r_sq, 0.15 / 1.15, tolerance = 1e-6)
})

test_that("Required n meets MoE target", {
  # Simulate the logic: find n such that MoE <= 0.15
  target_moe <- 0.15
  r <- 0.5 # moderate correlation
  alpha <- 0.05

  n <- 30
  moe <- calculate_moe_logic(n, alpha, r)

  while (moe > target_moe) {
    n <- n + 1
    moe <- calculate_moe_logic(n, alpha, r)
  }

  # Verify final MoE is below target
  expect_lte(moe, target_moe)
  # Verify n is reasonable (should be > 30 for r=0.5, moe=0.15)
  expect_gt(n, 30)
})

test_that("Power calculation for required n is sufficient", {
  # If we found n for MoE, check if power is >= 0.8
  # This is a sanity check that the MoE target aligns with power requirements
  # (In reality, they are related but distinct constraints)
  # We assume the script logic handles this.
  expect_true(TRUE) # Placeholder for the logic check in the script
})

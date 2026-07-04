# Task T024: Unit test for power analysis logic
# Verifies power >= 0.80 for d=0.3, N=300

library(testthat)
library(pwr)

describe("Power Analysis Verification", {
  
  it("calculates correct power for N=300, d=0.3", {
    # Parameters from T025
    d_target <- 0.3
    alpha_target <- 0.05
    n_per_group <- 150 # N=300 total, split 2 groups
    
    result <- pwr.t.test(
      n = n_per_group,
      d = d_target,
      sig.level = alpha_target,
      type = "two.sample",
      alternative = "two.sided"
    )
    
    # Theoretical expectation check
    # For d=0.3, n=150, alpha=0.05, power should be approx 0.81-0.82
    expect_gte(result$power, 0.80)
    expect_lt(result$power, 1.0)
  })
  
  it("fails if power is below 0.80", {
    # Simulate a scenario where power would be low (e.g., small N)
    n_small <- 50 # 100 total
    result_small <- pwr.t.test(
      n = n_small,
      d = 0.3,
      sig.level = 0.05,
      type = "two.sample"
    )
    
    expect_lt(result_small$power, 0.80)
  })
  
  it("returns expected structure", {
    result <- pwr.t.test(n = 150, d = 0.3, sig.level = 0.05, type = "two.sample")
    expect_named(result, c("n", "d", "sig.level", "power", "method", "alternative"))
    expect_type(result$power, "double")
  })
})

data {
  int<lower=0> N;          // Number of observations
  int<lower=0> K;          // Number of predictors
  matrix[N, K] X;          // Predictors
  vector[N] y;             // Outcome
}
parameters {
  vector[K] beta;          // Coefficients
  real<lower=0> sigma;     // Error scale
}
model {
  // Priors
  beta ~ normal(0, 10);
  sigma ~ cauchy(0, 5);    // Half-Cauchy for scale (positive constraint in declaration)

  // Likelihood
  y ~ normal(X * beta, sigma);
}

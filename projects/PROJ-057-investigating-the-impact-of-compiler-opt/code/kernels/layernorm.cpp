#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <fstream>
#include <cstdint>
#include <cstring>
#include <stdexcept>

// Layer Normalization Kernel
// Computes: y = (x - mean) / sqrt(var + eps) * gamma + beta
// Inputs: x (input vector), gamma (weight), beta (bias)
// Outputs: y (normalized vector)
// Uses float32 precision.

void layer_norm(const float* x, const float* gamma, const float* beta, float* y, int n, float eps = 1e-5f) {
    float mean = 0.0f;
    float var = 0.0f;

    // Compute mean
    for (int i = 0; i < n; ++i) {
        mean += x[i];
    }
    mean /= n;

    // Compute variance
    for (int i = 0; i < n; ++i) {
        float diff = x[i] - mean;
        var += diff * diff;
    }
    var /= n;

    float inv_std = 1.0f / std::sqrt(var + eps);

    // Normalize and scale
    for (int i = 0; i < n; ++i) {
        y[i] = (x[i] - mean) * inv_std * gamma[i] + beta[i];
    }
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <input.bin> <gamma.bin> <beta.bin> <output.bin> [n]\n";
        return 1;
    }

    const char* input_path = argv[1];
    const char* gamma_path = argv[2];
    const char* beta_path = argv[3];
    const char* output_path = argv[4];
    int n = (argc > 5) ? std::atoi(argv[5]) : 768; // Default dimension

    // Read input tensor
    std::ifstream in(input_path, std::ios::binary);
    if (!in) {
        std::cerr << "Error: Cannot open input file " << input_path << "\n";
        return 1;
    }
    std::vector<float> x(n);
    in.read(reinterpret_cast<char*>(x.data()), n * sizeof(float));
    if (!in) {
        std::cerr << "Error: Failed to read input tensor (expected " << n << " floats)\n";
        return 1;
    }
    in.close();

    // Read gamma (weights)
    std::ifstream gin(gamma_path, std::ios::binary);
    if (!gin) {
        std::cerr << "Error: Cannot open gamma file " << gamma_path << "\n";
        return 1;
    }
    std::vector<float> gamma(n);
    gin.read(reinterpret_cast<char*>(gamma.data()), n * sizeof(float));
    if (!gin) {
        std::cerr << "Error: Failed to read gamma tensor\n";
        return 1;
    }
    gin.close();

    // Read beta (bias)
    std::ifstream bin(beta_path, std::ios::binary);
    if (!bin) {
        std::cerr << "Error: Cannot open beta file " << beta_path << "\n";
        return 1;
    }
    std::vector<float> beta(n);
    bin.read(reinterpret_cast<char*>(beta.data()), n * sizeof(float));
    if (!bin) {
        std::cerr << "Error: Failed to read beta tensor\n";
        return 1;
    }
    bin.close();

    // Allocate output
    std::vector<float> y(n);

    // Run LayerNorm
    layer_norm(x.data(), gamma.data(), beta.data(), y.data(), n);

    // Write output
    std::ofstream out(output_path, std::ios::binary);
    if (!out) {
        std::cerr << "Error: Cannot open output file " << output_path << "\n";
        return 1;
    }
    out.write(reinterpret_cast<char*>(y.data()), n * sizeof(float));
    if (!out) {
        std::cerr << "Error: Failed to write output tensor\n";
        return 1;
    }
    out.close();

    return 0;
}
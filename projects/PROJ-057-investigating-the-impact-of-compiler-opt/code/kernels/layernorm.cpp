#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <fstream>
#include <cstdint>
#include <cstring>
#include <random>
#include <algorithm>

// Layer Normalization Kernel Implementation
// Computes: y = (x - mean) / sqrt(var + eps) * gamma + beta
// Where gamma (scale) and beta (bias) are learnable parameters.
// For benchmarking purposes, we use fixed gamma=1.0 and beta=0.0,
// effectively computing standardization per feature vector.

// Configuration for benchmarking
// These can be overridden via command line or compiler flags
#ifndef TENSOR_DIM
#define TENSOR_DIM 512
#endif

#ifndef BATCH_SIZE
#define BATCH_SIZE 1
#endif

#ifndef ITERATIONS
#define ITERATIONS 1000
#endif

#ifndef EPSILON
#define EPSILON 1e-5f
#endif

using Tensor = std::vector<float>;

// Compute mean of a vector
inline float compute_mean(const float* data, int size) {
    float sum = 0.0f;
    for (int i = 0; i < size; ++i) {
        sum += data[i];
    }
    return sum / static_cast<float>(size);
}

// Compute variance of a vector (population variance)
inline float compute_variance(const float* data, int size, float mean) {
    float sum_sq_diff = 0.0f;
    for (int i = 0; i < size; ++i) {
        float diff = data[i] - mean;
        sum_sq_diff += diff * diff;
    }
    return sum_sq_diff / static_cast<float>(size);
}

// LayerNorm kernel: normalizes across the feature dimension
// Input: [batch_size, feature_dim] flattened as row-major
// Output: same shape, normalized per feature vector
void layernorm_kernel(const float* input, float* output, int batch_size, int feature_dim) {
    for (int b = 0; b < batch_size; ++b) {
        const float* row = input + b * feature_dim;
        float* out_row = output + b * feature_dim;

        // Compute mean
        float mean = compute_mean(row, feature_dim);

        // Compute variance
        float var = compute_variance(row, feature_dim, mean);
        float inv_std = 1.0f / std::sqrt(var + EPSILON);

        // Normalize and apply scale/bias (gamma=1, beta=0 for benchmark)
        for (int f = 0; f < feature_dim; ++f) {
            out_row[f] = (row[f] - mean) * inv_std;
        }
    }
}

// Generate deterministic input data for reproducibility
void generate_input_data(float* data, int size, int seed) {
    std::mt19937 gen(seed);
    std::normal_distribution<float> dist(0.0f, 1.0f);
    for (int i = 0; i < size; ++i) {
        data[i] = dist(gen);
    }
}

// Verify output contains no NaN or Inf
bool verify_output(const float* data, int size) {
    for (int i = 0; i < size; ++i) {
        if (std::isnan(data[i]) || std::isinf(data[i])) {
            return false;
        }
    }
    return true;
}

// Write output tensor to binary file
void write_output(const float* data, int size, const std::string& filename) {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "Error: Could not open output file: " << filename << std::endl;
        return;
    }
    // Write size first
    int32_t n = static_cast<int32_t>(size);
    file.write(reinterpret_cast<const char*>(&n), sizeof(n));
    // Write data
    file.write(reinterpret_cast<const char*>(data), size * sizeof(float));
    file.close();
}

// Compute checksum for verification
uint32_t compute_checksum(const float* data, int size) {
    uint32_t hash = 0;
    for (int i = 0; i < size; ++i) {
        uint32_t val;
        std::memcpy(&val, &data[i], sizeof(float));
        hash ^= val;
        hash = (hash << 5) | (hash >> 27);
    }
    return hash;
}

int main(int argc, char* argv[]) {
    // Parse command line arguments for dimensions
    int batch_size = BATCH_SIZE;
    int feature_dim = TENSOR_DIM;
    int iterations = ITERATIONS;
    std::string output_file = "data/intermediates/layernorm_output.bin";

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--batch" && i + 1 < argc) {
            batch_size = std::stoi(argv[++i]);
        } else if (arg == "--dim" && i + 1 < argc) {
            feature_dim = std::stoi(argv[++i]);
        } else if (arg == "--iter" && i + 1 < argc) {
            iterations = std::stoi(argv[++i]);
        } else if (arg == "--output" && i + 1 < argc) {
            output_file = argv[++i];
        } else if (arg == "--help") {
            std::cout << "Usage: " << argv[0] << " [--batch N] [--dim N] [--iter N] [--output FILE]" << std::endl;
            return 0;
        }
    }

    const int total_size = batch_size * feature_dim;

    // Allocate memory
    float* input_data = new float[total_size];
    float* output_data = new float[total_size];

    // Generate input data with fixed seed for reproducibility
    generate_input_data(input_data, total_size, 42);

    // Warmup run
    layernorm_kernel(input_data, output_data, batch_size, feature_dim);

    // Timed benchmark
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        layernorm_kernel(input_data, output_data, batch_size, feature_dim);
    }
    auto end = std::chrono::high_resolution_clock::now();

    // Verify output
    if (!verify_output(output_data, total_size)) {
        std::cerr << "Error: Output contains NaN or Inf!" << std::endl;
        delete[] input_data;
        delete[] output_data;
        return 1;
    }

    // Calculate timing
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double total_time_us = static_cast<double>(duration.count());
    double avg_time_ms = total_time_us / (iterations * 1000.0);

    // Write output
    write_output(output_data, total_size, output_file);

    // Compute checksum
    uint32_t checksum = compute_checksum(output_data, total_size);

    // Output results to stdout for parsing by executor
    std::cout << "{\"median_ms\": " << avg_time_ms << ", \"checksum\": " << checksum << ", \"iterations\": " << iterations << ", \"tensor_dim\": \"" << batch_size << "x" << feature_dim << "\"}" << std::endl;

    // Cleanup
    delete[] input_data;
    delete[] output_data;

    return 0;
}
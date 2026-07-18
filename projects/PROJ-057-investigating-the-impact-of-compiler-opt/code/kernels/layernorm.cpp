/**
 * Layer Normalization Kernel Implementation
 * 
 * Performs LayerNorm on a 2D float32 tensor.
 * Formula: y = (x - mean(x)) / sqrt(var(x) + eps) * gamma + beta
 * For this benchmark, gamma=1.0 and beta=0.0 are used (standard normalization).
 * 
 * Usage: ./layernorm <rows> <cols> <output_file>
 */
#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <cstring>

// Constants
const float EPSILON = 1e-5f;

void run_layer_norm(const int rows, const int cols, const std::string& output_path) {
    // Allocate input data (simulated with a deterministic pattern for reproducibility)
    // In a real scenario, this would be loaded from a file or passed via stdin
    std::vector<float> input(rows * cols);
    std::vector<float> output(rows * cols);
    
    // Fill input with a deterministic pattern to avoid random initialization overhead
    // Pattern: sin(i * j) to ensure non-trivial values
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            input[i * cols + j] = std::sin(static_cast<float>(i) * static_cast<float>(j) * 0.01f);
        }
    }

    // Compute LayerNorm
    for (int i = 0; i < rows; ++i) {
        float sum = 0.0f;
        float sq_sum = 0.0f;
        const int row_start = i * cols;
        
        // First pass: compute mean
        for (int j = 0; j < cols; ++j) {
            sum += input[row_start + j];
        }
        float mean = sum / static_cast<float>(cols);

        // Second pass: compute variance and normalize
        for (int j = 0; j < cols; ++j) {
            float diff = input[row_start + j] - mean;
            sq_sum += diff * diff;
        }
        float variance = sq_sum / static_cast<float>(cols);
        float std_dev = std::sqrt(variance + EPSILON);

        // Normalize and write to output
        for (int j = 0; j < cols; ++j) {
            float diff = input[row_start + j] - mean;
            output[row_start + j] = diff / std_dev;
        }
    }

    // Write output to binary file
    std::ofstream out(output_path, std::ios::binary);
    if (!out.is_open()) {
        std::cerr << "Error: Could not open output file: " << output_path << std::endl;
        return;
    }

    // Write dimensions for verification
    out.write(reinterpret_cast<const char*>(&rows), sizeof(int));
    out.write(reinterpret_cast<const char*>(&cols), sizeof(int));
    
    // Write data
    out.write(reinterpret_cast<const char*>(output.data()), sizeof(float) * rows * cols);
    out.close();
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <rows> <cols> <output_file>" << std::endl;
        return 1;
    }

    int rows = std::atoi(argv[1]);
    int cols = std::atoi(argv[2]);
    std::string output_path = argv[3];

    if (rows <= 0 || cols <= 0) {
        std::cerr << "Error: Invalid dimensions. Rows and cols must be positive." << std::endl;
        return 1;
    }

    run_layer_norm(rows, cols, output_path);

    return 0;
}

#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <random>
#include <algorithm>
#include <cstring>

// Softmax Kernel Implementation for LLM Inference Latency Benchmarking
// Compiles with: g++ -O2 -std=c++17 -o softmax_softmax code/kernels/softmax.cpp
// Supports standard C++17, float32 precision.
// Optimizations (e.g., -ffast-math) can be injected via compiler flags.

// Forward declaration for the kernel function
void run_softmax_kernel(const float* input, float* output, int size);

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <size> <output_file>" << std::endl;
        return 1;
    }

    int size = std::stoi(argv[1]);
    std::string output_file = argv[2];

    // Allocate memory
    float* input = new float[size];
    float* output = new float[size];

    if (!input || !output) {
        std::cerr << "Error: Memory allocation failed for size " << size << std::endl;
        delete[] input;
        delete[] output;
        return 1;
    }

    // Initialize input with deterministic pseudo-random values
    // Using a fixed seed for reproducibility across runs
    std::mt19937 gen(42); 
    std::uniform_real_distribution<> dis(-10.0, 10.0);

    for (int i = 0; i < size; ++i) {
        input[i] = static_cast<float>(dis(gen));
    }

    // Execute the kernel
    run_softmax_kernel(input, output, size);

    // Write results to file
    std::ofstream ofs(output_file, std::ios::binary);
    if (!ofs) {
        std::cerr << "Error: Could not open output file " << output_file << std::endl;
        delete[] input;
        delete[] output;
        return 1;
    }

    // Write header: size
    ofs.write(reinterpret_cast<char*>(&size), sizeof(int));
    // Write data: float array
    ofs.write(reinterpret_cast<char*>(output), size * sizeof(float));
    ofs.close();

    // Cleanup
    delete[] input;
    delete[] output;

    std::cout << "Softmax completed. Output written to " << output_file << std::endl;
    return 0;
}

// Kernel implementation
// Standard Softmax: exp(x_i) / sum(exp(x_j))
// Includes max-subtraction for numerical stability
void run_softmax_kernel(const float* input, float* output, int size) {
    if (size <= 0) return;

    // 1. Find max value for numerical stability
    float max_val = input[0];
    for (int i = 1; i < size; ++i) {
        if (input[i] > max_val) {
            max_val = input[i];
        }
    }

    // 2. Compute exp(x_i - max) and sum
    float sum_exp = 0.0f;
    for (int i = 0; i < size; ++i) {
        float diff = input[i] - max_val;
        // Note: Compiler optimizations like -ffast-math may affect exp() precision
        output[i] = std::exp(diff);
        sum_exp += output[i];
    }

    // 3. Normalize
    // Avoid division by zero if sum_exp is 0 (unlikely with float exp, but safe)
    if (sum_exp == 0.0f) sum_exp = 1.0f; 
    float inv_sum = 1.0f / sum_exp;

    for (int i = 0; i < size; ++i) {
        output[i] *= inv_sum;
    }
}
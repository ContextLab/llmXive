#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <limits>
#include <iomanip>
#include <cstring>

// Softmax Kernel Implementation for LLM Inference Latency Benchmarking
// Compiles with g++/clang++ and supports various optimization flags (-O0 to -O3, -ffast-math, etc.)
// Usage: ./softmax <input_file> <output_file> <num_iterations>
// Input/Output files are raw binary float32 arrays (little-endian)

void softmax(const float* input, float* output, size_t size) {
    float max_val = -std::numeric_limits<float>::infinity();
    
    // Find max for numerical stability
    for (size_t i = 0; i < size; ++i) {
        if (input[i] > max_val) {
            max_val = input[i];
        }
    }

    // Compute exp and sum
    float sum_exp = 0.0f;
    for (size_t i = 0; i < size; ++i) {
        float exp_val = std::exp(input[i] - max_val);
        output[i] = exp_val;
        sum_exp += exp_val;
    }

    // Normalize
    if (sum_exp > 0.0f) {
        for (size_t i = 0; i < size; ++i) {
            output[i] /= sum_exp;
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <input_file> <output_file> <num_iterations>" << std::endl;
        return 1;
    }

    const char* input_file = argv[1];
    const char* output_file = argv[2];
    int num_iterations = std::atoi(argv[3]);

    if (num_iterations <= 0) {
        std::cerr << "Error: num_iterations must be positive" << std::endl;
        return 1;
    }

    // Read input tensor
    std::ifstream in(input_file, std::ios::binary);
    if (!in) {
        std::cerr << "Error: Cannot open input file: " << input_file << std::endl;
        return 1;
    }

    in.seekg(0, std::ios::end);
    size_t file_size = in.tellg();
    in.seekg(0, std::ios::beg);

    size_t num_elements = file_size / sizeof(float);
    if (file_size % sizeof(float) != 0) {
        std::cerr << "Error: Input file size is not a multiple of float size" << std::endl;
        return 1;
    }

    std::vector<float> input_data(num_elements);
    std::vector<float> output_data(num_elements);

    if (!in.read(reinterpret_cast<char*>(input_data.data()), file_size)) {
        std::cerr << "Error: Failed to read input file" << std::endl;
        return 1;
    }
    in.close();

    // Warmup run
    softmax(input_data.data(), output_data.data(), num_elements);

    // Benchmark runs
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < num_iterations; ++i) {
        softmax(input_data.data(), output_data.data(), num_elements);
    }
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    double avg_time_ms = (elapsed.count() / num_iterations) * 1000.0;

    // Write output tensor
    std::ofstream out(output_file, std::ios::binary);
    if (!out) {
        std::cerr << "Error: Cannot open output file: " << output_file << std::endl;
        return 1;
    }
    out.write(reinterpret_cast<char*>(output_data.data()), num_elements * sizeof(float));
    out.close();

    // Output timing to stdout for executor parsing (in milliseconds)
    std::cout << std::fixed << std::setprecision(6) << avg_time_ms << std::endl;

    return 0;
}
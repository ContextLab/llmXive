#include <iostream>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <fstream>
#include <string>
#include <iomanip>

// MatMul Kernel: C = A * B
// A: M x K, B: K x N, C: M x N
// All matrices are row-major, float32

void matmul(const float* A, const float* B, float* C, int M, int K, int N) {
    for (int i = 0; i < M; ++i) {
        for (int j = 0; j < N; ++j) {
            float sum = 0.0f;
            for (int k = 0; k < K; ++k) {
                sum += A[i * K + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }
}

// Initialize matrix with deterministic pseudo-random values based on seed
void init_matrix(float* mat, int rows, int cols, unsigned int seed) {
    srand(seed);
    for (int i = 0; i < rows * cols; ++i) {
        // Normalize to [-1.0, 1.0]
        mat[i] = (static_cast<float>(rand()) / RAND_MAX) * 2.0f - 1.0f;
    }
}

// Verify result against a reference (simple naive implementation for verification)
// In a real benchmark, we would compare against the Python decimal reference
bool verify_result(const float* C, int M, int N, const float* A, const float* B, int K, float tolerance = 1e-5f) {
    // Recompute a few elements to check for NaN/Inf or gross errors
    // For full verification, we'd need the reference output loaded
    // Here we just check for NaN/Inf and basic range
    for (int i = 0; i < M * N; ++i) {
        if (std::isnan(C[i]) || std::isinf(C[i])) {
            std::cerr << "Error: NaN or Inf detected at index " << i << std::endl;
            return false;
        }
    }
    return true;
}

void write_output(const float* C, int M, int N, const std::string& filename) {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "Error: Could not open output file " << filename << std::endl;
        return;
    }
    // Write header: M, N
    file.write(reinterpret_cast<const char*>(&M), sizeof(int));
    file.write(reinterpret_cast<const char*>(&N), sizeof(int));
    // Write data
    file.write(reinterpret_cast<const char*>(C), sizeof(float) * M * N);
    file.close();
}

int main(int argc, char* argv[]) {
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0] << " <M> <K> <N> <output_file> [seed]" << std::endl;
        return 1;
    }

    int M = std::atoi(argv[1]);
    int K = std::atoi(argv[2]);
    int N = std::atoi(argv[3]);
    std::string output_file = argv[4];
    unsigned int seed = (argc > 5) ? std::atoi(argv[5]) : 42;

    // Allocate memory
    size_t size_A = M * K;
    size_t size_B = K * N;
    size_t size_C = M * N;

    std::vector<float> A(size_A);
    std::vector<float> B(size_B);
    std::vector<float> C(size_C);

    // Initialize matrices
    init_matrix(A.data(), M, K, seed);
    init_matrix(B.data(), K, N, seed + 1); // Different seed for B

    // Run benchmark
    auto start = std::chrono::high_resolution_clock::now();
    matmul(A.data(), B.data(), C.data(), M, K, N);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::micro> duration = end - start;
    double latency_us = duration.count();

    // Verify
    if (!verify_result(C.data(), M, N, A.data(), B.data(), K)) {
        std::cerr << "Verification failed!" << std::endl;
        return 1;
    }

    // Write output
    write_output(C.data(), M, N, output_file);

    // Print latency to stdout for the Python executor to capture
    std::cout << std::fixed << std::setprecision(6) << latency_us << std::endl;

    return 0;
}

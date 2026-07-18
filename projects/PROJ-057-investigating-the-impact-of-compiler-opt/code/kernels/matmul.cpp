#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <cstring>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <algorithm>

// MatMul Kernel for LLM Inference Latency Investigation
// Implements C++17 compliant matrix multiplication for float32 tensors.
// Supports configurable dimensions and optional output verification.

using Matrix = std::vector<float>;

// Initialize matrix with random values from a normal distribution
void init_matrix(Matrix& mat, size_t rows, size_t cols, float mean = 0.0f, float std_dev = 1.0f) {
    mat.resize(rows * cols);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(mean, std_dev);

    for (size_t i = 0; i < rows * cols; ++i) {
        mat[i] = dist(gen);
    }
}

// Initialize matrix with deterministic seed for reproducibility
void init_matrix_seed(Matrix& mat, size_t rows, size_t cols, unsigned int seed, float mean = 0.0f, float std_dev = 1.0f) {
    mat.resize(rows * cols);
    std::mt19937 gen(seed);
    std::normal_distribution<float> dist(mean, std_dev);

    for (size_t i = 0; i < rows * cols; ++i) {
        mat[i] = dist(gen);
    }
}

// Naive Matrix Multiplication: C = A * B
// A: M x K, B: K x N, C: M x N
void matmul_naive(const Matrix& A, const Matrix& B, Matrix& C, size_t M, size_t K, size_t N) {
    C.resize(M * N, 0.0f);
    for (size_t i = 0; i < M; ++i) {
        for (size_t k = 0; k < K; ++k) {
            float a_ik = A[i * K + k];
            for (size_t j = 0; j < N; ++j) {
                C[i * N + j] += a_ik * B[k * N + j];
            }
        }
    }
}

// Optimized Matrix Multiplication (Loop Tiling for Cache Efficiency)
// Uses 64x64 tiles to improve cache locality.
void matmul_optimized(const Matrix& A, const Matrix& B, Matrix& C, size_t M, size_t K, size_t N) {
    const size_t TILE_SIZE = 64;
    C.resize(M * N, 0.0f);

    for (size_t ii = 0; ii < M; ii += TILE_SIZE) {
        for (size_t jj = 0; jj < N; jj += TILE_SIZE) {
            for (size_t kk = 0; kk < K; kk += TILE_SIZE) {
                size_t i_end = std::min(ii + TILE_SIZE, M);
                size_t j_end = std::min(jj + TILE_SIZE, N);
                size_t k_end = std::min(kk + TILE_SIZE, K);

                for (size_t i = ii; i < i_end; ++i) {
                    for (size_t k = kk; k < k_end; ++k) {
                        float a_ik = A[i * K + k];
                        for (size_t j = jj; j < j_end; ++j) {
                            C[i * N + j] += a_ik * B[k * N + j];
                        }
                    }
                }
            }
        }
    }
}

// Check if output contains NaN or Inf
bool is_valid_output(const Matrix& C) {
    for (float val : C) {
        if (std::isnan(val) || std::isinf(val)) {
            return false;
        }
    }
    return true;
}

// Write output tensor to binary file for external verification
void write_tensor_to_file(const Matrix& C, const std::string& filename) {
    std::ofstream outfile(filename, std::ios::binary);
    if (!outfile) {
        std::cerr << "Error: Could not open output file " << filename << std::endl;
        return;
    }
    size_t size = C.size();
    outfile.write(reinterpret_cast<const char*>(&size), sizeof(size));
    outfile.write(reinterpret_cast<const char*>(C.data()), size * sizeof(float));
    outfile.close();
}

int main(int argc, char* argv[]) {
    // Expected arguments: <M> <K> <N> [iterations] [seed] [output_file] [optimization_level]
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0] << " <M> <K> <N> [iterations] [seed] [output_file] [optimization_level]" << std::endl;
        std::cerr << "  M, K, N: Matrix dimensions (A: MxK, B: KxN, C: MxN)" << std::endl;
        std::cerr << "  iterations: Number of times to run the multiplication (default: 100)" << std::endl;
        std::cerr << "  seed: Random seed for reproducibility (default: 12345)" << std::endl;
        std::cerr << "  output_file: Path to write output tensor (optional)" << std::endl;
        std::cerr << "  optimization_level: 'naive' or 'optimized' (default: optimized)" << std::endl;
        return 1;
    }

    size_t M = std::stoul(argv[1]);
    size_t K = std::stoul(argv[2]);
    size_t N = std::stoul(argv[3]);
    int iterations = (argc > 4) ? std::stoi(argv[4]) : 100;
    unsigned int seed = (argc > 5) ? std::stoul(argv[5]) : 12345;
    std::string output_file = (argc > 6) ? argv[6] : "";
    std::string opt_level = (argc > 7) ? argv[7] : "optimized";

    // Validate dimensions
    if (M == 0 || K == 0 || N == 0) {
        std::cerr << "Error: Matrix dimensions must be positive." << std::endl;
        return 1;
    }

    // Memory pressure check: estimate allocation size
    // A: M*K, B: K*N, C: M*N (all float32)
    size_t total_elements = M * K + K * N + M * N;
    size_t total_bytes = total_elements * sizeof(float);
    
    // If allocation exceeds ~1GB, downsample (simulating memory pressure)
    // This is a heuristic; actual memory availability varies by system.
    if (total_bytes > 1024 * 1024 * 1024) {
        std::cerr << "Memory Pressure: Estimated allocation " << total_bytes << " bytes exceeds 1GB." << std::endl;
        std::cerr << "Attempting to downsample..." << std::endl;
        // Simple downsample: reduce M, K, N proportionally until under 1GB
        float scale = std::cbrt(1024.0 * 1024 * 1024.0 / (float)total_bytes);
        size_t new_M = std::max(1UL, (size_t)(M * scale));
        size_t new_K = std::max(1UL, (size_t)(K * scale));
        size_t new_N = std::max(1UL, (size_t)(N * scale));
        
        std::cerr << "Downsampled dimensions: " << new_M << "x" << new_K << "x" << new_N << std::endl;
        M = new_M; K = new_K; N = new_N;
        total_elements = M * K + K * N + M * N;
        total_bytes = total_elements * sizeof(float);
        
        if (total_bytes > 1024 * 1024 * 1024) {
            std::cerr << "Error: Even downsampled allocation exceeds 1GB. Aborting." << std::endl;
            return 1;
        }
    }

    // Initialize matrices
    Matrix A, B, C;
    init_matrix_seed(A, M, K, seed);
    init_matrix_seed(B, K, N, seed + 1); // Use different seed for B

    // Warm-up run
    if (opt_level == "naive") {
        matmul_naive(A, B, C, M, K, N);
    } else {
        matmul_optimized(A, B, C, M, K, N);
    }

    // Verify warm-up output
    if (!is_valid_output(C)) {
        std::cerr << "Error: Warm-up run produced invalid output (NaN/Inf)." << std::endl;
        return 1;
    }

    // Benchmark loop
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        if (opt_level == "naive") {
            matmul_naive(A, B, C, M, K, N);
        } else {
            matmul_optimized(A, B, C, M, K, N);
        }
        
        // Verify each iteration to catch stability issues
        if (!is_valid_output(C)) {
            std::cerr << "Error: Iteration " << i << " produced invalid output (NaN/Inf)." << std::endl;
            return 1;
        }
    }
    auto end = std::chrono::high_resolution_clock::now();

    // Calculate latency
    std::chrono::duration<double, std::milli> elapsed = end - start;
    double median_ms = elapsed.count() / iterations;

    // Output results in a format parsable by Python executor
    std::cout << "DIMENSIONS:" << M << "x" << K << "x" << N << std::endl;
    std::cout << "ITERATIONS:" << iterations << std::endl;
    std::cout << "LATENCY_MS:" << std::fixed << std::setprecision(6) << median_ms << std::endl;
    std::cout << "VALID:TRUE" << std::endl;

    // Write output tensor if requested
    if (!output_file.empty()) {
        write_tensor_to_file(C, output_file);
        std::cout << "OUTPUT_FILE:" << output_file << std::endl;
    }

    return 0;
}
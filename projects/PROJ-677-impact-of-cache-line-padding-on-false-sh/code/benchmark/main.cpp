#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <atomic>
#include <chrono>
#include <fstream>
#include <sstream>
#include <iomanip>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Function to parse command line arguments
bool parse_args(int argc, char* argv[], int& thread_count, std::string& config_type, int& iterations) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <thread_count> <config_type> <iterations>" << std::endl;
        std::cerr << "  thread_count: Number of threads (e.g., 1, 2, 4, 8)" << std::endl;
        std::cerr << "  config_type: 'packed' or 'padded'" << std::endl;
        std::cerr << "  iterations: Number of increments per thread" << std::endl;
        return false;
    }

    try {
        thread_count = std::stoi(argv[1]);
        if (thread_count < 1) {
            std::cerr << "Error: thread_count must be >= 1" << std::endl;
            return false;
        }

        config_type = argv[2];
        if (config_type != "packed" && config_type != "padded") {
            std::cerr << "Error: config_type must be 'packed' or 'padded'" << std::endl;
            return false;
        }

        iterations = std::stoi(argv[3]);
        if (iterations < 1) {
            std::cerr << "Error: iterations must be >= 1" << std::endl;
            return false;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error parsing arguments: " << e.what() << std::endl;
        return false;
    }

    return true;
}

// Single-threaded validation to ensure atomic increments are not optimized away
// This runs before multi-threaded execution to verify correctness and prevent compiler optimizations
bool validate_single_threaded(const std::string& config_type, int iterations) {
    std::cout << "Running single-threaded validation..." << std::endl;

    if (config_type == "packed") {
        // Use packed counters for validation
        std::vector<PackedCounter> counters(1);
        std::atomic<long> total{0};

        // Perform increments
        for (int i = 0; i < iterations; ++i) {
            counters[0].increment();
            total.fetch_add(1, std::memory_order_relaxed);
        }

        // Verify results
        if (counters[0].value != iterations) {
            std::cerr << "Validation FAILED: Expected " << iterations 
                      << " but got " << counters[0].value << std::endl;
            return false;
        }

        if (total.load() != iterations) {
            std::cerr << "Validation FAILED: Total atomic mismatch. Expected " 
                      << iterations << " but got " << total.load() << std::endl;
            return false;
        }

        std::cout << "Single-threaded validation PASSED for packed config." << std::endl;

    } else if (config_type == "padded") {
        // Use padded counters for validation
        std::vector<PaddedCounter> counters(1);
        std::atomic<long> total{0};

        // Perform increments
        for (int i = 0; i < iterations; ++i) {
            counters[0].increment();
            total.fetch_add(1, std::memory_order_relaxed);
        }

        // Verify results
        if (counters[0].value != iterations) {
            std::cerr << "Validation FAILED: Expected " << iterations 
                      << " but got " << counters[0].value << std::endl;
            return false;
        }

        if (total.load() != iterations) {
            std::cerr << "Validation FAILED: Total atomic mismatch. Expected " 
                      << iterations << " but got " << total.load() << std::endl;
            return false;
        }

        std::cout << "Single-threaded validation PASSED for padded config." << std::endl;
    }

    return true;
}

// Multi-threaded benchmark execution
void run_benchmark(int thread_count, const std::string& config_type, int iterations, double& wall_clock_time_ms) {
    std::cout << "Running benchmark: " << thread_count << " threads, " 
              << config_type << " config, " << iterations << " iterations/thread" << std::endl;

    std::vector<std::thread> workers;
    std::vector<void*> counter_array;
    
    // Allocate counters based on configuration
    if (config_type == "packed") {
        auto* packed_counters = new PackedCounter[thread_count];
        counter_array.resize(thread_count);
        for (int i = 0; i < thread_count; ++i) {
            counter_array[i] = &packed_counters[i];
        }
    } else {
        auto* padded_counters = new PaddedCounter[thread_count];
        counter_array.resize(thread_count);
        for (int i = 0; i < thread_count; ++i) {
            counter_array[i] = &padded_counters[i];
        }
    }

    auto start = std::chrono::high_resolution_clock::now();

    // Launch threads
    for (int t = 0; t < thread_count; ++t) {
        workers.emplace_back([&, t]() {
            if (config_type == "packed") {
                auto* packed_counters = static_cast<PackedCounter*>(counter_array[0]);
                for (int i = 0; i < iterations; ++i) {
                    packed_counters[t].increment();
                }
            } else {
                auto* padded_counters = static_cast<PaddedCounter*>(counter_array[0]);
                for (int i = 0; i < iterations; ++i) {
                    padded_counters[t].increment();
                }
            }
        });
    }

    // Wait for all threads to complete
    for (auto& worker : workers) {
        worker.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> duration = end - start;
    wall_clock_time_ms = duration.count();

    // Cleanup
    if (config_type == "packed") {
        delete[] static_cast<PackedCounter*>(counter_array[0]);
    } else {
        delete[] static_cast<PaddedCounter*>(counter_array[0]);
    }

    std::cout << "Benchmark completed in " << wall_clock_time_ms << " ms" << std::endl;
}

int main(int argc, char* argv[]) {
    int thread_count;
    std::string config_type;
    int iterations;

    // Parse arguments
    if (!parse_args(argc, argv, thread_count, config_type, iterations)) {
        return 1;
    }

    // Step 1: Single-threaded validation (FR-004)
    // This ensures atomic increments are not optimized away by the compiler
    if (!validate_single_threaded(config_type, iterations)) {
        std::cerr << "Single-threaded validation failed. Aborting benchmark." << std::endl;
        return 1;
    }

    // Step 2: Run multi-threaded benchmark
    double wall_clock_time_ms = 0.0;
    run_benchmark(thread_count, config_type, iterations, wall_clock_time_ms);

    // Step 3: Output results to CSV (format: thread_count,config,iterations,time_ms)
    std::cout << thread_count << "," << config_type << "," << iterations 
              << "," << std::fixed << std::setprecision(3) << wall_clock_time_ms << std::endl;

    return 0;
}
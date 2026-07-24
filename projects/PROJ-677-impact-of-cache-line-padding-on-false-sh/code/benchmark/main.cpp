#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <sstream>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

void worker_packed(PackedCounter* counters, int thread_id, long iterations) {
    for (long i = 0; i < iterations; ++i) {
        counters[thread_id].value.fetch_add(1, std::memory_order_relaxed);
    }
}

void worker_padded(PaddedCounter* counters, int thread_id, long iterations) {
    for (long i = 0; i < iterations; ++i) {
        counters[thread_id].value.fetch_add(1, std::memory_order_relaxed);
    }
}

double run_benchmark(int thread_count, bool use_padded, long iterations_per_thread) {
    if (use_padded) {
        std::vector<PaddedCounter> counters(thread_count);
        std::vector<std::thread> threads;

        auto start = std::chrono::high_resolution_clock::now();

        for (int i = 0; i < thread_count; ++i) {
            threads.emplace_back(worker_padded, counters.data(), i, iterations_per_thread);
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(end - start).count();
    } else {
        std::vector<PackedCounter> counters(thread_count);
        std::vector<std::thread> threads;

        auto start = std::chrono::high_resolution_clock::now();

        for (int i = 0; i < thread_count; ++i) {
            threads.emplace_back(worker_packed, counters.data(), i, iterations_per_thread);
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(end - start).count();
    }
}

void write_csv(const std::string& filename, int thread_count, bool use_padded, 
               long iterations, double time_ms) {
    std::ofstream file(filename, std::ios::app);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        return;
    }

    std::string config = use_padded ? "padded" : "packed";
    file << thread_count << "," << config << "," << iterations << "," << time_ms << std::endl;
    file.close();
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <thread_count> <config(packed/padded)> <iterations>" << std::endl;
        return 1;
    }

    int thread_count = std::atoi(argv[1]);
    std::string config = argv[2];
    long iterations = std::atol(argv[3]);

    if (thread_count <= 0 || iterations <= 0) {
        std::cerr << "Error: Invalid arguments" << std::endl;
        return 1;
    }

    bool use_padded = (config == "padded");

    // Run single test
    double time_ms = run_benchmark(thread_count, use_padded, iterations);

    // Output to stdout for verification
    std::cout << "Thread count: " << thread_count << ", Config: " << config 
              << ", Iterations: " << iterations << ", Time (ms): " << time_ms << std::endl;

    // Write to CSV
    std::string csv_file = "data/benchmark_results.csv";
    write_csv(csv_file, thread_count, use_padded, iterations, time_ms);

    return 0;
}

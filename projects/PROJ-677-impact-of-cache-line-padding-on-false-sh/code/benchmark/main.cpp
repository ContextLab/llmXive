#include <iostream>
#include <fstream>
#include <chrono>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <cstring>
#include <cstdlib>
#include <iomanip>
#include <sstream>

// Include counter definitions
#include "counter_packed.hpp"
#include "counter_padded.hpp"

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " <thread_count> <config_type> <iterations>" << std::endl;
    std::cerr << "  thread_count: Number of threads (e.g., 1, 2, 4, 8)" << std::endl;
    std::cerr << "  config_type: 'packed' or 'padded'" << std::endl;
    std::cerr << "  iterations: Number of increments per thread" << std::endl;
}

template <typename CounterStruct>
void run_benchmark(int thread_count, long long iterations, const std::string& config_type, const std::string& output_file) {
    // Allocate shared array of structs
    // Each thread will write to a distinct element to isolate false sharing effects
    std::vector<CounterStruct> counters(thread_count);
    
    // Initialize counters to zero
    for (int i = 0; i < thread_count; ++i) {
        counters[i].value = 0;
    }

    std::atomic<bool> start_flag(false);
    std::vector<std::thread> workers;
    
    auto start_time = std::chrono::high_resolution_clock::now();

    // Launch threads
    for (int i = 0; i < thread_count; ++i) {
        workers.emplace_back([&counters, &start_flag, iterations, i]() {
            // Wait for the start signal to ensure simultaneous start
            while (!start_flag.load(std::memory_order_acquire)) {
                std::this_thread::yield();
            }
            
            // Perform increments
            for (long long j = 0; j < iterations; ++j) {
                counters[i].value++;
            }
        });
    }

    // Signal all threads to start
    start_flag.store(true, std::memory_order_release);

    // Wait for all threads to complete
    for (auto& worker : workers) {
        worker.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    double wall_clock_ms = elapsed.count();

    // Append results to CSV
    std::ofstream file(output_file, std::ios::app);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open output file: " << output_file << std::endl;
        return;
    }

    // Write CSV row: thread_count, configuration, iteration_count, wall_clock_time_ms
    file << thread_count << "," << config_type << "," << iterations << "," << std::fixed << std::setprecision(4) << wall_clock_ms << "\n";
    
    file.close();

    // Optional: Print to stdout for immediate feedback
    std::cout << "Completed: " << thread_count << " threads, " 
              << config_type << ", " << iterations << " iterations, " 
              << wall_clock_ms << " ms" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        print_usage(argv[0]);
        return 1;
    }

    int thread_count = std::atoi(argv[1]);
    std::string config_type = argv[2];
    long long iterations = std::atoll(argv[3]);

    if (thread_count <= 0 || iterations <= 0) {
        std::cerr << "Error: Invalid arguments. Thread count and iterations must be positive." << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    // Determine struct type based on config
    if (config_type != "packed" && config_type != "padded") {
        std::cerr << "Error: Invalid config_type. Must be 'packed' or 'padded'." << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    // Output file path (matches tasks.md requirement)
    std::string output_file = "data/benchmark_results.csv";
    
    // Ensure header exists if file is new (simple check: if file doesn't exist, write header)
    std::ifstream check_file(output_file);
    if (!check_file.good()) {
        std::ofstream init_file(output_file);
        init_file << "thread_count,configuration,iteration_count,wall_clock_time_ms\n";
        init_file.close();
    }
    check_file.close();

    if (config_type == "packed") {
        run_benchmark<CounterPacked>(thread_count, iterations, config_type, output_file);
    } else {
        run_benchmark<CounterPadded>(thread_count, iterations, config_type, output_file);
    }

    return 0;
}

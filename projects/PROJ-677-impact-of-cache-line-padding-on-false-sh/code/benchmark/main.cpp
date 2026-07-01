#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <thread>
#include <vector>

#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Constants for the benchmark
constexpr size_t NUM_INCREMENTS = 10000000; // 10 million increments per thread
constexpr size_t WARMUP_INCREMENTS = 100000; // 100k warmup

template <typename CounterType>
void run_single_threaded_validation() {
    std::cout << "Running single-threaded validation for " 
              << (std::is_same_v<CounterType, PackedCounter> ? "Packed" : "Padded") 
              << " counter..." << std::endl;

    // Allocate array of counters. 
    // Packed: 24 bytes, Padded: >= 192 bytes (64 bytes alignment * 3 fields roughly)
    // We allocate enough space to hold 100 counters to ensure distinct cache lines if padded.
    constexpr size_t NUM_COUNTERS = 100;
    
    // Use alignas to ensure the array itself is aligned if necessary, though the struct alignment handles internal layout.
    alignas(64) CounterType counters[NUM_COUNTERS];

    // Initialize counters to 0 (atomic default constructor handles this, but explicit for clarity)
    for (size_t i = 0; i < NUM_COUNTERS; ++i) {
        counters[i].value.store(0, std::memory_order_relaxed);
    }

    // Warmup phase
    for (size_t i = 0; i < WARMUP_INCREMENTS; ++i) {
        counters[0].increment();
    }

    // Reset for measurement
    for (size_t i = 0; i < NUM_COUNTERS; ++i) {
        counters[i].value.store(0, std::memory_order_relaxed);
    }

    // Measurement phase
    auto start = std::chrono::high_resolution_clock::now();
    
    // Perform increments on a single counter to ensure no false sharing during this specific check
    // The thread count logic in main will handle multi-threaded distribution.
    // Here we just verify the atomic increment works and isn't optimized away.
    for (size_t i = 0; i < NUM_INCREMENTS; ++i) {
        counters[0].increment();
    }

    auto end = std::chrono::high_resolution_clock::now();
    
    // Read result
    long long final_value = counters[0].value.load(std::memory_order_relaxed);

    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Validation Result:" << std::endl;
    std::cout << "  Expected increments: " << NUM_INCREMENTS << std::endl;
    std::cout << "  Actual value: " << final_value << std::endl;
    std::cout << "  Time: " << duration.count() << " microseconds" << std::endl;

    if (final_value != static_cast<long long>(NUM_INCREMENTS)) {
        std::cerr << "ERROR: Atomic increment validation failed! Expected " 
                  << NUM_INCREMENTS << " but got " << final_value << std::endl;
        std::exit(1);
    }

    // Prevent compiler optimization of the result variable
    volatile long long sink = final_value;
    (void)sink;

    std::cout << "  [PASS] Single-threaded atomic increment validation successful." << std::endl;
}

void print_usage(const char* prog_name) {
    std::cerr << "Usage: " << prog_name << " --validate-single [--type packed|padded]" << std::endl;
    std::cerr << "       " << prog_name << " --benchmark --threads <N> --type packed|padded [--output <file>]" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        print_usage(argv[0]);
        return 1;
    }

    std::string mode = argv[1];
    
    if (mode == "--validate-single") {
        std::string type_str = "padded"; // Default
        for (int i = 2; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--type" && i + 1 < argc) {
                type_str = argv[++i];
            }
        }

        if (type_str == "packed") {
            run_single_threaded_validation<PackedCounter>();
        } else if (type_str == "padded") {
            run_single_threaded_validation<PaddedCounter>();
        } else {
            std::cerr << "Error: Invalid type. Use 'packed' or 'padded'." << std::endl;
            return 1;
        }
        return 0;
    } 
    else if (mode == "--benchmark") {
        // Placeholder for multi-threaded benchmark logic (T021)
        // This block ensures the binary compiles and runs but the actual 
        // multi-threading logic is implemented in T021.
        std::cerr << "Multi-threaded benchmark mode (--benchmark) is not yet implemented in this task (T016)." << std::endl;
        std::cerr << "Please run with --validate-single to verify atomic operations." << std::endl;
        return 1; // Return non-zero to indicate this mode is not ready, but not a crash
    }
    else {
        print_usage(argv[0]);
        return 1;
    }

    return 0;
}
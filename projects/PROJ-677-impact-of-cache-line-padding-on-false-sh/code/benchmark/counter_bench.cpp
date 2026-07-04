#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <string>
#include <algorithm>

// Include headers for struct definitions
// We assume these are defined in counter_packed.hpp and counter_padded.hpp
// Since we are implementing the binary, we include the logic directly or via headers
// For this task, we define the structs inline to ensure the code is self-contained
// as per the task requirement to implement the binary logic.

#include <cstddef>

// Packed Counter (FR-007, T007)
#pragma pack(push, 1)
struct CounterPacked {
    long value;
    char padding[8]; // To make it larger than just long, simulating false sharing risk
};
#pragma pack(pop)

// Padded Counter (FR-007, T007)
struct CounterPadded {
    alignas(64) long value; // 64-byte alignment for cache line
    char padding[64]; // Ensure it spans a cache line or more
};

void run_benchmark(int thread_count, const std::string& config, long iterations) {
    // Allocate array of counters
    // Each thread will write to a distinct element to avoid data races on the value itself,
    // but we are testing cache line padding impact on false sharing if they were close.
    // In this specific test, we allocate them contiguously.
    
    // Use a large enough array to avoid stack overflow
    std::vector<CounterPacked> packed_counters(thread_count);
    std::vector<CounterPadded> padded_counters(thread_count);
    
    void* work_array = nullptr;
    size_t struct_size = 0;

    if (config == "packed") {
        struct_size = sizeof(CounterPacked);
        // Cast the vector data to the base pointer for uniform access if needed,
        // but here we just use the specific type.
        // We will use a union or void* to pass to threads, but simpler to just template or use a lambda capture.
        // Let's use a generic worker that takes a pointer and stride.
    } else if (config == "padded") {
        struct_size = sizeof(CounterPadded);
    } else {
        std::cerr << "Unknown config: " << config << std::endl;
        exit(1);
    }

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    threads.reserve(thread_count);

    if (config == "packed") {
        for (int i = 0; i < thread_count; ++i) {
            threads.emplace_back([&, i]() {
                for (long j = 0; j < iterations; ++j) {
                    packed_counters[i].value++;
                }
            });
        }
    } else {
        for (int i = 0; i < thread_count; ++i) {
            threads.emplace_back([&, i]() {
                for (long j = 0; j < iterations; ++j) {
                    padded_counters[i].value++;
                }
            });
        }
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> duration = end - start;

    // Output format for parsing by run_benchmarks.sh
    // We print the time in ms.
    std::cout << "time_ms: " << duration.count() << std::endl;
}

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " --threads <N> --config <packed|padded> --iterations <N>" << std::endl;
}

int main(int argc, char* argv[]) {
    int thread_count = 1;
    std::string config = "packed";
    long iterations = 1000000;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--threads" && i + 1 < argc) {
            thread_count = std::atoi(argv[++i]);
        } else if (arg == "--config" && i + 1 < argc) {
            config = argv[++i];
        } else if (arg == "--iterations" && i + 1 < argc) {
            iterations = std::atol(argv[++i]);
        } else if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
    }

    if (thread_count < 1) {
        std::cerr << "Thread count must be >= 1" << std::endl;
        return 1;
    }

    run_benchmark(thread_count, config, iterations);
    return 0;
}

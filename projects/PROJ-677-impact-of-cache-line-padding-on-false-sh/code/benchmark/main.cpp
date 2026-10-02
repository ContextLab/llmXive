#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <cstdlib>
#include <getopt.h>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Constants
const long ITERATIONS_PER_THREAD = 10000000;
const int NUM_RUNS = 5;

// Global variables for benchmark
std::atomic<long>* counters = nullptr;
int thread_count = 0;
std::string config = "packed";

void worker_thread(int thread_id, long iterations) {
    // Each thread writes to its own distinct element in the array
    // For packed: elements are adjacent (64 bytes total for 3 longs), causing false sharing
    // For padded: elements are 64-byte aligned, preventing false sharing
    if (config == "packed") {
        // Use packed counters - false sharing will occur
        CounterPacked* packed_counters = reinterpret_cast<CounterPacked*>(counters);
        for (long i = 0; i < iterations; ++i) {
            packed_counters[thread_id].c1++;
        }
    } else {
        // Use padded counters - no false sharing
        CounterPadded* padded_counters = reinterpret_cast<CounterPadded*>(counters);
        for (long i = 0; i < iterations; ++i) {
            padded_counters[thread_id].c1++;
        }
    }
}

void run_benchmark() {
    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    for (int i = 0; i < thread_count; ++i) {
        threads.emplace_back(worker_thread, i, ITERATIONS_PER_THREAD);
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double wall_clock_time_ms = duration.count() / 1000.0;

    // Output results
    std::cout << thread_count << "," << config << "," << ITERATIONS_PER_THREAD << "," << wall_clock_time_ms << std::endl;
}

void print_usage(const char* program_name) {
    std::cerr << "Usage: " << program_name << " --threads <N> --config <packed|padded>" << std::endl;
    std::cerr << "  --threads, -t <N>    Number of threads (1-8)" << std::endl;
    std::cerr << "  --config, -c <type>  Configuration: 'packed' or 'padded'" << std::endl;
    std::cerr << "  --help, -h           Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    int opt;
    int threads = 0;
    std::string config_type = "packed";

    static struct option long_options[] = {
        {"threads", required_argument, 0, 't'},
        {"config", required_argument, 0, 'c'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    while ((opt = getopt_long(argc, argv, "t:c:h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 't':
                threads = std::atoi(optarg);
                break;
            case 'c':
                config_type = std::string(optarg);
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }

    if (threads < 1 || threads > 8) {
        std::cerr << "Error: Thread count must be between 1 and 8" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    if (config_type != "packed" && config_type != "padded") {
        std::cerr << "Error: Config must be 'packed' or 'padded'" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    thread_count = threads;
    config = config_type;

    // Allocate counter array
    // For packed: sizeof(CounterPacked) = 24 bytes, so 8 threads need 192 bytes
    // For padded: sizeof(CounterPadded) >= 192 bytes (64 bytes per counter * 3 counters)
    int counter_size = (config == "packed") ? sizeof(CounterPacked) : sizeof(CounterPadded);
    counters = new std::atomic<long>[thread_count * counter_size];

    // Initialize counters to zero
    for (int i = 0; i < thread_count * counter_size; ++i) {
        counters[i].store(0);
    }

    // Run benchmark multiple times and output results
    for (int run = 0; run < NUM_RUNS; ++run) {
        run_benchmark();
    }

    delete[] counters;
    return 0;
}
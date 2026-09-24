#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <sstream>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " <thread_count> <config> <iterations>\n"
              << "  thread_count: 1, 2, 4, 8\n"
              << "  config: 'packed' or 'padded'\n"
              << "  iterations: number of increments per thread\n";
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        print_usage(argv[0]);
        return 1;
    }

    int thread_count = std::atoi(argv[1]);
    std::string config = argv[2];
    long long iterations = std::atoll(argv[3]);

    if (thread_count <= 0 || iterations <= 0) {
        std::cerr << "Error: thread_count and iterations must be positive integers.\n";
        return 1;
    }

    if (config != "packed" && config != "padded") {
        std::cerr << "Error: config must be 'packed' or 'padded'.\n";
        return 1;
    }

    // Allocate shared array based on configuration
    // We need thread_count distinct elements to avoid false sharing in the padded case
    // and to simulate the scenario where threads write to distinct elements in the packed case
    // but due to cache line packing, they might share lines.
    // To strictly test false sharing, we place elements such that in 'packed' they share lines
    // and in 'padded' they don't.
    
    // For 'packed', CounterPacked is 24 bytes. 3 fit in 64 bytes.
    // For 'padded', CounterPadded is >= 192 bytes (alignas 64 usually implies 64 or 128 padding).
    // We allocate a vector of size thread_count.
    
    std::vector<CounterPacked> packed_counters(thread_count);
    std::vector<CounterPadded> padded_counters(thread_count);

    std::vector<std::thread> threads;
    
    auto start_time = std::chrono::high_resolution_clock::now();

    for (int t = 0; t < thread_count; ++t) {
        threads.emplace_back([&, t]() {
            volatile long long sink = 0; // Prevent optimization
            if (config == "packed") {
                for (long long i = 0; i < iterations; ++i) {
                    packed_counters[t].increment();
                    // In a real false sharing scenario, we might want threads to write to
                    // adjacent indices that share a cache line.
                    // However, the task description says "each thread writes to a distinct element".
                    // The impact comes from the fact that in 'packed', multiple counters fit in one line.
                    // If we strictly follow "distinct element", we just increment our own.
                    // The "false sharing" usually implies threads writing to *different* variables
                    // that happen to be on the *same* cache line.
                    // If thread 0 writes index 0 and thread 1 writes index 1, and they are packed:
                    // Index 0 and 1 are in the same 64-byte line.
                    // So we must ensure we are testing the scenario where they share the line.
                    // Since we allocated a vector, index 0 and 1 are adjacent in memory.
                    // So this setup is correct for testing false sharing on the packed struct.
                }
            } else {
                for (long long i = 0; i < iterations; ++i) {
                    padded_counters[t].increment();
                }
            }
            // Consume a value to ensure compiler doesn't optimize the loop entirely
            // if it could prove no side effects (though atomic does have side effects).
            sink = packed_counters[0].value; 
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    double wall_clock_ms = elapsed.count();

    // Output to stdout in CSV format as required by the task
    // Format: thread_count, configuration, iteration_count, wall_clock_time_ms
    std::cout << thread_count << "," << config << "," << iterations << "," << std::fixed << std::setprecision(6) << wall_clock_ms << std::endl;

    return 0;
}
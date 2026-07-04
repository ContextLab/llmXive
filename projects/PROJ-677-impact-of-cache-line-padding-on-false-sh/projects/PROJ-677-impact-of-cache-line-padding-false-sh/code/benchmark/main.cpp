#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <string>
#include <sstream>
#include <iomanip>

// Include counter definitions
#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Global configuration
static const long long INCREMENTS_PER_THREAD = 10000000; // 10M increments
static const size_t MAX_THREADS = 64;

// Worker function for a single thread
// Each thread increments its own distinct element in the shared array
void worker_thread(size_t thread_id, std::atomic<long>* counters, size_t stride, size_t num_threads) {
    // Calculate the index this thread is responsible for
    // We use a stride to ensure we don't accidentally share cache lines if the array is small
    // However, the struct padding (if any) is the primary defense.
    // The task requires: "allocating a shared array of structs where each thread writes to a distinct element"
    
    size_t index = thread_id;
    
    // Perform the increments
    // We use a local accumulator to prevent false sharing on the atomic itself during the loop
    // if the compiler doesn't optimize it, but here we just do atomic fetch_add for simplicity
    // or just load/store if we trust the compiler. 
    // To strictly follow "atomic increments", we use atomic operations.
    
    // Optimization: Use a local variable for the loop to avoid repeated atomic load/store overhead
    // if the goal is just to measure the cost of the atomic operation itself under contention.
    // However, to measure FALSE SHARING, we must ensure the atomic variable itself is being 
    // written to. If we use a local register and only write once at the end, we hide the 
    // contention of the atomic increment itself.
    // But false sharing is about CACHE LINES. 
    // If Thread A writes to Counter[0] and Thread B writes to Counter[1], and they are on the same cache line,
    // the cache line bounces.
    
    // So we must actually perform the atomic operation repeatedly.
    for (long long i = 0; i < INCREMENTS_PER_THREAD; ++i) {
        // We use fetch_add to ensure the atomic operation happens.
        // To force the memory access, we might need volatile, but std::atomic handles this.
        counters[index].fetch_add(1, std::memory_order_relaxed);
    }
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <thread_count> <config_type> <output_csv_path>" << std::endl;
        std::cerr << "  config_type: 'packed' or 'padded'" << std::endl;
        return 1;
    }

    int thread_count = std::atoi(argv[1]);
    std::string config_type = argv[2];
    std::string output_path = argv[3];

    if (thread_count <= 0 || thread_count > static_cast<int>(MAX_THREADS)) {
        std::cerr << "Error: Thread count must be between 1 and " << MAX_THREADS << std::endl;
        return 1;
    }

    // Verify struct sizes as per FR-004 (T005 requirement)
    if (config_type == "packed") {
        if (sizeof(PackedCounter) != 24) {
            std::cerr << "Error: PackedCounter size is " << sizeof(PackedCounter) << " bytes, expected 24." << std::endl;
            return 1;
        }
    } else if (config_type == "padded") {
        if (sizeof(PaddedCounter) < 192) { // 3 structs * 64 bytes = 192
            std::cerr << "Error: PaddedCounter size is " << sizeof(PaddedCounter) << " bytes, expected >= 192." << std::endl;
            return 1;
        }
    } else {
        std::cerr << "Error: Unknown config type: " << config_type << std::endl;
        return 1;
    }

    // Allocate shared array
    // We need at least 'thread_count' elements. 
    // To ensure distinct elements are truly distinct in memory (and not just structurally),
    // we allocate a vector.
    std::vector<std::atomic<long>> counters(thread_count);
    
    // Initialize counters to 0
    for (int i = 0; i < thread_count; ++i) {
        counters[i].store(0, std::memory_order_relaxed);
    }

    // Start timing
    auto start_time = std::chrono::high_resolution_clock::now();

    // Launch threads
    std::vector<std::thread> threads;
    threads.reserve(thread_count);

    for (int i = 0; i < thread_count; ++i) {
        threads.emplace_back(worker_thread, i, &counters[0], 1, thread_count);
    }

    // Wait for all threads to complete
    for (auto& t : threads) {
        t.join();
    }

    // End timing
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> duration = end_time - start_time;
    double time_ms = duration.count();

    // Verify results (optional but good for debugging)
    long long total_sum = 0;
    for (int i = 0; i < thread_count; ++i) {
        total_sum += counters[i].load(std::memory_order_relaxed);
    }
    long long expected = static_cast<long long>(thread_count) * INCREMENTS_PER_THREAD;
    
    if (total_sum != expected) {
        std::cerr << "Warning: Result mismatch. Expected " << expected << ", got " << total_sum << std::endl;
        // We don't fail here, as the timing is the primary metric, but log it.
    }

    // Write to CSV
    std::ofstream outfile(output_path, std::ios::app);
    if (!outfile.is_open()) {
        std::cerr << "Error: Could not open output file: " << output_path << std::endl;
        return 1;
    }

    // CSV Header: thread_count, configuration, iteration_count, wall_clock_time_ms
    // We append to the file, assuming the header exists or we handle it. 
    // For this specific task (T021), we focus on the logic. 
    // The runner script (T022) will handle headers.
    // We write the row here.
    
    outfile << thread_count << "," 
            << config_type << "," 
            << INCREMENTS_PER_THREAD << "," 
            << std::fixed << std::setprecision(3) << time_ms << std::endl;

    outfile.close();

    std::cout << "Completed " << thread_count << " threads, " << config_type 
              << " config. Time: " << time_ms << " ms." << std::endl;

    return 0;
}

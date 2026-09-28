#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <string>
#include <cstring>
#include <cstdlib>
#include <getopt.h>

#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Global configuration
static int num_threads = 1;
static std::string config_type = "packed"; // "packed" or "padded"
static long long iterations_per_thread = 10000000;
static std::string output_file = "data/raw_benchmark_results.csv";

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " [options]\n"
              << "Options:\n"
              << "  -t, --threads <n>      Number of threads (default: 1)\n"
              << "  -c, --config <type>    Configuration: 'packed' or 'padded' (default: packed)\n"
              << "  -i, --iterations <n>   Iterations per thread (default: 10000000)\n"
              << "  -o, --output <file>    Output CSV file (default: data/raw_benchmark_results.csv)\n"
              << "  -h, --help             Show this help message\n";
}

void parse_args(int argc, char** argv) {
    static struct option long_options[] = {
        {"threads",   required_argument, 0, 't'},
        {"config",    required_argument, 0, 'c'},
        {"iterations",required_argument, 0, 'i'},
        {"output",    required_argument, 0, 'o'},
        {"help",      no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "t:c:i:o:h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 't':
                num_threads = std::atoi(optarg);
                if (num_threads < 1) {
                    std::cerr << "Error: Thread count must be >= 1\n";
                    exit(1);
                }
                break;
            case 'c':
                config_type = std::string(optarg);
                if (config_type != "packed" && config_type != "padded") {
                    std::cerr << "Error: Config must be 'packed' or 'padded'\n";
                    exit(1);
                }
                break;
            case 'i':
                iterations_per_thread = std::atoll(optarg);
                if (iterations_per_thread < 1) {
                    std::cerr << "Error: Iterations must be >= 1\n";
                    exit(1);
                }
                break;
            case 'o':
                output_file = std::string(optarg);
                break;
            case 'h':
                print_usage(argv[0]);
                exit(0);
            default:
                print_usage(argv[0]);
                exit(1);
        }
    }
}

template <typename CounterType>
void run_benchmark_worker(std::atomic<long long>& total_elapsed_us, int thread_id, int num_threads, long long iterations) {
    // Allocate a distinct counter for this thread to avoid false sharing during the increment phase
    // The benchmark measures the cost of atomic operations when threads are logically separated
    // but physically might share cache lines if not padded.
    // However, the task description says: "allocating a shared array of structs where each thread writes to a distinct element"
    // To test false sharing, we usually place them close. But to measure the cost of the counter itself
    // in a multi-threaded environment without interference, we use distinct indices.
    // The "false sharing" effect is tested by comparing the *total time* of packed vs padded
    // when the counters are placed in a shared array.
    
    // We will allocate an array of counters here to simulate the shared memory access pattern.
    // Size: num_threads * 2 (to ensure padding if needed, though we just need num_threads)
    // Actually, the standard false sharing benchmark creates an array of size N (num_threads)
    // and thread i accesses index i.
    
    // Since this is a template, we need to know the size. We'll pass it or use num_threads.
    // To make it generic, we assume the caller handles the array allocation or we do it here.
    // Let's allocate the array here.
    
    // Note: In a real false-sharing test, we want the counters to be close in memory.
    // If we use `std::vector<CounterType> counters(num_threads);`, the compiler might optimize padding.
    // But `CounterType` itself defines the size (packed=24, padded=192).
    // If packed: 24 bytes. 3 packed counters fit in 64 bytes. So thread 0 and 1 might share a line.
    // If padded: 192 bytes. Each gets its own lines.
    
    // We need to ensure the array is large enough and aligned.
    // Let's allocate a raw buffer to be safe, or just rely on vector.
    // Vector is fine for this test.
    
    // However, we need to pass the array to the thread. 
    // We can't easily pass a local vector to a lambda without capture.
    // Let's restructure: The main function allocates the array, and threads access it.
    // But this function is a template worker.
    // Let's change the signature to accept a pointer.
}

template <typename CounterType>
void worker_thread(std::atomic<long long>& elapsed_us, CounterType* counters, int thread_id, long long iterations) {
    // Each thread increments its own counter in the shared array
    // This creates the contention/false sharing scenario if the array is packed
    auto start = std::chrono::high_resolution_clock::now();
    
    for (long long i = 0; i < iterations; ++i) {
        // Use atomic increment
        counters[thread_id].value.fetch_add(1, std::memory_order_relaxed);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    // We want the total time for the run, not per thread sum.
    // But we are in a thread. We can't easily sum up without another lock.
    // The standard approach for this benchmark is to measure the wall clock time
    // of the entire parallel block from the main thread.
    // So this worker just does the work.
    // We will measure time in main.
}

int main(int argc, char** argv) {
    parse_args(argc, argv);

    // Ensure output directory exists (simple check, assume user created it or we create it)
    // In C++, we can't easily create directories without C++17 filesystem or system calls.
    // We assume the script `run_benchmarks.sh` handles the directory creation.
    
    // Open CSV file for appending
    // Header is written only if file is empty or new. 
    // For simplicity in this task, we assume the script handles header or we check file size.
    // But the task says "append rows".
    std::ofstream csv_file(output_file, std::ios::app);
    if (!csv_file.is_open()) {
        std::cerr << "Error: Could not open output file " << output_file << "\n";
        return 1;
    }

    // Write header if file is empty
    if (csv_file.tellp() == 0) {
        csv_file << "thread_count,configuration,iteration_count,wall_clock_time_ms\n";
    }

    // Allocate counters
    // We need num_threads counters.
    // Using a vector is safe, but we want to ensure the memory layout is as expected.
    // std::vector will allocate contiguous memory.
    std::vector<CounterType> counters(num_threads);
    
    // Initialize counters to 0
    for (int i = 0; i < num_threads; ++i) {
        counters[i].value.store(0);
    }

    // Create threads
    std::vector<std::thread> threads;
    threads.reserve(num_threads);

    auto start_time = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(worker_thread<CounterType>, std::ref(counters), i, iterations_per_thread);
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    double wall_clock_time_ms = static_cast<double>(duration.count());

    // Verify results (sanity check)
    long long total = 0;
    for (int i = 0; i < num_threads; ++i) {
        total += counters[i].value.load();
    }
    long long expected = num_threads * iterations_per_thread;
    if (total != expected) {
        std::cerr << "Warning: Result mismatch! Expected " << expected << ", got " << total << "\n";
    }

    // Write to CSV
    csv_file << num_threads << "," << config_type << "," << iterations_per_thread << "," << wall_clock_time_ms << "\n";
    csv_file.close();

    std::cout << "Benchmark completed: " << num_threads << " threads, " << config_type 
              << " config, " << iterations_per_thread << " iterations/thread.\n"
              << "Time: " << wall_clock_time_ms << " ms\n"
              << "Result written to " << output_file << "\n";

    return 0;
}

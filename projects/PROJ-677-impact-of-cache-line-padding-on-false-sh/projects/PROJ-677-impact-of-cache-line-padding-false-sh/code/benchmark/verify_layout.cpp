#include <iostream>
#include <iomanip>
#include <atomic>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

// Include the header files we are verifying
#include "counter_packed.hpp"
#include "counter_padded.hpp"

// Helper to get cache line size (platform specific, fallback to 64)
size_t get_cache_line_size() {
    #ifdef __x86_64__
    return 64;
    #elif defined(__aarch64__)
    return 64;
    #else
    return 64; // Default assumption
    #endif
}

int main(int argc, char* argv[]) {
    std::cout << "=== Memory Layout Verification Utility ===" << std::endl;
    
    size_t cache_line = get_cache_line_size();
    std::cout << "Detected Cache Line Size: " << cache_line << " bytes" << std::endl;

    bool success = true;

    // 1. Verify Packed Counter
    std::cout << "\n--- Verifying Packed Counter ---" << std::endl;
    std::cout << "Size of PackedCounter: " << sizeof(PackedCounter) << " bytes" << std::endl;
    std::cout << "Alignment of PackedCounter: " << alignof(PackedCounter) << " bytes" << std::endl;
    
    // Expected: 24 bytes (as per task description)
    // Expected: Alignment might be 1 (due to pack) or natural alignment of members
    if (sizeof(PackedCounter) != 24) {
        std::cerr << "ERROR: PackedCounter size is " << sizeof(PackedCounter) 
                  << " bytes, expected 24 bytes." << std::endl;
        success = false;
    } else {
        std::cout << "PASS: PackedCounter size is 24 bytes." << std::endl;
    }

    // Check if it fits in one cache line (it should, since 24 < 64)
    if (sizeof(PackedCounter) > cache_line) {
        std::cout << "WARNING: PackedCounter spans multiple cache lines." << std::endl;
    } else {
        std::cout << "INFO: PackedCounter fits within one cache line." << std::endl;
    }

    // 2. Verify Padded Counter
    std::cout << "\n--- Verifying Padded Counter ---" << std::endl;
    std::cout << "Size of PaddedCounter: " << sizeof(PaddedCounter) << " bytes" << std::endl;
    std::cout << "Alignment of PaddedCounter: " << alignof(PaddedCounter) << " bytes" << std::endl;

    // Expected: >= 192 bytes
    // Expected: Alignment 64
    if (sizeof(PaddedCounter) < 192) {
        std::cerr << "ERROR: PaddedCounter size is " << sizeof(PaddedCounter) 
                  << " bytes, expected >= 192 bytes." << std::endl;
        success = false;
    } else {
        std::cout << "PASS: PaddedCounter size is >= 192 bytes." << std::endl;
    }

    if (alignof(PaddedCounter) != 64) {
        std::cerr << "ERROR: PaddedCounter alignment is " << alignof(PaddedCounter) 
                  << " bytes, expected 64 bytes." << std::endl;
        success = false;
    } else {
        std::cout << "PASS: PaddedCounter alignment is 64 bytes." << std::endl;
    }

    // 3. Verify False Sharing Potential (Conceptual)
    // If we have an array of these, do they share cache lines?
    std::cout << "\n--- False Sharing Analysis ---" << std::endl;
    
    // Packed: 24 bytes. Two packed counters in an array: 0-23, 24-47. 
    // If cache line is 64, they fit in one line. FALSE SHARING LIKELY.
    if (sizeof(PackedCounter) * 2 <= cache_line) {
        std::cout << "WARNING: Multiple PackedCounters may share a cache line. False sharing likely." << std::endl;
    } else {
        std::cout << "INFO: PackedCounters likely fit in separate cache lines if array is small, but size is small." << std::endl;
    }

    // Padded: >= 192 bytes. One padded counter per cache line (or multiple lines).
    // 192 bytes = 3 cache lines.
    // Next counter starts at offset 192. 
    // 192 % 64 == 0. So it starts on a new cache line boundary.
    // No false sharing.
    std::cout << "INFO: PaddedCounter size (" << sizeof(PaddedCounter) 
              << ") ensures separation. False sharing unlikely." << std::endl;

    std::cout << "\n=== Verification Complete ===" << std::endl;
    if (success) {
        std::cout << "STATUS: SUCCESS" << std::endl;
        return 0;
    } else {
        std::cout << "STATUS: FAILED" << std::endl;
        return 1;
    }
}

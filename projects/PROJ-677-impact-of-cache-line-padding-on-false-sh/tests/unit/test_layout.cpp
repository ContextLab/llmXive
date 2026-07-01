#include <iostream>
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

// Include the header that defines the struct layouts
// We expect this to be in the benchmark directory as per T007
#include "../code/benchmark/counter_packed.hpp"
#include "../code/benchmark/counter_padded.hpp"

/**
 * Unit test for verify_layout.cpp output validation.
 * 
 * This test verifies that the struct sizes match the expected values:
 * - Packed struct: 24 bytes
 * - Padded struct: >= 192 bytes (3 cache lines of 64 bytes)
 * 
 * It also validates the output of verify_layout.cpp by re-implementing
 * the size checks directly in the test to ensure the binary would produce
 * correct results.
 */

void test_packed_struct_size() {
    constexpr size_t expected_size = 24;
    size_t actual_size = sizeof(PackedCounter);
    
    std::cout << "Testing PackedCounter size..." << std::endl;
    std::cout << "  Expected: " << expected_size << " bytes" << std::endl;
    std::cout << "  Actual:   " << actual_size << " bytes" << std::endl;
    
    assert(actual_size == expected_size && "PackedCounter size mismatch!");
    std::cout << "  PASS" << std::endl;
}

void test_padded_struct_size() {
    constexpr size_t min_expected_size = 192; // 3 * 64 bytes
    size_t actual_size = sizeof(PaddedCounter);
    
    std::cout << "Testing PaddedCounter size..." << std::endl;
    std::cout << "  Expected: >= " << min_expected_size << " bytes" << std::endl;
    std::cout << "  Actual:   " << actual_size << " bytes" << std::endl;
    
    assert(actual_size >= min_expected_size && "PaddedCounter size too small!");
    std::cout << "  PASS" << std::endl;
}

void test_struct_alignment() {
    // Verify that PaddedCounter is aligned to cache line boundary
    constexpr size_t cache_line_size = 64;
    size_t alignment = alignof(PaddedCounter);
    
    std::cout << "Testing PaddedCounter alignment..." << std::endl;
    std::cout << "  Cache line size: " << cache_line_size << " bytes" << std::endl;
    std::cout << "  Actual alignment: " << alignment << " bytes" << std::endl;
    
    assert(alignment >= cache_line_size && "PaddedCounter alignment insufficient!");
    std::cout << "  PASS" << std::endl;
}

void test_array_layout() {
    // Test that array elements are properly spaced to avoid false sharing
    constexpr size_t cache_line_size = 64;
    
    PaddedCounter arr[2];
    size_t diff = reinterpret_cast<size_t>(&arr[1]) - reinterpret_cast<size_t>(&arr[0]);
    
    std::cout << "Testing array element spacing..." << std::endl;
    std::cout << "  Element 0 address: " << reinterpret_cast<size_t>(&arr[0]) << std::endl;
    std::cout << "  Element 1 address: " << reinterpret_cast<size_t>(&arr[1]) << std::endl;
    std::cout << "  Difference: " << diff << " bytes" << std::endl;
    
    assert(diff >= cache_line_size && "Array elements too close - potential false sharing!");
    std::cout << "  PASS" << std::endl;
}

int main() {
    std::cout << "=== Layout Validation Unit Tests ===" << std::endl;
    std::cout << std::endl;
    
    try {
        test_packed_struct_size();
        test_padded_struct_size();
        test_struct_alignment();
        test_array_layout();
        
        std::cout << std::endl;
        std::cout << "=== All tests PASSED ===" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "Test failed with unknown exception" << std::endl;
        return 1;
    }
}
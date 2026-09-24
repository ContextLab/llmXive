#include <iostream>
#include <cassert>
#include <cstdlib>
#include "../code/benchmark/counter_packed.hpp"
#include "../code/benchmark/counter_padded.hpp"

void test_packed_layout() {
    // Verify packed struct is exactly 24 bytes
    static_assert(sizeof(CounterPacked) == 24, "CounterPacked must be 24 bytes");
    static_assert(alignof(CounterPacked) >= 8, "CounterPacked must have at least 8-byte alignment");
    
    // Verify offsets (should be contiguous)
    static_assert(offsetof(CounterPacked, value1) == 0, "value1 should be at offset 0");
    static_assert(offsetof(CounterPacked, value2) == 8, "value2 should be at offset 8");
    static_assert(offsetof(CounterPacked, value3) == 16, "value3 should be at offset 16");
}

void test_padded_layout() {
    // Verify padded struct is at least 192 bytes
    static_assert(sizeof(CounterPadded) >= 192, "CounterPadded must be at least 192 bytes");
    static_assert(alignof(CounterPadded) >= 64, "CounterPadded must be aligned to 64 bytes");
    
    // Verify each member is on its own cache line (64-byte aligned)
    static_assert(offsetof(CounterPadded, value1) % 64 == 0, "value1 must be 64-byte aligned");
    static_assert(offsetof(CounterPadded, value2) % 64 == 0, "value2 must be 64-byte aligned");
    static_assert(offsetof(CounterPadded, value3) % 64 == 0, "value3 must be 64-byte aligned");
    
    // Verify spacing between members
    static_assert(offsetof(CounterPadded, value2) - offsetof(CounterPadded, value1) >= 64, 
                  "value2 must be at least 64 bytes after value1");
    static_assert(offsetof(CounterPadded, value3) - offsetof(CounterPadded, value2) >= 64, 
                  "value3 must be at least 64 bytes after value2");
}

int main() {
    std::cout << "Running layout tests..." << std::endl;
    
    try {
        test_packed_layout();
        std::cout << "  [PASS] test_packed_layout" << std::endl;
        
        test_padded_layout();
        std::cout << "  [PASS] test_padded_layout" << std::endl;
        
        std::cout << "All tests passed!" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed: " << e.what() << std::endl;
        return 1;
    }
}
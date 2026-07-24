#include <iostream>
#include <cassert>
#include <cstddef>
#include <vector>
#include <cstdint>

#include "counter_packed.hpp"
#include "counter_padded.hpp"

void test_packed_size() {
    std::cout << "Testing CounterPacked size...\n";
    assert(sizeof(CounterPacked) == 24);
    std::cout << "  PASSED: CounterPacked is 24 bytes\n";
}

void test_padded_size() {
    std::cout << "Testing CounterPadded size...\n";
    assert(sizeof(CounterPadded) >= 192);
    std::cout << "  PASSED: CounterPadded is >= 192 bytes\n";
}

void test_padded_alignment() {
    std::cout << "Testing CounterPadded alignment...\n";
    assert(alignof(CounterPadded) >= 64);
    std::cout << "  PASSED: CounterPadded alignment >= 64\n";
}

void test_array_spacing() {
    std::cout << "Testing array element spacing...\n";
    
    alignas(64) std::vector<CounterPadded> padded_array(4);
    alignas(1) std::vector<CounterPacked> packed_array(4);

    // Check padded array spacing
    for (size_t i = 0; i < 3; ++i) {
        size_t offset = reinterpret_cast<uintptr_t>(&padded_array[i+1]) - reinterpret_cast<uintptr_t>(&padded_array[i]);
        assert(offset >= 64);
    }
    std::cout << "  PASSED: Padded array spacing >= 64 bytes\n";

    // Check packed array spacing (should be small)
    for (size_t i = 0; i < 3; ++i) {
        size_t offset = reinterpret_cast<uintptr_t>(&packed_array[i+1]) - reinterpret_cast<uintptr_t>(&packed_array[i]);
        assert(offset <= 32); // Should be close to 24
    }
    std::cout << "  PASSED: Packed array spacing <= 32 bytes\n";
}

int main() {
    std::cout << "=== Unit Tests for Memory Layout ===\n\n";
    
    test_packed_size();
    test_padded_size();
    test_padded_alignment();
    test_array_spacing();
    
    std::cout << "\n=== All Tests Passed ===\n";
    return 0;
}

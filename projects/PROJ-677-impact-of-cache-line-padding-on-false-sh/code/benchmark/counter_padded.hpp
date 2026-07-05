#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstddef>

struct CounterPadded {
    alignas(64) long long value;
    int tag;
    char padding[52]; // 8 + 4 + 52 = 64 bytes for the first element
    // To ensure the next element starts on a new cache line, the struct size must be >= 64
    // and aligned.
    // We need the struct to be at least 64 bytes.
    // If we want the next element to be on a new line, the struct size should be 64.
    // 8 (value) + 4 (tag) + 52 (padding) = 64.
};

#endif // COUNTER_PADDED_HPP
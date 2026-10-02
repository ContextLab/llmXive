#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstddef>

// Cache line size constant (typically 64 bytes on modern x86/x64)
constexpr std::size_t CACHE_LINE_SIZE = 64;

/**
 * @struct CounterPadded
 * @brief A structure containing three counters, each padded to occupy
 *        a full cache line to prevent false sharing in multi-threaded
 *        scenarios.
 *
 * Each member is explicitly aligned to CACHE_LINE_SIZE (64 bytes).
 * This ensures that c1, c2, and c3 reside on separate cache lines,
 * preventing the false sharing problem where multiple threads writing
 * to different variables on the same cache line cause unnecessary
 * cache coherence traffic.
 *
 * Expected size: 3 * 64 = 192 bytes (assuming long is 8 bytes).
 */
struct CounterPadded {
    // Align each counter to a 64-byte boundary
    alignas(CACHE_LINE_SIZE) long c1;
    alignas(CACHE_LINE_SIZE) long c2;
    alignas(CACHE_LINE_SIZE) long c3;
};

// Static assertion to verify the struct size is at least 192 bytes
// (3 counters * 64 bytes per cache line)
static_assert(sizeof(CounterPadded) >= 192, "Padded size must be >= 192");

// Optional: Verify individual member alignment
static_assert(alignof(CounterPadded::c1) == CACHE_LINE_SIZE, "c1 must be 64-byte aligned");
static_assert(alignof(CounterPadded::c2) == CACHE_LINE_SIZE, "c2 must be 64-byte aligned");
static_assert(alignof(CounterPadded::c3) == CACHE_LINE_SIZE, "c3 must be 64-byte aligned");

#endif // COUNTER_PADDED_HPP
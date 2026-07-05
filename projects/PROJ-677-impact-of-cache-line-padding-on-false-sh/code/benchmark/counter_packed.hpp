#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#pragma pack(push, 1)
struct CounterPacked {
    long long value;
    int tag;
    char padding[2]; // To make total size 24 bytes (8 + 4 + 2 + padding to align next if needed, but pack forces 12 or 24 depending on implementation, let's ensure specific size)
};
// Note: With #pragma pack(1), sizeof(CounterPacked) should be 14 (8+4+2) or similar depending on alignment of members.
// The task spec mentioned 24 bytes. Let's explicitly pad to reach 24 if the natural size is smaller, 
// or rely on the fact that without alignment, it's compact.
// To strictly match "24 bytes" requirement from T007:
// 8 (long long) + 4 (int) = 12. We need 12 more bytes.
struct CounterPacked {
    long long value;
    int tag;
    char extra[12]; // Total 8+4+12 = 24 bytes
};
#pragma pack(pop)

#endif // COUNTER_PACKED_HPP

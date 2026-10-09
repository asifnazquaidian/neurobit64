# Reference model of NeuroBit64-S in plain Python (no cocotb needed).
# words(n, lif, leak, tsel) yields the 64-bit words the chip sends in self-test (bist) mode.
# Run this file directly to print the same RESULT line as the Verilog testbench and the JS model.
import sys

MASK32 = 0xFFFFFFFF


def words(n, lif=0, leak=3, tsel=0):
    x = 0x12345678
    vm = [0] * 64
    thresh = ((248 - 16 * tsel) << leak) if lif else (256 - (1 << tsel)) & 255
    for _ in range(n):
        word = 0
        for ch in range(64):
            total = ((vm[ch] - (vm[ch] >> leak)) if lif else 0) + (x >> 24)
            if total >= thresh:
                word |= 1 << ch
                vm[ch] = 0
            else:
                vm[ch] = total
            x ^= (x << 13) & MASK32
            x ^= x >> 17
            x ^= (x << 5) & MASK32
        yield word


def signature(n, lif=0, leak=3, tsel=0):
    sig, ones = 0, 0
    for i, w in enumerate(words(n, lif, leak, tsel)):
        sig = (((sig << 1) | (sig >> 63)) & 0xFFFFFFFFFFFFFFFF) ^ w ^ i
        ones += bin(w).count("1")
    return sig, ones


if __name__ == "__main__":
    n, lif, leak, tsel = (int(a) for a in sys.argv[1:5])
    sig, ones = signature(n, lif, leak, tsel)
    print(f"RESULT n_words={n} lif={lif} leak={leak} tsel={tsel} words={n} ones={ones} sig={sig:016x} framing_errors=0")

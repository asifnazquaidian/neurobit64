## How it works

NeuroBit64-S is a 64-neuron circuit that stores every neuron decision as one bit in an external
serial memory. One neuron circuit is shared by all 64 neurons.

A neuron tick has 64 slots, one per neuron, and a slot is 8 clocks:

1. the 8-bit input sample of that neuron is shifted in on `SDI`, most significant bit first
   (with `BIST_EN = 1` the sample comes from an on-chip xorshift32 generator instead);
2. on the last clock of the slot the neuron is updated and decides 1 (fire) or 0;
3. the decision is held on `SDO` for the whole next slot, with one `SCK` pulse in its middle;
4. `SYNC` is high while the bit of neuron 0 is on `SDO`, marking the start of a 64-bit word.

So the chip sends one 64-bit word per tick (neuron 0 first) on three pins. With the 50 MHz clock
this is 6.25 Mbit/s, or 97,656 ticks per second.

Two neuron types are selectable:

- `LIF_EN = 0`, threshold neuron: fires when `sample >= 256 - 2^THRESH_SEL`.
- `LIF_EN = 1`, leaky integrate-and-fire: `v = v - (v >> LEAK) + sample`; fires when
  `v >= (248 - 16 * THRESH_SEL) << LEAK`, then `v = 0`. Each neuron keeps its own 11-bit `v`.

## How to test

Hold `rst_n` low, set `BIST_EN = 1` and choose the neuron settings on `ui[7:2]`, then release
reset. Capture `SDO` on every rising edge of `SCK`; a word starts where `SYNC` is high. The words
must equal the ones produced by `test/reference.py` for the same settings, for example
`LIF_EN = 1, LEAK = 3, THRESH_SEL = 5` (`ui_in = 0b10111110`).

To use real signals, set `BIST_EN = 0` and send 64 samples of 8 bits per tick on `SDI`,
changing `SDI` on the falling clock edge. The first bit after reset belongs to neuron 0.

## External hardware

A serial memory or logic analyser on `SDO`, `SCK` and `SYNC`. For long recordings, a
microcontroller (for example the RP2040 on the Tiny Tapeout demo board) that collects the
6.25 Mbit/s stream and writes it to an SD card: 102.4 billion bits are 12.8 GB.

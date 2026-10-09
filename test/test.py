# SPDX-FileCopyrightText: © 2026 Asif Mehmood
# SPDX-License-Identifier: Apache-2.0
#
# Captures the serial word stream of NeuroBit64-S in self-test mode and compares it with the
# Python reference model (reference.py) for a leaky and a threshold neuron setting.

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reference import words  # noqa: E402


async def capture(dut, ui_in, n_words):
    """Reset the chip with the given settings and return the first n_words words it sends."""
    dut.ena.value = 1
    dut.ui_in.value = ui_in
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    got, word, nbit, started, prev_sck = [], 0, 0, False, 0
    for _ in range((n_words + 2) * 512):
        await FallingEdge(dut.clk)
        v = dut.uo_out.value.to_unsigned()
        sdo, sck, sync = v & 1, (v >> 1) & 1, (v >> 2) & 1
        if sck and not prev_sck:          # rising edge of SCK: the memory samples SDO here
            if sync:
                assert nbit == 0, "SYNC arrived in the middle of a word"
                started = True
            if started:
                word |= sdo << nbit
                nbit += 1
                if nbit == 64:
                    got.append(word)
                    word, nbit = 0, 0
        prev_sck = sck
        if len(got) == n_words:
            break
    return got


@cocotb.test()
async def test_project(dut):
    clock = Clock(dut.clk, 20, unit="ns")  # 50 MHz
    cocotb.start_soon(clock.start())

    # ui_in = {thresh_sel[2:0], leak[1:0], lif_en, bist_en, sdi}
    dut._log.info("Leaky integrate-and-fire neurons: leak 3, threshold select 5")
    got = await capture(dut, (5 << 5) | (3 << 3) | (1 << 2) | (1 << 1), 12)
    assert got == list(words(12, lif=1, leak=3, tsel=5))

    dut._log.info("Threshold neurons: threshold select 6")
    got = await capture(dut, (6 << 5) | (1 << 1), 12)
    assert got == list(words(12, lif=0, leak=0, tsel=6))

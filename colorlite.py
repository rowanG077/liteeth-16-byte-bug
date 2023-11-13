#!/usr/bin/env python3

#
# This file is part of Colorlite.
#
# Copyright (c) 2020-2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse
import sys

# litex_projects_path = "/home/rowan.goemans/Documents/engineering"
# sys.path = [s for s in sys.path if "liteeth" not in s]
# sys.path.append(f"{litex_projects_path}/liteeth")
# sys.path = [s for s in sys.path if "litex" not in s]
# sys.path.append(f"{litex_projects_path}/litex")

from migen import *
from migen.genlib.misc import WaitTimer
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *
from litex.build.lattice.platform import LatticePlatform
from litex_boards.platforms import colorlight_5a_75b

from litex.soc.cores.clock import *
from litex.soc.cores.spi_flash import ECP5SPIFlash
from litex.soc.cores.gpio import GPIOOut
from litex.soc.cores.led import LedChaser
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect.packet import PacketFIFO

from liteeth.common import eth_udp_user_description
from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.common import *
from liteeth.core.udp import LiteEthUDPTX
from litex.build.generic_platform import *

_io = [
    ("sys_clock", 0, Pins(1)),
    ("sys_reset", 1, Pins(1)),
    ("rgmii_clocks", 0,
        Subsignal("tx", Pins(1)),
        Subsignal("rx", Pins(1))
    ),
    ("rgmii_tx_refclk", 0, Pins(1)),
    ("rgmii", 0,
        # Subsignal("rst_n",   Pins(1)),
        Subsignal("int_n",   Pins(1)),
        Subsignal("mdio",    Pins(1)),
        Subsignal("mdc",     Pins(1)),
        Subsignal("rx_ctl",  Pins(1)),
        Subsignal("rx_data", Pins(4)),
        Subsignal("tx_ctl",  Pins(1)),
        Subsignal("tx_data", Pins(4))
    ),
]

def get_udp_raw_port_ios(name, data_width):
    return [
        (f"{name}", 0,
            # Sink.
            Subsignal("sink_ip_address", Pins(32)),
            Subsignal("sink_src_port",   Pins(16)),
            Subsignal("sink_dst_port",   Pins(16)),
            Subsignal("sink_valid",      Pins(1)),
            Subsignal("sink_length",     Pins(16)),
            Subsignal("sink_last",       Pins(1)),
            Subsignal("sink_ready",      Pins(1)),
            Subsignal("sink_data",       Pins(data_width)),
            Subsignal("sink_last_be",    Pins(data_width//8)),
        ),
    ]

def get_ip_raw_port_ios(name, data_width):
    return [
        (f"{name}", 0,
            # Sink.
            Subsignal("source_ip_address", Pins(32)),
            Subsignal("source_protocol",   Pins(16)),
            Subsignal("source_length",   Pins(16)),
            Subsignal("source_valid",      Pins(1)),
            Subsignal("source_data",     Pins(16)),
            Subsignal("source_ready",      Pins(1)),
            Subsignal("source_error",       Pins(data_width)),
            Subsignal("source_last",       Pins(1)),
            Subsignal("source_last_be",    Pins(data_width//8)),
        ),
    ]


# ColorLite ----------------------------------------------------------------------------------------

class ColorLite(SoCMini):
    def __init__(self, sys_clk_freq=int(40e6), ip_address=None, mac_address=None):
        platform  = LatticePlatform("LFE5U-25F-6BG256C", io=[], toolchain="trellis")
        platform.add_extension(_io)

        # CRG --------------------------------------------------------------------------------------
        self.crg = CRG(platform.request("sys_clock"), platform.request("sys_reset"))

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, clk_freq=sys_clk_freq)

        data_width = 32
        self.core = core = LiteEthUDPTX(convert_ip(ip_address), dw=data_width)

        platform.add_extension(get_udp_raw_port_ios("udp", data_width = data_width))
        port_udp = platform.request("udp")

        platform.add_extension(get_ip_raw_port_ios("ip", data_width = data_width))
        port_ip = platform.request("ip")

        # Connect user IO to UDPTx
        self.comb += [
            core.sink.valid.eq(port_udp.sink_valid),
            core.sink.last.eq(port_udp.sink_last),
            core.sink.dst_port.eq(port_udp.sink_dst_port),
            core.sink.src_port.eq(port_udp.sink_src_port),
            core.sink.ip_address.eq(port_udp.sink_ip_address),
            core.sink.length.eq(port_udp.sink_length),
            port_udp.sink_ready.eq(core.sink.ready),
            core.sink.data.eq(port_udp.sink_data),
            core.sink.last_be.eq(port_udp.sink_last_be),
        ]

        # Connect UDPTx IP out to user IO
        self.comb += [
            port_ip.source_ip_address.eq(core.source.ip_address),
            port_ip.source_protocol.eq(core.source.protocol),
            port_ip.source_length.eq(core.source.length),
            port_ip.source_valid.eq(core.source.valid),
            port_ip.source_data.eq(core.source.data),
            core.source.ready.eq(port_ip.source_ready),
            port_ip.source_error.eq(core.source.error),
            port_ip.source_last.eq(core.source.last),
            port_ip.source_last_be.eq(core.source.last_be),
        ]
        

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Take control of your ColorLight FPGA board with LiteX/LiteEth :)")
    parser.add_argument("--build",       action="store_true",      help="Build bitstream")
    parser.add_argument("--load",        action="store_true",      help="Load bitstream")
    parser.add_argument("--flash",       action="store_true",      help="Flash bitstream")
    parser.add_argument("--ip-address",  default="192.168.1.20",   help="Ethernet IP address of the board (default: 192.168.1.20).")
    parser.add_argument("--mac-address", default="0x726b895bc2e2", help="Ethernet MAC address of the board (defaullt: 0x726b895bc2e2).")
    args = parser.parse_args()

    soc     = ColorLite(ip_address=args.ip_address, mac_address=int(args.mac_address, 0))
    builder = Builder(soc, output_dir="build")
    builder.build(build_name="colorlite", run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".svf"))

    if args.flash:
        prog = soc.platform.create_programmer()
        os.system("cp bit_to_flash.py build/gateware/")
        os.system("cd build/gateware && chmod +x ./build_colorlite.sh && ./build_colorlite.sh")
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()

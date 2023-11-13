#! /usr/bin/env sh
set -e

iverilog -o run_sim.vvp -s tb -Wall -pfileline=1 build/gateware/colorlite.v tb.sv
vvp run_sim.vvp -fst -lvvp.log
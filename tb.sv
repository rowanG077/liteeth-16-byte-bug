`timescale 1ns / 1ps

module tb;

  reg clk;
  reg rst = 0;
  always #10 clk = !clk;


  initial begin
    #100;
    $finish;
  end

  wire [15:0] ip_data;
  wire [31:0] ip_error;
  wire [31:0] ip_ip_address;
  wire        ip_last;
  wire  [3:0] ip_last_be;
  wire [15:0] ip_length;
  wire [15:0] ip_protocol;
  reg         ip_ready;
  wire        ip_valid;
  reg [31:0]  udp_data;
  reg [15:0]  udp_dst_port;
  reg [31:0]  udp_ip_address;
  reg         udp_last;
  reg  [3:0]  udp_last_be;
  reg [15:0]  udp_length;
  wire        udp_ready;
  reg [15:0]  udp_src_port;
  reg         udp_valid;

  colorlite inst (
    .sys_clock(clk),
    .sys_reset(rst),
    .ip_source_data(ip_data),
    .ip_source_error(ip_error),
    .ip_source_ip_address(ip_ip_address),
    .ip_source_last(ip_last),
    .ip_source_last_be(ip_last_be),
    .ip_source_length(ip_length),
    .ip_source_protocol(ip_protocol),
    .ip_source_ready(ip_ready),
    .ip_source_valid(ip_valid),
    .udp_sink_data(udp_data),
    .udp_sink_dst_port(udp_dst_port),
    .udp_sink_ip_address(udp_ip_address),
    .udp_sink_last(udp_last),
    .udp_sink_last_be(udp_last_be),
    .udp_sink_length(udp_length),
    .udp_sink_ready(udp_ready),
    .udp_sink_src_port(udp_src_port),
    .udp_sink_valid(udp_valid)
  );


  initial begin
    ip_ready <= 1'b1;

    udp_data <= 32'hDEADBEEF;
    udp_dst_port <= 16'd13373;
    udp_ip_address <= 32'h0a000b2b;
    udp_last <= 1'b0;
    udp_last_be <= 4'b1000;
    udp_length <= 16'd4;
    udp_src_port <= 16'd50000;
    udp_valid <= 1'b0;
  end

  initial begin
    $dumpvars;
  end


endmodule
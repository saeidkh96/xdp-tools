
# XDP-TOOLS + CICFlowMeter + ML Intrusion Detection

This project integrates high-performance XDP-based packet processing tools, CICFlowMeter flow extraction, and a Machine Learning intrusion detection pipeline.

It provides:

- XDP utilities (xdp-loader, xdp-filter, xdp-dump, xdp-monitor, etc.)
- Flow feature extraction (CICFlowMeter)
- ML-based flow classification (Python)
- XDP program for in-kernel ML tagging

-----------------------------------------

## Features

### XDP Tools  
Located in:

xdp-bench/
xdp-dump/
xdp-filter/
xdp-forward/
xdp-loader/
xdp-monitor/
xdp-traffgen/

Capabilities:
- Load/unload XDP programs  
- Dump packets  
- Filter IPv4/IPv6/TCP/UDP  
- Realtime monitoring/output  
- Traffic generation  
- Performance benchmarking  

-----------------------------------------

### CICFlowMeter – Flow Extraction

Folder:

cicflowmeter/

CICFlowMeter extracts 80+ flow features from PCAP traffic and produces ML-ready CSV files.

-----------------------------------------

### ML Intrusion Detection

Scripts:

predict_capture3.py  
xdp_ml_detect.c

Pipeline:

1. Capture packets (xdp-dump)
2. Extract flows (cicflowmeter)
3. Run ML prediction (predict_capture3.py)
4. Optional: Load XDP ML program (xdp_ml_detect.c) to mark packets in-kernel

-----------------------------------------

## Installation

### System Requirements

- Linux with XDP/eBPF support  
- clang & llvm  
- libbpf + bpftool  
- make + gcc  
- Python 3.8+  

Install dependencies (Ubuntu):

sudo apt update
sudo apt install clang llvm libbpf-dev libelf-dev build-essential python3-pip bpftool

Install Python packages:

pip install -r requirements.txt

-----------------------------------------

## Build Instructions

Configure:

./configure

Build all XDP tools:

make

Build ML XDP program:

clang -O2 -target bpf -c xdp_ml_detect.c -o xdp_ml_detect.o

-----------------------------------------

## Running the Full Pipeline

1) Dump traffic (pcap)

sudo ./xdp-dump/xdp-dump -i eth0 -w capture.pcap

2) Generate flows

python3 cicflowmeter/flow_generator.py capture.pcap flows.csv

3) ML prediction

python3 predict_capture3.py flows.csv predictions.csv

4) Load XDP ML classifier

sudo ./xdp-loader/xdp-loader load eth0 xdp_ml_detect.o

Unload:

sudo ./xdp-loader/xdp-loader unload eth0

-----------------------------------------

## Project Structure

xdp-tools/
 ├── xdp-loader/
 ├── xdp-filter/
 ├── xdp-monitor/
 ├── xdp-forward/
 ├── xdp-dump/
 ├── xdp-traffgen/
 ├── cicflowmeter/
 ├── predict_capture3.py
 ├── xdp_ml_detect.c
 ├── Makefile
 ├── configure
 ├── headers/
 ├── runtime/
 ├── lib/
 └── README.md

-----------------------------------------

## Files Not Included in GitHub

*.pcap  
*.pcap.lz4  
*.csv  
*.o  
venv/  
__pycache__/  
.vscode/  
.idea/  

-----------------------------------------

## License
MIT (or your chosen license)


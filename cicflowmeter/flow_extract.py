from cicflowmeter.sniffer import Sniffer

input_pcap = "../capture3.pcap"
output_csv = "../capture3_flows.csv"

sniffer = Sniffer(
    input_file=input_pcap,
    output_file=output_csv,
    max_bytes=262144,
    verbose=True,
)

sniffer.start()

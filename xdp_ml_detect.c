#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_ml_detect(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    __u32 pkt_size = data_end - data;

    // ML-like rule (kernel level)
    if (pkt_size > 400) {
        return XDP_DROP;  // classify as attack and drop
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

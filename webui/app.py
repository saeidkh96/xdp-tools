from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import pandas as pd
import numpy as np
from joblib import load
from pathlib import Path
import time


BASE_DIR = Path(__file__).resolve().parent.parent      # ~/xdp-lab/xdp-tools
WEB_DIR = BASE_DIR / "webui"
RUNTIME_DIR = BASE_DIR / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

PCAP_PATH = RUNTIME_DIR / "live_capture.pcap"
FLOWS_CSV = RUNTIME_DIR / "live_flows.csv"
FLOWS_WITH_PRED = RUNTIME_DIR / "live_flows_with_pred.csv"


OUT_DIR = BASE_DIR / "outputs"
PREFIX = "ddos_full"

# ddos_full_scaler_20.joblib, ddos_full_selector_20.joblib,
# ddos_full_label_encoder.joblib, ddos_full_gb_20.joblib
try:
    scaler = load(OUT_DIR / f"{PREFIX}_scaler_20.joblib")
    selector = load(OUT_DIR / f"{PREFIX}_selector_20.joblib")
    label_encoder = load(OUT_DIR / f"{PREFIX}_label_encoder.joblib")
    model = load(OUT_DIR / f"{PREFIX}_gb_20.joblib")
except Exception as e:
    print("WARNING: could not load model artifacts:", e)
    scaler = selector = label_encoder = model = None

app = FastAPI()


app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "static" / "index.html")


# --------- API Models ---------
class CaptureRequest(BaseModel):
    interface: str
    timespan: int  # seconds


_last_flows_json: list[dict] = []


# --------- Helper functions ---------
def run_capture(interface: str, timespan: int):
    """
    Capture packets from the given interface into PCAP_PATH.
    We use `timeout` so it stops automatically after `timespan` seconds.
    Exit code 124 from `timeout` is treated as normal (time limit reached).
    """
    if PCAP_PATH.exists():
        PCAP_PATH.unlink()

    cmd = [
        "timeout",
        str(timespan),
        "tcpdump",
        "-i",
        interface,
        "-w",
        str(PCAP_PATH),
    ]
    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd)  

    if completed.returncode not in (0, 124):
        raise RuntimeError(f"tcpdump failed with code {completed.returncode}")

def run_cicflowmeter():
    """
    pcap -> flows.csv using full cicflowmeter path
    """
    if FLOWS_CSV.exists():
        FLOWS_CSV.unlink()

    CIC_PATH = "/home/saeid/xdp-lab/xdp-tools/cicflowmeter/venv/bin/cicflowmeter"

    cmd = [
        CIC_PATH,
        "-f",
        str(PCAP_PATH),
        "-c",
        str(FLOWS_CSV),
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def run_classifier():
    global _last_flows_json

    if not FLOWS_CSV.exists() or FLOWS_CSV.stat().st_size == 0:
        print("WARNING: No flow file or file is empty.")
        _last_flows_json = []
        return

    try:
        df = pd.read_csv(FLOWS_CSV)
    except pd.errors.EmptyDataError:
        print("WARNING: Flow CSV is empty (pandas EmptyDataError).")
        _last_flows_json = []
        return
    except Exception as e:
        print("ERROR reading CSV:", e)
        _last_flows_json = []
        return

    if df.empty:
        print("WARNING: Flow CSV parsed but has no rows.")
        _last_flows_json = []
        return

    if not (model and scaler and selector):
        print("WARNING: Model or scaler/selector not loaded, marking all as UNKNOWN.")
        df["Prediction"] = "UNKNOWN"
        cols = ["src_ip", "src_port", "dst_ip", "dst_port", "timestamp", "Prediction"]
        existing = [c for c in cols if c in df.columns]
        _last_flows_json = df[existing].to_dict(orient="records")
        return

    df_num = (
        df.select_dtypes(include=[np.number])
        .replace([np.inf, -np.inf], 0)
        .fillna(0)
    )

    if df_num.shape[0] == 0:
        print("WARNING: No numeric rows for classifier.")
        _last_flows_json = []
        return

    expected_cols = selector.get_feature_names_out()

    aligned = pd.DataFrame(index=df_num.index)
    for col in expected_cols:
        if col in df_num.columns:
            aligned[col] = df_num[col]
        else:
            aligned[col] = 0 

    if aligned.shape[0] == 0:
        print("WARNING: Aligned feature matrix has 0 rows.")
        _last_flows_json = []
        return

    X_scaled = scaler.transform(aligned)
    y_pred = model.predict(X_scaled)

    try:
        y_labels = label_encoder.inverse_transform(y_pred)
    except Exception:
        y_labels = y_pred

    df["Prediction"] = y_labels

    cols = ["src_ip", "src_port", "dst_ip", "dst_port", "timestamp", "Prediction"]
    existing = [c for c in cols if c in df.columns]
    _last_flows_json = df[existing].to_dict(orient="records")
    

# --------- API endpoints ---------
@app.post("/api/start_capture")
def start_capture(req: CaptureRequest):
    """
    این endpoint از UI صدا زده می‌شه:
    1) pcap می‌گیرد
    2) cicflowmeter اجرا می‌کند
    3) classifier را اجرا می‌کند
    """
    start = time.time()
    run_capture(req.interface, req.timespan)
    run_cicflowmeter()
    run_classifier()
    elapsed = time.time() - start

    return {
        "status": "ok",
        "elapsed_sec": round(elapsed, 2),
        "flows": len(_last_flows_json),
    }


@app.get("/api/flows")
def get_flows():
    """
    آخرین نتیجه کلاسفایر را برمی‌گرداند.
    UI این را می‌خواند و جدول را پر می‌کند.
    """
    return _last_flows_json

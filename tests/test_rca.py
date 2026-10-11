import importlib.util
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "rca.py"
spec = importlib.util.spec_from_file_location("rca", MODULE)
rca = importlib.util.module_from_spec(spec)
sys.modules["rca"] = rca
spec.loader.exec_module(rca)


def test_detects_threshold_and_error_code():
    rows = [
        {"timestamp": "t1", "device": "M1", "temperature_c": "60",
         "vibration_mm_s": "2.0", "current_a": "10", "error_code": "0"},
        {"timestamp": "t2", "device": "M1", "temperature_c": "95",
         "vibration_mm_s": "8.0", "current_a": "30", "error_code": "E02"},
    ]
    anomalies = rca.detect(rows)
    kinds = {a.kind for a in anomalies}
    assert "temperature_c" in kinds
    assert "vibration_mm_s" in kinds
    assert "current_a" in kinds
    assert "error_code" in kinds
    assert rca.summarize(anomalies)["criticas"] >= 3


def test_normal_row_produces_no_anomaly():
    rows = [{"timestamp": "t", "device": "M1", "temperature_c": "50",
             "vibration_mm_s": "1.0", "current_a": "8", "error_code": "0"}]
    assert rca.detect(rows) == []


def test_root_cause_prioritises_mechanical():
    rows = [{"timestamp": "t", "device": "M1", "temperature_c": "95",
             "vibration_mm_s": "9", "current_a": "30", "error_code": "0"}]
    cause = rca.probable_root_cause(rca.detect(rows))
    assert "mecanico" in cause.lower()


def test_sample_is_deterministic(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    rca.make_sample(a)
    rca.make_sample(b)
    assert a.read_text() == b.read_text()

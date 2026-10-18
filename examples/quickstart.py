"""Run: python examples/quickstart.py"""
import json
from pathlib import Path
from contextatlas import analyze
payload=json.loads((Path(__file__).resolve().parents[1]/"datasets/demo.json").read_text())
result=analyze(**payload)
print(json.dumps({"optimized":result["optimized_metrics"],"baseline":result["baseline_metrics"]},indent=2))
print("\nPACKED CONTEXT\n",result["assembled_context"])

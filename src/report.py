import json
import sys
from pathlib import Path


def write_report(report: dict, path: Path | None) -> None:
    if path is None:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
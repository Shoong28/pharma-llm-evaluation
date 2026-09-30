"""Display historical aggregate results. No API calls or raw data required."""
from pathlib import Path
import csv


def main():
    source = Path(__file__).resolve().parents[1] / "reports" / "reported_summary.csv"
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for group in ("prompt", "model", "question_type"):
        print(f"\n{group}")
        for row in rows:
            if row["group"] == group:
                print(f"  {row['condition']:16} {float(row['strict_accuracy_percent']):6.2f}%")
    print("\nHistorical reported aggregates; raw responses were not re-evaluated.")


if __name__ == "__main__":
    main()

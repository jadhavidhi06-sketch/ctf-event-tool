import json
import csv

def export_json(data):
    with open("events.json", "w") as f:
        json.dump(data, f, indent=4)


def export_csv(data):
    with open("events.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Name", "Platform", "Location", "Date", "Score"])

        for e in data:
            writer.writerow([
                e["name"],
                e["platform"],
                e["location"],
                e["date"],
                e["score"]
            ])
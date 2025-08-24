\
from __future__ import annotations
from .storage import aggregate_records, todays_file
import json

def send_all_to_tally():
    """Mock sender: marks all 'No' to 'Yes' within today's file.
       In real life, you'd iterate unsent across files and POST to Tally.
    """
    items = aggregate_records()
    sent = 0
    failed = 0
    # For the demo, only update today's file to keep IO simple.
    f = todays_file()
    if f.exists():
        arr = json.loads(f.read_text())
        for r in arr:
            if r.get("sent_to_tally") != "Yes":
                # TODO: call external API here; if success:
                r["sent_to_tally"] = "Yes"
                sent += 1
        f.write_text(json.dumps(arr, indent=2))
    return sent, failed

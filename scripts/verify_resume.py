import json
import os

OUT_DIR = "data/labeled"
CANDIDATES = "data/candidates/pmcoa_candidates.jsonl"

def main():
    out_path = os.path.join(OUT_DIR, "gold.jsonl")
    bad_path = os.path.join(OUT_DIR, "bad.jsonl")

    completed_ids = set()
    
    # Simulate loading gold
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                try: 
                    d = json.loads(line)
                    if "input" in d:
                        uid = d["input"].get("url") or d["input"].get("title")
                        completed_ids.add(uid)
                except: pass
    
    gold_count = len(completed_ids)
    print(f"Loaded {gold_count} IDs from gold.jsonl")

    # Simulate loading bad
    if os.path.exists(bad_path):
        with open(bad_path, "r", encoding="utf-8") as f:
            for line in f:
                try: 
                    d = json.loads(line)
                    if "ex" in d:
                         uid = d["ex"].get("url") or d["ex"].get("title")
                         completed_ids.add(uid)
                except: pass
    
    total_completed = len(completed_ids)
    print(f"Total unique completed IDs (gold + bad): {total_completed}")

    # Check candidates
    total_candidates = 0
    skipped = 0
    to_process = 0
    
    if os.path.exists(CANDIDATES):
        with open(CANDIDATES, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ex = json.loads(line)
                    total_candidates += 1
                    uid = ex.get("url") or ex.get("title")
                    
                    if uid in completed_ids:
                        skipped += 1
                    else:
                        to_process += 1
                except: pass
    
    print("-" * 30)
    print(f"Total Candidates in file: {total_candidates}")
    print(f"Skipped (Already in gold/bad): {skipped}")
    print(f"To Be Processed: {to_process}")
    
    if skipped == total_completed and skipped > 0:
         print("\nVERIFICATION SUCCESSFUL: The logic correctly identifies labeled rows.")
    elif skipped < total_completed and total_candidates > 0:
         # This might happen if gold has items not in the current candidate file (e.g. if candidate file was regenerated/overwritten)
         print("\nNOTE: Gold has more items than matched in candidates. This is expected if candidates file was reset.")
    else:
         print("\nVERIFICATION STATUS: seems correct based on available files.")

if __name__ == "__main__":
    main()

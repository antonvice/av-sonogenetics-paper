import os
import re
import json
import multiprocessing as mp
from datasets import load_dataset
from tqdm import tqdm

KEYWORDS = [
  r"\bsonogenetic", r"\bultrasound neuromod", r"\bfocused ultrasound\b",
  r"\bprestin\b", r"\bMscL\b", r"\bgas vesicle", r"\bacoustic reporter gene",
  r"\bmechanical index\b", r"\bPRF\b", r"\bduty cycle\b"
]
compiled_keywords = [re.compile(k, re.IGNORECASE) for k in KEYWORDS]

OUT_FILE = "data/candidates/pmcoa_candidates.jsonl"
STATE_FILE = "data/candidates/state.json"

def check_paper(ex):
    text = (ex.get("text") or ex.get("article") or "")
    title = ex.get("title") or ""
    
    # Check if any keyword hits
    t_search = text.lower()
    for pat in compiled_keywords:
        if pat.search(t_search) or pat.search(title):
            return {
                "title": title,
                "url": ex.get("url") or ex.get("pmcid") or "",
                "pmcid": ex.get("pmcid"),
                "doi": ex.get("doi"),
                "year": ex.get("year"),
                "text": text[:25000]
            }
    return None

def main():
    os.makedirs("data/candidates", exist_ok=True)
    
    # Load state
    start_idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                start_idx = state.get("processed_count", 0)
        except: pass
    
    print(f"Resuming from index {start_idx}...")

    # Load dataset streaming
    try:
        ds = load_dataset("gabrielaltay/pmcoa", split="train", streaming=True)
    except Exception:
        ds = load_dataset("gabrielaltay/pmcoa", split="train")
    
    iterator = iter(ds)
    
    # Fast forward
    if start_idx > 0:
        print(f"Fast-forwarding {start_idx} records...")
        for _ in tqdm(range(start_idx), desc="Skipping"):
            next(iterator, None)

    # Worker pool
    num_cpus = max(1, mp.cpu_count() - 1)
    pool = mp.Pool(processes=num_cpus)
    
    batch_size = 1000
    batch = []
    
    processed_count = start_idx
    
    # We append to output if resuming
    mode = "a" if start_idx > 0 else "w"
    
    with open(OUT_FILE, mode, encoding="utf-8") as f_out:
        for item in tqdm(iterator, desc="Filtering", initial=start_idx):
            batch.append(item)
            
            if len(batch) >= batch_size:
                # Parallel process
                results_list = pool.map(check_paper, batch)
                
                # Write hits
                for h in results_list:
                    if h:
                        f_out.write(json.dumps(h, ensure_ascii=False) + "\n")
                f_out.flush()
                
                processed_count += len(batch)
                batch = []
                
                # Update state occasionally
                with open(STATE_FILE, "w") as f_state:
                    json.dump({"processed_count": processed_count}, f_state)
        
        # Process remaining
        if batch:
            results_list = pool.map(check_paper, batch)
            for h in results_list:
                if h:
                    f_out.write(json.dumps(h, ensure_ascii=False) + "\n")
            processed_count += len(batch)

    # Final state
    with open(STATE_FILE, "w") as f_state:
        json.dump({"processed_count": processed_count}, f_state)
    
    pool.close()
    pool.join()

if __name__ == "__main__":
    mp.set_start_method("fork", force=True) # efficient on mac
    main()

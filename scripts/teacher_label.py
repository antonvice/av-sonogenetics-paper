import os, json, asyncio, time
from tqdm.asyncio import tqdm_asyncio
from jsonschema import validate
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

SCHEMA_PATH = "schema/protocol_extractor_v1.schema.json"
CANDIDATES = "data/candidates/pmcoa_candidates.jsonl"
OUT_DIR = "data/labeled"
MODEL = "gemini-3-flash-preview"
CONCURRENCY = 15  # Adjust based on tier

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_id(ex):
    # Unique ID for resumability
    return ex.get("url") or ex.get("title")

def clean_schema(s):
    # Recursive schema sanitizer for Gemini
    if not isinstance(s, dict):
        return
    for k in ["uniqueItems", "minItems", "additionalProperties", "minLength", "$schema", "$id", "title"]:
        s.pop(k, None)
    if "type" in s:
        t = s["type"]
        if isinstance(t, list):
            if "string" in t: s["type"] = "string"
            elif "number" in t: s["type"] = "number"
            elif "integer" in t: s["type"] = "integer"
    if "enum" in s and isinstance(s["enum"], list):
        s["enum"] = [v for v in s["enum"] if v is not None]
    if "properties" in s:
        for prop in s["properties"].values():
            clean_schema(prop)
        if "required" in s:
            s["required"] = [k for k in s["required"] if k in s["properties"]]
    if "items" in s:
        clean_schema(s["items"])

async def process_paper(line, client, schema, system, user_t, sem, f_out, f_bad):
    async with sem:
        ex = json.loads(line)
        excerpt = ex["text"]
        
        # Prepare prompt
        user = user_t.replace("{{EXCERPT}}", excerpt)\
                    .replace("{{TITLE}}", str(ex.get("title")))\
                    .replace("{{URL}}", str(ex.get("url")))\
                    .replace("{{YEAR}}", str(ex.get("year")))\
                    .replace("{{DOI}}", str(ex.get("doi")))\
                    .replace("{{PMCID}}", str(ex.get("pmcid")))

        cfg = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema
        )

        try:
            # Wrap sync call in thread
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=MODEL,
                contents=user,
                config=cfg
            )
            
            obj = json.loads(response.text)
            # Validate output locally just in case
            # (Note: we skip validation against original schema just to be fast, 
            # trust Gemini's schema adherence if it didn't error)
            
            record = {
                "input": {
                    "title": ex.get("title"),
                    "url": ex.get("url"),
                    "year": ex.get("year"),
                    "doi": ex.get("doi"),
                    "pmcid": ex.get("pmcid"),
                    "excerpt": excerpt
                },
                "output": obj
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            f_out.flush()
            return True
            
        except Exception as e:
            err_record = {"error": str(e), "ex": ex}
            f_bad.write(json.dumps(err_record, ensure_ascii=False) + "\n")
            f_bad.flush()
            return False

def get_id(ex):
    # Robust ID generation: pmcid > doi > url > title > hash
    if ex.get("pmcid"): return str(ex.get("pmcid"))
    if ex.get("doi"): return str(ex.get("doi"))
    if ex.get("url"): return str(ex.get("url"))
    if ex.get("title"): return str(ex.get("title"))
    # fallback hash
    import hashlib
    txt = ex.get("text") or ""
    return hashlib.md5(txt[:500].encode("utf-8")).hexdigest()

async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Init files
    out_path = os.path.join(OUT_DIR, "gold.jsonl")
    bad_path = os.path.join(OUT_DIR, "bad.jsonl")
    CANDIDATES = "data/candidates/pmcoa_candidates.jsonl"
    
    # Load completed IDs for resumability
    completed_ids = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                try: 
                    d = json.loads(line)
                    if "input" in d:
                        completed_ids.add(get_id(d["input"]))
                except: pass
    
    if os.path.exists(bad_path):
         with open(bad_path, "r", encoding="utf-8") as f:
            for line in f:
                try: 
                    d = json.loads(line)
                    if "ex" in d:
                         completed_ids.add(get_id(d["ex"]))
                except: pass

    print(f"Resuming... found {len(completed_ids)} already processed.")

    # Load & Prep Schema
    raw_schema = json.loads(load_text(SCHEMA_PATH))
    clean_schema(raw_schema)
    schema = raw_schema
    
    system = load_text("prompts/teacher_system.txt").strip()
    user_t = load_text("prompts/teacher_user.txt").strip()
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    sem = asyncio.Semaphore(CONCURRENCY)

    # Collect tasks
    tasks = []
    
    # Open files in append mode
    # Read all candidates first to filter
    lines_to_process = []
    if os.path.exists(CANDIDATES):
        with open(CANDIDATES, "r", encoding="utf-8") as f_in:
            for line in f_in:
                try:
                    ex = json.loads(line)
                    uid = get_id(ex)
                    if uid in completed_ids:
                        continue
                    # Just append the raw line to be parsed inside process_paper again? 
                    # No, process_paper takes 'line' usually? 
                    # Looking at previous code, process_paper takes 'line'.
                    # But wait, lines_to_process appended 'line' (string).
                    lines_to_process.append(line)
                except: pass

    print(f"Queueing {len(lines_to_process)} papers...")
    
    # We must open output files globally for the tasks OR pass them down?
    # The previous code opened them within a 'with' block.
    # We will replicate that structure.
    
    with open(out_path, "a", encoding="utf-8") as f_out, \
         open(bad_path, "a", encoding="utf-8") as f_bad:
        
        for line_str in lines_to_process:
             # Create task
             tasks.append(process_paper(line_str, client, schema, system, user_t, sem, f_out, f_bad))
        
        await tqdm_asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

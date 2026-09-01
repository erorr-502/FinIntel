import json,re
from pathlib import Path
DOCS=json.loads((Path(__file__).parent/"data"/"disclosures.json").read_text(encoding="utf-8"))
def tok(s): return set(re.findall(r"[a-zA-Z0-9]+",s.lower()))
def retrieve(symbol,query,top_k=2):
    q=tok(query); scored=[]
    for d in DOCS:
        if d["symbol"]!=symbol: continue
        scored.append((len(q & tok(d["title"]+" "+d["text"])),d))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{"doc_id":d["doc_id"],"title":d["title"],"text":d["text"],"query_terms":query} for _,d in scored[:top_k]]

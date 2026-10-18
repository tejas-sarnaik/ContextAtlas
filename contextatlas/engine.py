"""Deterministic retrieval and budget-aware evidence assembly.

All token counts are approximate whitespace/punctuation tokens, not model tokenizer counts.
"""
from __future__ import annotations
import math, re
from collections import Counter

STOPWORDS = set("a an the and or of to in for on by with as at is are was were be been this that from how what which does do can an into their we it its our your about using based under across".split())
WORD = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in WORD.findall(text) if t.lower() not in STOPWORDS]

def token_cost(text: str) -> int:
    """Explainable lexical token approximation; NOT a provider tokenizer."""
    return max(1,len(re.findall(r"\w+|[^\w\s]",text,flags=re.UNICODE)))

def similarity(a:set[str],b:set[str]) -> float:
    return len(a&b)/len(a|b) if a|b else 0.0

def bm25(query: list[str], docs: list[list[str]]) -> list[float]:
    if not docs:return []
    n=len(docs);lengths=[len(x) for x in docs];avg=max(1,sum(lengths)/n)
    dfs=Counter(t for d in docs for t in set(d))
    out=[]
    for d in docs:
        counts=Counter(d);score=0.0
        for word in set(query):
            df=dfs.get(word,0)
            if not df:continue
            idf=math.log(1+(n-df+0.5)/(df+0.5))
            tf=counts[word]
            score+=idf*(tf*2.2)/(tf+1.2*(0.25+0.75*len(d)/avg)) if tf else 0
        out.append(score)
    return out

def _prepare(chunks):
    results=[]
    for i, x in enumerate(chunks):
        if isinstance(x,str):x={"text":x,"source":f"Document {i+1}"}
        if not isinstance(x,dict) or not isinstance(x.get("text"),str):
            raise ValueError("Every chunk must be a string or an object containing text")
        txt=x["text"].strip()
        if not txt:continue
        results.append({"id":str(x.get("id",f"C{i+1:02d}")),"source":str(x.get("source",f"Document {i+1}")),"text":txt,"tokens":token_cost(txt)})
    return results

def _metrics(selected,budget):
    tokens=sum(x["tokens"] for x in selected)
    overlap=[similarity(set(tokenize(a["text"])),set(tokenize(b["text"]))) for i,a in enumerate(selected) for b in selected[i+1:]]
    return {"tokens":tokens,"utilization":round(tokens/budget,3),"mean_relevance":round(sum(x["relevance"] for x in selected)/len(selected),3) if selected else 0.0,"redundancy":round(sum(overlap)/len(overlap),3) if overlap else 0.0,"chunks":len(selected)}

def analyze(query:str,chunks:list,budget:int=120,diversity:float=0.55)->dict:
    """Compare fit-aware relevance baseline with redundancy-aware marginal utility packing.

    Objective heuristic: (normalized BM25 relevance + query-term coverage bonus
    - diversity * max Jaccard-to-selected) / sqrt(estimated tokens).
    This is a deterministic heuristic, NOT globally optimal knapsack.
    """
    if not isinstance(query,str) or not query.strip():raise ValueError("A non-empty query is required")
    if not isinstance(budget,int) or not 1<=budget<=100000:raise ValueError("budget must be 1..100000")
    if not isinstance(diversity,(int,float)) or not 0<=diversity<=1:raise ValueError("diversity must be between 0 and 1")
    if not isinstance(chunks,list) or len(chunks)>300:raise ValueError("Provide a list of at most 300 chunks")
    items=_prepare(chunks)
    if not items:raise ValueError("At least one non-empty chunk is required")
    q=tokenize(query); doc_toks=[tokenize(x["text"]) for x in items]
    scores=bm25(q,doc_toks);mx=max(scores) or 1.0
    for x,s,toks in zip(items,scores,doc_toks):
        x["relevance"]=round(s/mx,5);x["keywords"]=sorted(set(toks)&set(q))
        x["score"]=0.0;x["why"]="Not selected";x["raw_bm25"]=round(s,4)
    remaining=budget;base=[]
    for x in sorted(items,key=lambda z:(-z["relevance"],z["id"])):
        if x["tokens"]<=remaining and x["relevance"]>0:
            base.append(x);remaining-=x["tokens"]
    selected=[];unused=list(items);remaining=budget;covered=set()
    while True:
        scored=[]
        for x in unused:
            if x["tokens"]>remaining or x["relevance"]<=0:continue
            terms=set(tokenize(x["text"]))
            repetition=max((similarity(terms,set(tokenize(y["text"]))) for y in selected),default=0.0)
            novel=len(set(x["keywords"])-covered)/max(1,len(set(q)))
            utility=(x["relevance"]+0.35*novel-diversity*repetition)/math.sqrt(x["tokens"])
            scored.append((utility,x["id"],x,repetition,novel))
        if not scored:break
        utility,_,chosen,rep,novel=max(scored,key=lambda z:(z[0],z[1]))
        if utility<=0:break
        chosen["score"]=round(utility,5)
        chosen["why"]=f"Relevance {chosen['relevance']:.2f} · new-term coverage {novel:.2f} · overlap penalty {rep:.2f}"
        selected.append(chosen);unused.remove(chosen);remaining-=chosen["tokens"];covered.update(chosen["keywords"])
    selected.sort(key=lambda x:(-x["relevance"],x["id"]))
    return {"query":query,"budget":budget,"diversity":diversity,"selected":selected,"baseline":base,"rejected":[x for x in items if x not in selected],"all_chunks":items,"optimized_metrics":_metrics(selected,budget),"baseline_metrics":_metrics(base,budget),"assembled_context":"\n\n".join(f"[{x['id']}] {x['source']}\n{x['text']}" for x in selected),"limitations":["Token counts are estimates; use a model tokenizer before deployment.","Scores are lexical heuristics, not learned relevance or answer-faithfulness estimates.","No LLM is called and no generated answer quality is claimed."]}

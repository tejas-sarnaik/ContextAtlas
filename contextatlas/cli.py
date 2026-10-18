import argparse,json
from pathlib import Path
from .engine import analyze
from .server import serve

def main():
    p=argparse.ArgumentParser(prog="contextatlas",description="Inspect budget-aware RAG context selection")
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("serve",help="Launch local UI");s.add_argument("--port",type=int,default=8765)
    a=sub.add_parser("analyze",help="Analyze a JSON file with query and chunks")
    a.add_argument("input",type=Path);a.add_argument("--budget",type=int);a.add_argument("--diversity",type=float);a.add_argument("--output",type=Path)
    args=p.parse_args()
    if args.command=="serve":return serve(port=args.port)
    payload=json.loads(args.input.read_text(encoding="utf8"))
    result=analyze(payload["query"],payload["chunks"],args.budget if args.budget is not None else payload.get("budget",120),args.diversity if args.diversity is not None else payload.get("diversity",0.55))
    out=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output:args.output.write_text(out,encoding="utf8");print(f"Saved {args.output}")
    else:print(out)
if __name__=="__main__":main()

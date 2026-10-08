import json,re,statistics,subprocess
from collections import Counter,defaultdict
from pathlib import Path
import yaml
r=Path(__file__).resolve().parents[2]
ps=[yaml.safe_load(p.read_text()) for p in (r/'state/projects').glob('*.yaml')]
report={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'stages':dict(Counter(p['current_stage'] for p in ps))}
tasks=[]; invisible=[]
old=re.compile(r'^- \[[ Xx]\]\s+(T\d+[a-z]?)(?=\s|$).*$',re.M)
for p in ps:
 d=p.get('speckit_research_dir')
 f=r/d/'tasks.md' if d else None
 if not f or not f.exists():continue
 lines=[s for s in f.read_text().splitlines() if re.match(r'^\s*-\s*\[[ xX~]\]\s',s)]
 tasks.append(len(lines))
 for s in lines:
  if re.match(r'^\s*-\s*\[ \]\s',s) and not old.match(s):invisible.append({'project':p['id'],'stage':p['current_stage'],'line':s[:500]})
report['task_counts']={'projects':len(tasks),'median':statistics.median(tasks),'max':max(tasks),'total':sum(tasks)}
report['unparseable_open_tasks']=invisible
for d in ['execution_status','advance_errors','paper_status']:
 rows=[json.loads(p.read_text()) for p in (r/'state'/d).glob('*.json')]
 report[d]={'count':len(rows),'classes':dict(Counter(str(p.get('failure_class',p.get('class',p.get('status')))) for p in rows))}
 report[d]['top_reasons']=Counter(str(p.get('reason',p.get('last_error','')))[:160] for p in rows).most_common(8)
 if d=='execution_status':report[d]['passed_projects']=[p.get('project_id') for p in rows if p.get('ok')]
counts=Counter(); models=Counter(); noops=Counter(); latest={}; n=0
for f in (r/'state/run-log').rglob('*.jsonl'):
 for line in f.read_text(errors='replace').splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  n+=1
  if str(e.get('ended_at',''))<'2026-10-01':continue
  counts[(e.get('agent_name'),e.get('outcome'))]+=1;models[e.get('model_name')]+=1
  pid=e.get('project_id'); end=str(e.get('ended_at',''))
  if end>str(latest.get(pid,{}).get('ended_at','')):latest[pid]=e
  if not e.get('outputs') and not e.get('committed_paths'):noops[e.get('agent_name')]+=1
report['run_entries_total']=n; report['week_agent_outcomes']=[[*k,v] for k,v in counts.most_common()];report['week_models']=dict(models);report['week_no_output_entries']=dict(noops)
(r/'notes/audit-20261008/baseline.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='unparseable_open_tasks'},indent=2)[:14000])
print('unparseable_open_tasks',len(invisible),'projects',len({p['project'] for p in invisible}));print(invisible[:6])

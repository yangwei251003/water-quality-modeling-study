"""Run the archived EDA, prediction, lag/risk examples on synthetic CSV only."""
from pathlib import Path
import subprocess,sys,os,json,time,argparse
root=Path(__file__).resolve().parents[1];work=root/'.runtime'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--resume-from',choices=['phase2','phase3'],help='Reuse a successfully completed synthetic predecessor; do not regenerate input or repeat prior phases')
args=parser.parse_args()
steps=['phase1_eda.py','phase2_problem1.py','phase3_problems234.py'];rows=[]
if args.resume_from:
 meta=json.loads((work/'SYNTHETIC.json').read_text(encoding='utf-8'))
 if meta.get('data_kind')!='synthetic' or meta.get('real_observations')!=0 or not(work/'.apmcm-workspace').is_file():raise RuntimeError('Resume is limited to this initialized synthetic workspace')
 previous=json.loads((work/'run-summary.json').read_text(encoding='utf-8'))
 start=1 if args.resume_from=='phase2' else 2
 for name in steps[:start]:
  record=next((r for r in previous if r['script']==name and r['exit_code']==0),None)
  if record is None:raise RuntimeError('No successful predecessor for '+name)
  rows.append(record)
 steps=steps[start:]
else:subprocess.run([sys.executable,str(root/'scripts/create_demo.py')],check=True)
env=os.environ.copy();env.update(APMCM_WORKDIR=str(work),MPLBACKEND='Agg',PYTHONIOENCODING='utf-8',PYTHONUTF8='1',OMP_NUM_THREADS='2')
for name in steps:
 start=time.monotonic();log=work/(name+'.log')
 with log.open('wb')as f:p=subprocess.run([sys.executable,str(root/'src'/name)],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT)
 rows.append({'script':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,2),'input_kind':'synthetic','log':log.name})
 (work/'run-summary.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
 print(json.dumps(rows[-1]),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('Synthetic example completed. Logs and generated data remain local in .runtime; do not present these scores as real findings.')

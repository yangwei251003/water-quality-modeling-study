"""Generate only synthetic data in an isolated workspace; no source data read."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1]/'.runtime')
args=parser.parse_args();root=args.workspace.resolve();marker=root/'.apmcm-workspace'
if root.exists()and any(root.iterdir())and not marker.is_file():raise SystemExit('Refusing a nonempty directory without this project workspace marker.')
root.mkdir(parents=True,exist_ok=True);marker.write_text('Synthetic demonstration workspace. Never treat its data or scores as real observations.\n')
processed=root/'data/processed';processed.mkdir(parents=True,exist_ok=True);(root/'output/figures').mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(20261026)
dates=pd.DatetimeIndex([*pd.date_range('2025-01-01','2025-12-31',freq='D'),*pd.date_range('2026-01-01','2026-03-31 22:00',freq='2h')])
n=len(dates);t=np.arange(n);season=np.sin(t/65);raw_ntu=25+5*season+rng.normal(0,2,n);alum=32+raw_ntu*.2+rng.normal(0,1.3,n);filtered=.5+.009*raw_ntu+.002*alum+rng.normal(0,.02,n);out_ntu=.08+.42*filtered+rng.normal(0,.012,n)
df=pd.DataFrame({'DATETIME':dates.astype(str),'DATE':dates.strftime('%Y-%m-%d'),'TIME':dates.strftime('%H:%M'),'TIME_PARSED':dates.strftime('%H:%M'),'RIVER LEVEL':3+.2*season+rng.normal(0,.04,n),'R/W PUMP DUTY':65+rng.normal(0,3,n),'R/W FLOW':1100+35*season+rng.normal(0,10,n),'R/W NTU':raw_ntu,'R/W CLR':12+.3*raw_ntu+rng.normal(0,.5,n),'R/W PH':7.2+rng.normal(0,.06,n),'FILT. NTU':filtered,'C/W WELL LEVEL':4+rng.normal(0,.1,n),'PH':7.1+rng.normal(0,.05,n),'NTU':out_ntu,'CLR':3+.2*out_ntu+rng.normal(0,.1,n),'CL2':.6+rng.normal(0,.025,n),'F/RIDE':18+.1*alum+rng.normal(0,.6,n),'ALUM':alum,'T/W PUMP DUTY':60+rng.normal(0,3,n),'T/W FLOW':1020+rng.normal(0,15,n),'18ML LEVEL':5+rng.normal(0,.08,n),'18ML FLOW':120+rng.normal(0,5,n),'REMARKS':['SYNTHETIC FIXTURE - NOT A WATER PLANT RECORD']*n,'_source_year':dates.year,'_source_month':dates.month})
df.to_csv(processed/'df_raw_merged.csv',index=False,encoding='utf-8-sig')
df[dates.year==2026].to_csv(processed/'df_2026_dates_corrected.csv',index=False,encoding='utf-8-sig')
df[dates.year==2025].to_csv(processed/'df_2025_only.csv',index=False,encoding='utf-8-sig')
meta={'data_kind':'synthetic','seed':20261026,'rows':n,'real_observations':0,'raw_excel_import_exercised':False,'purpose':'Smoke-test archived analysis code; not reproduce historic metrics or validate a real water treatment process.'}
(root/'SYNTHETIC.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print(json.dumps(meta))

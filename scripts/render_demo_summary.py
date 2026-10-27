"""Draw publication-safe diagnostics from the verified synthetic workspace only; never uses historical scores or source spreadsheets."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workspace',type=Path,default=ROOT/'.runtime');ap.add_argument('--output',type=Path,default=ROOT/'docs/images');args=ap.parse_args()
 W=args.workspace.resolve();meta=json.loads((W/'SYNTHETIC.json').read_text(encoding='utf-8'))
 if meta.get('data_kind')!='synthetic' or meta.get('real_observations')!=0:raise RuntimeError('Only explicitly synthetic fixtures are accepted')
 df=pd.read_csv(W/'data/processed/df_raw_merged.csv');df['DATETIME']=pd.to_datetime(df['DATETIME'])
 q2=json.loads((W/'output/Q2_results.json').read_text());q3=json.loads((W/'output/Q3_results.json').read_text());risk=pd.read_csv(W/'output/Q4_risk_assessment.csv')
 assert len(df)==meta['rows'] and all(np.isfinite(x) for x in q2.values())
 assert len(q3)==6 and all(np.isfinite(v[k]) for v in q3.values() for k in ['rmse','r2'])
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,axes=plt.subplots(2,1,figsize=(11,7.2),layout='constrained')
 fig.suptitle(f'SYNTHETIC DEMO ONLY — {len(df):,} generated rows',fontsize=17,fontweight='bold')
 axes[0].plot(df['DATETIME'],df['R/W NTU'],color='#21668b',lw=1);axes[0].set(title='Generated input signal',ylabel='Raw-water field (synthetic NTU)');axes[0].grid(alpha=.2)
 axes[1].plot(df['DATETIME'],df['NTU'],color='#008975',lw=1);axes[1].set(title='Generated target = simple formula + noise',ylabel='Target field (synthetic NTU)',xlabel='Synthetic calendar');axes[1].grid(alpha=.2)
 fig.savefig(out/'synthetic-input-overview.png',dpi=150,metadata={'Title':'Synthetic fixture only; not water plant observations'});plt.close(fig)
 fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained');fig.suptitle('SYNTHETIC DEMO ONLY — software diagnostics, no real-world performance claim',fontsize=15,fontweight='bold')
 values=[q2['ARX_R2'],q2['NARX_R2']];axes[0].bar(['ARX','NARX/XGB'],values,color=['#21668b','#008975']);axes[0].set(title='Archived lag-model R²',ylabel='R² on synthetic split',ylim=(-.05,1))
 for i,v in enumerate(values):axes[0].text(i,v+.025,f'{v:.3f}',ha='center')
 steps=list(range(1,7));scores=[q3[f'step_{i}']['r2'] for i in steps];axes[1].plot(steps,scores,'o-',color='#b4771d');axes[1].set(title='Six sample-offset forecasts',xlabel='Sample step (not validated hours)',ylabel='R²',ylim=(-.05,1),xticks=steps);axes[1].grid(alpha=.2)
 axes[2].plot(pd.to_datetime(risk['日期']),risk['风险评分R'],color='#a0505b');axes[2].axhline(0,color='#777',lw=.8);axes[2].set(title='Legacy heuristic index',xlabel='Synthetic days',ylabel='Uncalibrated score');axes[2].tick_params(axis='x',rotation=25);axes[2].grid(alpha=.2)
 fig.savefig(out/'synthetic-model-diagnostics.png',dpi=150,metadata={'Title':'Synthetic model diagnostics only; legacy assumptions not validated'});plt.close(fig)
 summary={'input_kind':'synthetic','rows':len(df),'real_observations':0,'q2':q2,'q3':q3,'risk_days':len(risk),'risk_heuristic_min':float(risk['风险评分R'].min()),'risk_heuristic_max':float(risk['风险评分R'].max()),'not_real_water_safety_assessment':True,'forecast_steps_not_validated_hours':True}
 (out.parent/'synthetic-demo-results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps({'plots':2,'synthetic_rows':len(df),'q3_steps':len(q3),'real_observations':0}))
if __name__=='__main__':main()

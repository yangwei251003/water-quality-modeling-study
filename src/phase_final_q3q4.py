"""
亚太杯A题 — 最终交付：Q3深度预测 + Q4修正 + Nature图表
"""

from project_paths import WORKDIR
import pandas as pd, numpy as np, os, json, warnings
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import RidgeCV
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import spearmanr
import xgboost as xgb
warnings.filterwarnings('ignore')

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "output")
FIG = os.path.join(BASE, "output", "figures")

# Nature配色
NC = {"blue":"#2E86AB","red":"#E94F37","green":"#27AE60","purple":"#A23B72",
      "orange":"#E67E22","teal":"#00A896","navy":"#2C3E50","gold":"#F39C12","gray":"#7F8C8D"}

plt.rcParams.update({
    'font.family':'sans-serif','font.sans-serif':['Arial'],'font.size':9,
    'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':0.8,'grid.alpha':0.3,'figure.dpi':200,'savefig.dpi':300,'savefig.bbox':'tight'
})

print("="*60)
print("Q3 深度预测 + Q4 修正 + Nature图表")
print("="*60)

# ====== Load data ======
df = pd.read_csv(os.path.join(BASE, "data", "processed", "df_final_merged.csv"))
df['DATE'] = pd.to_datetime(df['DATE'])
df2026 = df[df['_YEAR']==2026].copy()

print(f"2026 data: {len(df2026)} rows, dates: {df2026['DATE'].min().date()} ~ {df2026['DATE'].max().date()}")

# ====== Q3: Deep multi-step prediction with proper CSTR + XGBoost ======
print("\n" + "="*60)
print("Q3: CSTR + XGBoost 混合预测 (1-12小时)")
print("="*60)

V = 18000  # m³, CSTR volume (18ML)
dt = 2.0   # hours between readings

def cstr_predict(ntu_filt, flow_in, flow_out, ntu_init=0.1):
    """清水池CSTR模型预测"""
    n = len(ntu_filt)
    ntu_cw = np.zeros(n)
    ntu_cw[0] = ntu_init
    for t in range(1, n):
        Qin = flow_in[min(t, len(flow_in)-1)]
        Qout = flow_out[min(t, len(flow_out)-1)]
        dN = (Qin * ntu_filt[t] - Qout * ntu_cw[t-1]) * dt
        ntu_cw[t] = max(0, ntu_cw[t-1] + dN / V)
    return ntu_cw

# Prepare multi-step prediction data
feature_cols = ['FILT. NTU','R/W NTU','R/W FLOW','ALUM','NTU']
available = [c for c in feature_cols if c in df2026.columns]
print(f"  Available features: {available}")

# Build multi-step dataset
history_len = 6  # past 6 readings = past 12 hours
future_steps = 6  # predict 1,2,4,6,8,12h ahead

X3, y3 = [], []
for i in range(history_len, len(df2026) - 6):
    past = df2026.iloc[i-history_len:i][available].values.flatten()
    if np.any(np.isnan(past)): continue
    # Target: NTU at +1h, +2h, +4h, +6h, +8h, +12h
    future_vals = []
    for step in [0, 1, 2, 3, 4, 5]:  # indices 0-5 = 0,2,4,6,8,12h
        future_vals.append(df2026.iloc[i+step]['NTU'])
    X3.append(past)
    y3.append(future_vals)

X3 = np.array(X3); y3 = np.array(y3)
X3 = np.nan_to_num(X3, 0); y3 = np.nan_to_num(y3, 0)

print(f"  Multi-step dataset: {len(X3)} samples")

# Train models for each step
scaler3 = RobustScaler()
X3s = scaler3.fit_transform(X3)
split = int(len(X3) * 0.8)

models_q3 = {}
predictions_q3 = {}
hours = [0, 2, 4, 6, 8, 12]

for step_idx, hour_label in enumerate(hours):
    m = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.03, random_state=42)
    m.fit(X3s[:split], y3[:split, step_idx])
    ypred = m.predict(X3s[split:])
    rmse = np.sqrt(mean_squared_error(y3[split:, step_idx], ypred))
    r2 = r2_score(y3[split:, step_idx], ypred)
    models_q3[step_idx] = m
    predictions_q3[f"t+{hour_label}h"] = {"RMSE": round(float(rmse),4), "R2": round(float(r2),4)}
    print(f"  t+{hour_label:2d}h: RMSE={rmse:.4f}, R²={r2:.4f}")

# Predict for target dates
print("\n🎯 Q3 目标日期预测:")
predictions_output = []
for date_str in ['2026-02-01', '2026-02-10', '2026-02-20']:
    mask = df2026['DATE'].dt.strftime('%Y-%m-%d') == date_str
    if mask.sum() == 0: continue
    
    day_data = df2026[mask].copy()
    print(f"\n  {date_str}: {len(day_data)} time points")
    
    for idx in range(len(day_data)):
        time_str = f"{idx*2:02d}:00"
        if idx + 6 > len(day_data):
            # Use last available data point
            X_input = day_data.iloc[-history_len:][available].fillna(
                df2026[available].median()).values.flatten()
        else:
            X_input = day_data.iloc[idx:idx+history_len][available].fillna(
                df2026[available].median()).values.flatten()
        
        X_input = np.nan_to_num(X_input, 0)
        X_scaled = scaler3.transform(X_input.reshape(1, -1))
        
        row_preds = {"日期": date_str, "时间": time_str}
        for step_idx, hour_label in enumerate(hours):
            pred_val = models_q3[step_idx].predict(X_scaled)[0]
            row_preds[f"NTU+{hour_label}h"] = round(float(pred_val), 4)
        
        predictions_output.append(row_preds)

df_q3_out = pd.DataFrame(predictions_output)
df_q3_out.to_csv(os.path.join(OUT, "Q3_predictions_final.csv"), index=False, encoding="utf-8-sig")
print(f"\n  ✅ Q3预测已保存: {len(df_q3_out)} point × {len(hours)} horizons")

# CSTR model comparison
if 'FILT. NTU' in df2026.columns and 'R/W FLOW' in df2026.columns:
    cstr_sample = df2026[['FILT. NTU','R/W FLOW','T/W FLOW','NTU']].dropna()
    if len(cstr_sample) > 200:
        ntu_cstr = cstr_predict(
            cstr_sample['FILT. NTU'].values[:200],
            cstr_sample['R/W FLOW'].values[:200],
            cstr_sample['T/W FLOW'].values[:200]
        )
        actual = cstr_sample['NTU'].values[:200]
        rmse_cstr = np.sqrt(mean_squared_error(actual, ntu_cstr))
        r2_cstr = r2_score(actual, ntu_cstr)
        print(f"\n  CSTR物理模型: RMSE={rmse_cstr:.4f}, R²={r2_cstr:.4f}")
        predictions_q3["CSTR_physical"] = {"RMSE": round(float(rmse_cstr),4), "R2": round(float(r2_cstr),4)}

# Q3 Nature figure: multi-step prediction panel
fig, axes = plt.subplots(2, 3, figsize=(12, 8))
axes = axes.flatten()
for step_idx in range(6):
    ax = axes[step_idx]
    ypred = models_q3[step_idx].predict(X3s[split:])
    ytrue = y3[split:, step_idx]
    
    ax.scatter(ytrue, ypred, alpha=0.4, s=10, c=NC["blue"], edgecolor="none")
    mn, mx = min(ytrue.min(), ypred.min()), max(ytrue.max(), ypred.max())
    ax.plot([mn, mx], [mn, mx], '--', color=NC["red"], linewidth=1, alpha=0.6)
    
    r2 = predictions_q3[f"t+{hours[step_idx]}h"]["R2"]
    rmse = predictions_q3[f"t+{hours[step_idx]}h"]["RMSE"]
    ax.text(0.05, 0.93, f"R²={r2:.3f}\nRMSE={rmse:.3f}", transform=ax.transAxes,
           fontsize=7, va="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    ax.set_xlabel("Observed", fontsize=8); ax.set_ylabel("Predicted", fontsize=8)
    ax.set_title(f"Outflow NTU at t+{hours[step_idx]}h", fontsize=10, fontweight="bold")

fig.suptitle("Q3 — Multi-Step Effluent NTU Prediction (XGBoost)", fontsize=13, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_nature_q3_multistep.pdf"), dpi=300)
fig.savefig(os.path.join(FIG, "fig_nature_q3_multistep.png"), dpi=300)
plt.close()
print("  ✅ Q3 Nature图表已保存")

# ====== Q4: Full 2026 Q1 risk with corrected data ======
print("\n" + "="*60)
print("Q4: 2026年1-3月逐日风险分级 (数据已修正)")
print("="*60)

q4 = df2026[df2026['DATE'].dt.month.isin([1,2,3])].copy()
q4['DAY'] = q4['DATE'].dt.date

def risk_magnitude(ntu_series): return np.mean(np.clip(np.maximum(0, np.array(ntu_series) - 1), 0, 10))
def risk_duration_h(vals):
    mx, cur = 0, 0
    for v in vals:
        cur = cur + 1 if v > 1 else 0
        mx = max(mx, cur)
    return mx * 2

daily = q4.groupby('DAY').agg(
    max_ntu=('NTU','max'), mean_ntu=('NTU','mean'), 
    std_ntu=('NTU','std'), vals=('NTU',list), n=('NTU','count')
).reset_index()

risk_records = []
for _, r in daily.iterrows():
    if r['n'] < 4: continue
    fm = risk_magnitude(r['vals'])
    fd = min(risk_duration_h(r['vals']) / 24, 1)
    ft = np.clip(abs(np.mean(np.diff(r['vals'][-6:])) / (0.5 if len(r['vals'])>=6 else 1)), 0, 1)
    R = 0.40 * fm + 0.35 * fd + 0.25 * ft
    
    if R < 0.12: level = "安全"
    elif R < 0.30: level = "低风险"
    elif R < 0.65: level = "中风险"
    else: level = "高风险"
    
    risk_records.append({
        "日期": str(r['DAY']), "最大NTU": round(float(r['max_ntu']), 4),
        "平均NTU": round(float(r['mean_ntu']), 4), "NTU标准差": round(float(r['std_ntu']), 4),
        "超标幅值": round(float(fm), 4), "连续超标时(h)": round(risk_duration_h(r['vals']), 1),
        "风险评分R": round(float(R), 4), "风险等级": level, "记录数": int(r['n'])
    })

df_risk = pd.DataFrame(risk_records)
df_risk.to_csv(os.path.join(OUT, "Q4_2026Q1_daily_risk_final.csv"), index=False, encoding="utf-8-sig")

# Statistics
lc = df_risk["风险等级"].value_counts()
td = len(df_risk)
print(f"\n  2026年1-3月风险分布 ({td}天):")
for lv in ["安全","低风险","中风险","高风险"]:
    c = lc.get(lv, 0)
    print(f"    {lv}: {c}天 ({c/td*100:.1f}%)")

# March detail
mar = df_risk[df_risk["日期"].str.contains("2026-03")]
print(f"\n  2026年3月详细 ({len(mar)}天):")
mar.to_csv(os.path.join(OUT, "Q4_march_detail_final.csv"), index=False, encoding="utf-8-sig")
for _, r in mar.iterrows():
    print(f"    {r['日期']}: maxNTU={r['最大NTU']:.3f}, R={r['风险评分R']:.3f}, {r['风险等级']}")

# ====== Nature Figures ======
print("\n" + "="*60)
print("统一学术图表生成")
print("="*60)

# Fig A: Comprehensive risk panel
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 9))

# Pie chart
level_colors = [NC["green"], NC["gold"], NC["orange"], NC["red"]]
level_labels = ["Safe", "Low", "Medium", "High"]
sizes = [lc.get(l, 0) for l in [lv for lv in ["安全","低风险","中风险","高风险"]]]
wedges, texts = ax1.pie(sizes, labels=[f"{l}\n{s}d ({s/td*100:.1f}%)" 
    for l, s in zip(level_labels, sizes)], colors=level_colors,
    startangle=90, explode=(0,0,0.03,0.08), textprops={'fontsize':8})
ax1.set_title("Risk Distribution\n(Jan-Mar 2026)", fontsize=11, fontweight="bold", pad=12)

# Scatter
dates_plot = pd.to_datetime(df_risk["日期"])
level_map = {"安全":0,"低风险":1,"中风险":2,"高风险":3}
df_risk["lv_num"] = df_risk["风险等级"].map(level_map)

sc = ax2.scatter(dates_plot, df_risk["最大NTU"], c=df_risk["lv_num"], cmap="RdYlGn_r",
                s=25, edgecolor="white", linewidth=0.3, alpha=0.85)
ax2.axhline(y=1.0, color=NC["red"], linestyle="--", linewidth=1.2, label="GB 5749-2022 (≤1 NTU)")
ax2.set_xlabel("Date", fontsize=10)
ax2.set_ylabel("Max Daily NTU", fontsize=10)
ax2.set_title("Daily Maximum NTU", fontsize=11, fontweight="bold", pad=10)
ax2.legend(fontsize=7, loc="upper right")
cbar = fig.colorbar(sc, ax=ax2, ticks=[0,1,2,3], shrink=0.8)
cbar.ax.set_yticklabels(["Safe","Low","Med","High"], fontsize=7)

# Histogram
ax3.hist(df_risk["风险评分R"], bins=15, color=NC["blue"], alpha=0.7, edgecolor="white", linewidth=0.3)
for th, cl, lb in [(0.12, NC["gold"], "Low"), (0.30, NC["orange"], "Medium"), (0.65, NC["red"], "High")]:
    ax3.axvline(x=th, color=cl, linestyle="--", linewidth=1.2)
    ax3.text(th+0.01, ax3.get_ylim()[1]*0.88, lb, fontsize=7, color=cl)
ax3.set_xlabel("Risk Score R", fontsize=10)
ax3.set_ylabel("Number of Days", fontsize=10)
ax3.set_title("Risk Score Distribution", fontsize=11, fontweight="bold", pad=10)

# March zoom
mar_dates = pd.to_datetime(mar["日期"])
ax4.bar(range(len(mar)), mar["最大NTU"], color=[NC["red"] if v>1 else NC["green"] for v in mar["最大NTU"]],
       edgecolor="white", linewidth=0.3, alpha=0.8)
ax4.axhline(y=1.0, color=NC["red"], linestyle="--", linewidth=1.2, label="Standard")
ax4.set_xticks(range(0, len(mar), 3))
ax4.set_xticklabels([d.split("-")[2] for d in mar["日期"].values[::3]], fontsize=7)
ax4.set_xlabel("March 2026 (Day)", fontsize=10)
ax4.set_ylabel("Max Daily NTU", fontsize=10)
ax4.set_title("March 2026 — Daily NTU Detail", fontsize=11, fontweight="bold", pad=10)
ax4.legend(fontsize=7)

fig.suptitle("Water Quality Risk Assessment (2026 Q1)", fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_nature_risk_panel.pdf"), dpi=300)
fig.savefig(os.path.join(FIG, "fig_nature_risk_panel.png"), dpi=300)
plt.close()
print("  ✅ 风险面板图已保存")

# Save all results
all_results = {
    "Q3": predictions_q3,
    "Q4": {
        "total_days": td,
        "level_distribution": {k: int(v) for k, v in lc.items()},
        "march_days": len(mar),
        "risk_thresholds": {"安全": "R<0.12", "低风险": "0.12≤R<0.30", "中风险": "0.30≤R<0.65", "高风险": "R≥0.65"}
    }
}
with open(os.path.join(OUT, "final_results_complete.json"), "w") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print("✅ 全部完成！")
print(f"  Q3预测: {len(df_q3_out)} 点 × {len(hours)} 时域")
print(f"  Q4风险: {td} 天 (2026-01-01 ~ 2026-03-31)")
print(f"  Nature图表: fig_nature_q3_multistep, fig_nature_risk_panel")
print("="*60)

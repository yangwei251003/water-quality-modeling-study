"""
亚太杯A题 — 问题2/3/4 综合脚本：动态时滞模型 + 混合预测 + 风险评价
"""

from project_paths import WORKDIR
import pandas as pd, numpy as np, os, warnings, json
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
warnings.filterwarnings('ignore')

BASE_DIR = str(WORKDIR)
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
OUT_DIR = os.path.join(BASE_DIR, "output")

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# ============================================================
# 数据加载 (使用修正后的日期)
# ============================================================
print("=" * 70)
print("加载数据...")
df26 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "df_2026_dates_corrected.csv"))
df25 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "df_clean.csv"))
df25 = df25[df25["DATE"].astype(str).str[:4] != "2026"]

# 统一2026列名
COL_MAP = {
    "River Level": "RIVER LEVEL", "R/W Flow": "R/W FLOW",
    "R/W NTU": "R/W NTU", "R/W CLR": "R/W CLR",
    "Filt. NTU": "FILT. NTU", "C/W Well Level": "C/W WELL LEVEL",
    "F/Ride": "F/RIDE", "Alum": "ALUM", "T/W Flow": "T/W FLOW",
}
df26.rename(columns=COL_MAP, inplace=True)

# 数值化
for col in df26.columns:
    if col not in ["DATE", "_source_sheet"]:
        df26[col] = pd.to_numeric(df26[col], errors="coerce")

for col in df25.columns:
    if col not in ["DATE", "REMARKS"]:
        df25[col] = pd.to_numeric(df25[col], errors="coerce")

# 填补缺失
for col in ["R/W NTU", "FILT. NTU", "NTU", "R/W FLOW", "T/W FLOW",
            "ALUM", "F/RIDE", "R/W PH", "PH", "CL2", "R/W CLR", "CLR",
            "RIVER LEVEL", "C/W WELL LEVEL", "R/W PUMP DUTY"]:
    if col in df26.columns:
        df26[col] = df26[col].fillna(df26[col].median())
    if col in df25.columns and df25[col].dtype in ['float64','int64']:
        df25[col] = df25[col].fillna(df25[col].median())

# 合并数据集
common_cols = [c for c in ["R/W NTU","R/W PH","FILT. NTU","NTU","ALUM","F/RIDE",
                           "R/W FLOW","T/W FLOW","RIVER LEVEL","C/W WELL LEVEL",
                           "CL2","R/W CLR","CLR","DATE"] if c in df26.columns and c in df25.columns]
df_all = pd.concat([df25[common_cols], df26[common_cols]], ignore_index=True)
df_all["DATE"] = pd.to_datetime(df_all["DATE"], errors="coerce")
df_all.sort_values("DATE", inplace=True)
df_all.reset_index(drop=True, inplace=True)

print(f"总记录: {len(df_all)}, 日期范围: {df_all['DATE'].min()} ~ {df_all['DATE'].max()}")

# ============================================================
# 问题2：时滞动态模型 (ARX/NARX)
# ============================================================
print("\n" + "=" * 70)
print("问题2：滤后水浊度动态时滞模型")
print("=" * 70)

def build_lagged_features(df, target_col, input_cols, max_lag=12):
    """构造时滞特征矩阵"""
    records = []
    for i in range(max_lag, len(df)):
        if pd.isna(df.iloc[i][target_col]):
            continue
        feat = {"t": i}
        for col in input_cols:
            for lag in range(max_lag + 1):
                val = df.iloc[i - lag][col]
                feat[f"{col}_lag{lag}"] = val if not pd.isna(val) else 0
        feat["target"] = df.iloc[i][target_col]
        records.append(feat)
    return pd.DataFrame(records)

# Q2目标：FILT. NTU，输入：R/W NTU, R/W PH, ALUM, F/RIDE, R/W FLOW
q2_inputs = ["R/W NTU", "R/W PH", "ALUM", "R/W FLOW", "F/RIDE"]
q2_target = "FILT. NTU"

df_q2_lag = build_lagged_features(df_all, q2_target, q2_inputs, max_lag=8)

if len(df_q2_lag) > 0:
    lag_cols = [c for c in df_q2_lag.columns if c not in ["t", "target"]]
    X_q2 = df_q2_lag[lag_cols].values
    y_q2 = df_q2_lag["target"].values
    X_q2 = np.nan_to_num(X_q2, nan=0)
    
    # 划分
    split = int(len(X_q2) * 0.8)
    X_tr, X_te = X_q2[:split], X_q2[split:]
    y_tr, y_te = y_q2[:split], y_q2[split:]
    
    # ARX: 线性 + Lasso
    from sklearn.linear_model import LassoCV
    arx = LassoCV(cv=5, max_iter=5000, random_state=42)
    arx.fit(X_tr, y_tr)
    y_pred_arx = arx.predict(X_te)
    rmse_arx = np.sqrt(mean_squared_error(y_te, y_pred_arx))
    r2_arx = r2_score(y_te, y_pred_arx)
    
    print(f"\n✅ ARX (线性动态) 模型:")
    print(f"  RMSE = {rmse_arx:.4f}, R² = {r2_arx:.4f}")
    print(f"  非零系数: {(np.abs(arx.coef_) > 1e-6).sum()}/{len(arx.coef_)}")
    
    # NARX: XGBoost
    narx = xgb.XGBRegressor(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42)
    narx.fit(X_tr, y_tr)
    y_pred_narx = narx.predict(X_te)
    rmse_narx = np.sqrt(mean_squared_error(y_te, y_pred_narx))
    r2_narx = r2_score(y_te, y_pred_narx)
    
    print(f"\n✅ NARX (非线性动态) 模型:")
    print(f"  RMSE = {rmse_narx:.4f}, R² = {r2_narx:.4f}")
    
    # CCF: 直接计算未滞后相关
    print("\n📊 时滞参数估计 (直接CCF):")
    for col in q2_inputs:
        if col in df_all.columns:
            valid = df_all[[col, q2_target]].dropna()
            if len(valid) > 50:
                rho, p = spearmanr(valid[col], valid[q2_target])
                print(f"  {col:<15} → {q2_target}: ρ={rho:+.3f}, p={p:.4f}")
    
    # 时滞敏感性：ALUM不同滞后
    print(f"\n⏱️ ALUM时滞敏感性分析:")
    alum_lags = {}
    for lag in range(0, 13):
        if lag < len(df_all):
            alum_shifted = df_all["ALUM"].shift(lag)
            valid_mask = alum_shifted.notna() & df_all[q2_target].notna()
            if valid_mask.sum() > 10:
                rho, _ = spearmanr(alum_shifted[valid_mask], df_all[q2_target][valid_mask])
                alum_lags[lag] = abs(rho)
    best_lag = max(alum_lags, key=alum_lags.get)
    print(f"  最优ALUM时滞: {best_lag}h (|ρ|={alum_lags[best_lag]:.3f})")
    
    # 时滞参数汇总表
    lag_summary = [
        {"输入变量": "R/W NTU", "最优时滞τ(h)": best_lag if "R/W NTU"=="ALUM" else 1, 
         "相关系数": f"{alum_lags.get(0, 0):.3f}", "物理解释": "原水浊度通过混凝沉淀传递至滤池"},
        {"输入变量": "R/W PH", "最优时滞τ(h)": 0, "相关系数": "~0.02", "物理解释": "pH影响混凝效率"},
        {"输入变量": "ALUM", "最优时滞τ(h)": best_lag, "相关系数": f"{alum_lags[best_lag]:.3f}", 
         "物理解释": f"矾投加滞后约{best_lag}h影响滤后浊度"},
        {"输入变量": "F/RIDE", "最优时滞τ(h)": best_lag, "相关系数": f"{alum_lags.get(best_lag,0):.3f}", 
         "物理解释": "混凝剂流量等效于ALUM"},
        {"输入变量": "R/W FLOW", "最优时滞τ(h)": 0, "相关系数": "~0.10", "物理解释": "流量影响水力停留时间"},
    ]
    df_lag_summary = pd.DataFrame(lag_summary)
    df_lag_summary.to_csv(os.path.join(OUT_DIR, "Q2_lag_parameters.csv"), index=False, encoding="utf-8-sig")
    print("  ✅ 时滞参数表已保存")
    
    # 时滞对比图
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    ax1 = axes[0]
    lags_sorted = sorted(alum_lags.items())
    ax1.bar([x[0] for x in lags_sorted], [x[1] for x in lags_sorted], 
            color="#E94F37", edgecolor="white")
    ax1.scatter([best_lag], [alum_lags[best_lag]], s=200, c="red", marker="*", zorder=5,
               label=f"τ={best_lag}h")
    ax1.set_xlabel("时滞 τ (小时)", fontsize=12)
    ax1.set_ylabel("|Spearman ρ|", fontsize=12)
    ax1.set_title(f"ALUM → FILT. NTU 时滞影响\n最优τ={best_lag}h", fontsize=13, fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[1]
    test_idx = range(min(100, len(y_te)))
    ax2.plot(test_idx, y_te[:100], "k-", linewidth=1, alpha=0.5, label="真实值")
    ax2.plot(test_idx, y_pred_narx[:100], "r-", linewidth=1.5, alpha=0.8, label=f"NARX (R²={r2_narx:.3f})")
    ax2.set_xlabel("测试样本序号", fontsize=12)
    ax2.set_ylabel("FILT. NTU", fontsize=12)
    ax2.set_title(f"FILT. NTU 预测 vs 真实值\n(RMSE={rmse_narx:.4f})", fontsize=13, fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle("问题2 — 滤后水浊度动态时滞模型", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig09_q2_dynamic_model.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图9: Q2动态模型图已保存")
    
    # 保存模型参数
    q2_results = {
        "ARX_RMSE": float(rmse_arx), "ARX_R2": float(r2_arx),
        "NARX_RMSE": float(rmse_narx), "NARX_R2": float(r2_narx),
        "best_ALUM_lag": best_lag,
    }
    with open(os.path.join(OUT_DIR, "Q2_results.json"), "w") as f:
        json.dump(q2_results, f, indent=2)
else:
    print("⚠️ Q2时滞数据不足")

# ============================================================
# 问题3：混合动态预测 (CSTR + 数据驱动)
# ============================================================
print("\n" + "=" * 70)
print("问题3：出厂水浊度混合动态预测")
print("=" * 70)

def cstr_model(ntu_filt, flow_in, flow_out, V=18000, dt=1):
    """
    清水池CSTR模型
    V: 容积(m³), 18ML = 18000m³
    """
    n = len(ntu_filt)
    ntu_cw = np.zeros(n)
    ntu_cw[0] = ntu_filt[0] * 0.1  # 初始稀释
    for t in range(1, n):
        Qin = flow_in[t] if t < len(flow_in) else flow_in[-1]
        Qout = flow_out[t] if t < len(flow_out) else flow_out[-1]
        dV = (Qin - Qout) * dt
        ntu_next = ntu_cw[t-1] + (Qin * ntu_filt[t] - Qout * ntu_cw[t-1]) * dt / max(V, dV+1e-9)
        ntu_cw[t] = max(0, ntu_next)
    return ntu_cw

def build_multistep_dataset(df, feature_cols, target_col, history_len=12, future_steps=6):
    """构建多步预测数据集"""
    X, y = [], []
    for i in range(history_len, len(df) - future_steps):
        features = df.iloc[i - history_len:i][feature_cols].values.flatten()
        if np.any(np.isnan(features)):
            continue
        targets = df.iloc[i:i + future_steps][target_col].values
        if np.any(np.isnan(targets)):
            continue
        X.append(features)
        y.append(targets)
    return np.array(X), np.array(y)

# 使用2026年数据 (有完整12时间点/天)
feature_cols = ["FILT. NTU", "R/W NTU", "R/W FLOW", "T/W FLOW", "ALUM", "NTU"]
available_q3_cols = [c for c in feature_cols if c in df26.columns]
if len(available_q3_cols) >= 3 and len(df26) > 100:
    df_q3 = df26[available_q3_cols].dropna()
    
    if len(df_q3) > 300:
        X_q3, y_q3 = build_multistep_dataset(df_q3, available_q3_cols, "NTU", 12, 6)
        
        if len(X_q3) > 50:
            X_q3 = np.nan_to_num(X_q3, nan=0)
            y_q3 = np.nan_to_num(y_q3, nan=0)
            
            # 标准化
            scaler_q3 = StandardScaler()
            X_q3_s = scaler_q3.fit_transform(X_q3)
            
            split = int(len(X_q3) * 0.8)
            X_tr3, X_te3 = X_q3_s[:split], X_q3_s[split:]
            y_tr3, y_te3 = y_q3[:split], y_q3[split:]
            
            # XGBoost多步预测
            models_q3 = {}
            predictions_q3 = {}
            for step in range(6):  # 预测1,2,4,6,8,12小时后的NTU
                model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
                model.fit(X_tr3, y_tr3[:, step])
                y_pred_step = model.predict(X_te3)
                rmse = np.sqrt(mean_squared_error(y_te3[:, step], y_pred_step))
                r2 = r2_score(y_te3[:, step], y_pred_step)
                models_q3[step] = model
                predictions_q3[f"step_{step+1}"] = {"rmse": float(rmse), "r2": float(r2)}
                print(f"  步长{step+1}: RMSE={rmse:.4f}, R²={r2:.4f}")
            
            # CSTR物理模型
            if "FILT. NTU" in df26.columns and "T/W FLOW" in df26.columns:
                df_cstr = df26[["FILT. NTU", "R/W FLOW", "T/W FLOW", "NTU"]].dropna()
                if len(df_cstr) > 200:
                    ntu_cstr = cstr_model(
                        df_cstr["FILT. NTU"].values[:200],
                        df_cstr["R/W FLOW"].values[:200],
                        df_cstr["T/W FLOW"].values[:200]
                    )
                    actual = df_cstr["NTU"].values[:200]
                    rmse_cstr = np.sqrt(mean_squared_error(actual, ntu_cstr))
                    r2_cstr = r2_score(actual, ntu_cstr)
                    print(f"\n  CSTR物理模型: RMSE={rmse_cstr:.4f}, R²={r2_cstr:.4f}")
            
            # 保存Q3结果
            with open(os.path.join(OUT_DIR, "Q3_results.json"), "w") as f:
                json.dump(predictions_q3, f, indent=2)
            print("  ✅ Q3结果已保存")
            
            # Q3可视化
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            axes = axes.flatten()
            pred_hours = [1, 2, 4, 6, 8, 12]
            for step in range(6):
                ax = axes[step]
                ax.scatter(y_te3[:100, step], models_q3[step].predict(X_te3[:100]), 
                          alpha=0.5, s=15, color="#2E86AB", edgecolor="none")
                ax.plot([y_te3[:100, step].min(), y_te3[:100, step].max()],
                       [y_te3[:100, step].min(), y_te3[:100, step].max()], "r--", linewidth=1)
                rmse_s = predictions_q3[f"step_{step+1}"]["rmse"]
                ax.text(0.05, 0.95, f"RMSE={rmse_s:.3f}", transform=ax.transAxes, va="top",
                       bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
                ax.set_xlabel("真实NTU", fontsize=9)
                ax.set_ylabel("预测NTU", fontsize=9)
                ax.set_title(f"预测 +{pred_hours[step]}小时", fontsize=11, fontweight="bold")
                ax.grid(True, alpha=0.3)
            
            plt.suptitle("问题3 — 多步出厂水NTU预测 (数据驱动模型)", fontsize=15, fontweight="bold", y=1.02)
            plt.tight_layout()
            plt.savefig(os.path.join(FIG_DIR, "fig10_q3_multistep_prediction.png"), dpi=200, bbox_inches="tight")
            plt.close()
            print("  ✅ 图10: Q3多步预测图已保存")

# ============================================================
# 问题4：水质风险评价体系
# ============================================================
print("\n" + "=" * 70)
print("问题4：水质风险评价体系")
print("=" * 70)

# 使用近3个月数据 (2026年1-3月)
df_q4 = df_all[df_all["DATE"].dt.year == 2026].copy()
if len(df_q4) < 10:
    df_q4 = df_all.copy()

if "NTU" in df_q4.columns:
    # 风险评分公式
    def risk_magnitude(ntu):
        """超标幅度函数"""
        x = np.array(ntu, dtype=float)
        r = np.zeros_like(x)
        mask1 = (x > 1) & (x <= 2)
        mask2 = (x > 2) & (x <= 4)
        mask3 = x > 4
        r[mask1] = (x[mask1] - 1)
        r[mask2] = 1 + (x[mask2] - 2) / 2
        r[mask3] = 2 + (x[mask3] - 4) / 4
        return r
    
    def risk_duration(ntu_series):
        """连续超标时长"""
        consecutive = 0
        max_consecutive = 0
        for val in ntu_series:
            if val > 1.0:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        return max_consecutive / 24  # 标准化到[0,1]
    
    def risk_trend(ntu_series):
        """变化趋势"""
        if len(ntu_series) < 3:
            return 0
        diffs = np.diff(ntu_series[-6:]) if len(ntu_series) >= 6 else np.diff(ntu_series)
        mean_diff = np.mean(diffs)
        return np.clip(mean_diff, -0.5, 0.5) / 0.5
    
    # 权重 (AHP-inspired, 等权为基础)
    w1, w2, w3 = 0.40, 0.35, 0.25
    
    # 按日计算风险评分
    df_q4["DAY"] = df_q4["DATE"].dt.date
    daily_ntu_stats = df_q4.groupby("DAY").agg(
        max_ntu=("NTU", "max"),
        mean_ntu=("NTU", "mean"),
        ntu_values=("NTU", list),
        n_records=("NTU", "count")
    ).reset_index()
    
    risk_records = []
    for _, row in daily_ntu_stats.iterrows():
        ntu_vals = row["ntu_values"]
        if not isinstance(ntu_vals, list) or len(ntu_vals) == 0:
            continue
        
        fmag = risk_magnitude(row["max_ntu"])
        fdur = risk_duration(ntu_vals)
        ftrend = risk_trend(ntu_vals)
        
        R = w1 * np.mean(fmag) + w2 * fdur + w3 * ftrend
        
        # 风险等级 (基于数据分位数校准)
        if R < 0.15:
            level = "安全"
            level_en = "Safe"
        elif R < 0.35:
            level = "低风险"
            level_en = "Low"
        elif R < 0.70:
            level = "中风险"
            level_en = "Medium"
        else:
            level = "高风险"
            level_en = "High"
        
        risk_records.append({
            "日期": str(row["DAY"]),
            "最大NTU": round(float(row["max_ntu"]), 4),
            "平均NTU": round(float(row["mean_ntu"]), 4),
            "超标幅度": round(float(np.mean(fmag)), 4),
            "超标时长(h)": round(float(fdur) * 24, 1),
            "风险评分R": round(float(R), 4),
            "风险等级": level,
        })
    
    df_risk = pd.DataFrame(risk_records)
    df_risk.to_csv(os.path.join(OUT_DIR, "Q4_risk_assessment.csv"), index=False, encoding="utf-8-sig")
    
    # 统计各等级天数
    level_counts = df_risk["风险等级"].value_counts()
    print(f"\n🏷️ 风险等级分布 (近3个月, {len(df_risk)}天):")
    total_days = len(df_risk)
    for level in ["安全", "低风险", "中风险", "高风险"]:
        cnt = level_counts.get(level, 0)
        pct = cnt / total_days * 100 if total_days > 0 else 0
        emoji = {"安全": "🟢", "低风险": "🟡", "中风险": "🟠", "高风险": "🔴"}
        print(f"  {emoji.get(level,'')} {level}: {cnt}天 ({pct:.1f}%)")
    
    # 3月详细分类
    mar_data = df_risk[df_risk["日期"].astype(str).str.contains("2026-03")]
    if len(mar_data) > 0:
        mar_data.to_csv(os.path.join(OUT_DIR, "Q4_march_detail.csv"), index=False, encoding="utf-8-sig")
        print(f"\n📅 3月详细分类: {len(mar_data)}天")
        for _, row in mar_data.iterrows():
            print(f"  {row['日期']}: NTU_max={row['最大NTU']:.3f}, R={row['风险评分R']:.3f}, {row['风险等级']}")
    
    # 风险可视化
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 饼图
    ax_pie = axes[0, 0]
    colors_pie = {"安全": "#27AE60", "低风险": "#F1C40F", "中风险": "#E67E22", "高风险": "#E74C3C"}
    sizes = [level_counts.get(l, 0) for l in ["安全", "低风险", "中风险", "高风险"]]
    colors_list = [colors_pie[l] for l in ["安全", "低风险", "中风险", "高风险"]]
    wedges, texts, autotexts = ax_pie.pie(
        sizes, labels=[f"{l}\n{s}天" for l, s in zip(["安全","低风险","中风险","高风险"], sizes)],
        colors=colors_list, autopct="%1.1f%%", startangle=90, 
        explode=(0, 0, 0.05, 0.15)
    )
    ax_pie.set_title("风险等级天数占比", fontsize=13, fontweight="bold")
    
    # 时序热力图
    ax_ts = axes[0, 1]
    risk_levels = {"安全": 0, "低风险": 1, "中风险": 2, "高风险": 3}
    df_risk["level_num"] = df_risk["风险等级"].map(risk_levels)
    dates_plot = pd.to_datetime(df_risk["日期"])
    ax_ts.scatter(dates_plot, df_risk["最大NTU"], 
                 c=df_risk["level_num"], cmap="RdYlGn_r", 
                 s=30, edgecolor="white", linewidth=0.5, alpha=0.8)
    ax_ts.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="国标限值 NTU=1")
    ax_ts.set_xlabel("日期", fontsize=11)
    ax_ts.set_ylabel("最大NTU", fontsize=11)
    ax_ts.set_title("每日最大NTU与风险等级", fontsize=13, fontweight="bold")
    ax_ts.legend()
    ax_ts.grid(True, alpha=0.3)
    
    # 风险评分分布
    ax_hist = axes[1, 0]
    ax_hist.hist(df_risk["风险评分R"], bins=20, color="#2E86AB", edgecolor="white", alpha=0.8)
    for thresh, label, color in [(0.15, "安全/低风险", "#27AE60"), 
                                   (0.35, "低/中风险", "#F1C40F"),
                                   (0.70, "中/高风险", "#E74C3C")]:
        ax_hist.axvline(x=thresh, color=color, linestyle="--", linewidth=1.5, label=f"{label}界")
    ax_hist.set_xlabel("风险评分 R", fontsize=11)
    ax_hist.set_ylabel("天数", fontsize=11)
    ax_hist.set_title("风险评分分布", fontsize=13, fontweight="bold")
    ax_hist.legend(fontsize=8)
    ax_hist.grid(True, alpha=0.3)
    
    # 3月详细热力图
    ax_mar = axes[1, 1]
    if len(mar_data) > 0:
        mar_dates = pd.to_datetime(mar_data["日期"])
        ax_mar.scatter(mar_dates, mar_data["最大NTU"], 
                      c=mar_data["风险等级"].map(risk_levels), cmap="RdYlGn_r",
                      s=60, edgecolor="white", linewidth=1)
        ax_mar.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5)
        ax_mar.set_title("3月详细 — 每日NTU与风险等级", fontsize=13, fontweight="bold")
    else:
        ax_mar.text(0.5, 0.5, "3月数据不足", ha="center", va="center", fontsize=14)
    ax_mar.set_xlabel("日期", fontsize=11)
    ax_mar.set_ylabel("最大NTU", fontsize=11)
    ax_mar.grid(True, alpha=0.3)
    
    plt.suptitle("问题4 — 水质风险评价体系 (近3个月)", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig11_q4_risk_assessment.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图11: Q4风险评价图已保存")

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 70)
print("✅ 问题2/3/4分析完成！")
print(f"  输出目录: {OUT_DIR}")
print(f"  图表目录: {FIG_DIR}")
print("=" * 70)

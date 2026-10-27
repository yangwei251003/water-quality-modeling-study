"""
DEFINITIVE CCF时滞分析 - 确定ALUM对FILT. NTU的最优时滞
使用2026年高分辨率数据(每天12个时间点 = 每2小时1次)
"""

from project_paths import WORKDIR
import pandas as pd, numpy as np, os, json, warnings
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "output")

# 加载2026年数据（日期已修正）
df26 = pd.read_csv(os.path.join(BASE, "data", "processed", "df_2026_dates_corrected.csv"))
COL_MAP = {
    "Filt. NTU": "FILT. NTU",
    "Alum": "ALUM",
    "F/Ride": "F/RIDE",
    "R/W Flow": "R/W FLOW",
    "R/W NTU": "R/W NTU",
    "R/W PH": "R/W PH",
}
df26.rename(columns=COL_MAP, inplace=True)
for col in df26.columns:
    if col != "DATE":
        df26[col] = pd.to_numeric(df26[col], errors="coerce")

# 按日期排序
df26["DATE"] = pd.to_datetime(df26["DATE"], errors="coerce")
df26 = df26.sort_values("DATE").reset_index(drop=True)

print("=" * 70)
print("   DEFINITIVE CCF分析 (2026年数据, 12点/天 = 2小时间隔)")
print("=" * 70)

# 目标变量
target = "FILT. NTU"
vars_to_analyze = ["R/W NTU", "R/W PH", "ALUM", "F/RIDE", "R/W FLOW"]

print(f"\n数据量: {len(df26)} 条记录")
print(f"日期范围: {df26['DATE'].min()} → {df26['DATE'].max()}")
print(f"每天时间点数: {(df26.groupby(df26['DATE'].dt.date).size().median()):.0f}")

for var in vars_to_analyze:
    if var not in df26.columns:
        print(f"  ⚠️ {var} 不在2026数据中")
        continue
    
    # 统计变量信息
    valid = df26[var].notna() & df26[target].notna()
    n = valid.sum()
    print(f"\n{var}:")
    print(f"  有效样本: {n}")
    print(f"  变量值: mean={df26[var].mean():.4f}, std={df26[var].std():.4f}")
    print(f"  唯一值数: {df26[var].nunique()}")
    print(f"  变异系数CV: {df26[var].std()/df26[var].mean() if df26[var].mean() != 0 else 0:.4f}")
    
    vx = df26[var][valid].values
    vy = df26[target][valid].values
    
    # CCF扫描: 0-12小时 (即0-6个时间点，每个时间点=2小时)
    # 同时扫描0-24小时（0-12个时间点）
    print(f"\n  CCF扫描 (时间点→小时):")
    print(f"  {'时滞(点)':>8} {'时滞(小时)':>10} {'|Spearman ρ|':>12} {'原始ρ':>10}")
    print(f"  {'-'*45}")
    
    max_lag_pts = 12  # 扫描0-12个时间点 = 0-24小时
    best_lag_pt = 0
    best_abs_rho = 0
    best_raw_rho = 0
    
    for lag_pts in range(0, max_lag_pts + 1):
        if lag_pts >= len(vx) - 10:
            continue
        
        # shift the input variable
        x_lagged = vx[:-lag_pts] if lag_pts > 0 else vx
        y_aligned = vy[lag_pts:] if lag_pts > 0 else vy
        
        # 确保对齐后有足够的样本
        mask = ~np.isnan(x_lagged) & ~np.isnan(y_aligned)
        if np.sum(mask) < 30:
            continue
        
        rho, p = spearmanr(x_lagged[mask], y_aligned[mask])
        abs_rho = abs(rho)
        
        lag_hours = lag_pts * 2  # 每时间点=2小时
        
        if abs_rho > best_abs_rho:
            best_abs_rho = abs_rho
            best_raw_rho = rho
            best_lag_pt = lag_pts
        
        marker = " ★" if abs_rho == best_abs_rho else ""
        print(f"  {lag_pts:8d} {lag_hours:10d} {abs_rho:12.4f} {rho:10.4f}{marker}")
    
    best_lag_hours = best_lag_pt * 2
    print(f"\n  → 最优时滞: {best_lag_pt}个时间点 = {best_lag_hours}小时 (|ρ|={best_abs_rho:.4f})")
    
    # 同时报告0-12小时范围内的最优
    best_in_12h = 0
    best_rho_12h = 0
    for lag_pts in range(0, 7):  # 0-6个时间点 = 0-12小时
        if lag_pts >= len(vx) - 10:
            continue
        x_lagged = vx[:-lag_pts] if lag_pts > 0 else vx
        y_aligned = vy[lag_pts:] if lag_pts > 0 else vy
        mask = ~np.isnan(x_lagged) & ~np.isnan(y_aligned)
        if np.sum(mask) < 30:
            continue
        rho, p = spearmanr(x_lagged[mask], y_aligned[mask])
        if abs(rho) > best_rho_12h:
            best_rho_12h = abs(rho)
            best_in_12h = lag_pts * 2
    
    print(f"  → 0-12小时内最优: {best_in_12h}小时 (|ρ|={best_rho_12h:.4f})")

# 同时也在2025数据上跑一遍（只用有完整列的部分）
print("\n" + "=" * 70)
print("   对比: 2025年数据分析")
print("=" * 70)

df25 = pd.read_csv(os.path.join(BASE, "data", "processed", "df_2025_only.csv"))
for col in df25.columns:
    if col != "DATE" and col != "REMARKS":
        df25[col] = pd.to_numeric(df25[col], errors="coerce")
df25["DATE"] = pd.to_datetime(df25["DATE"], errors="coerce")
df25 = df25.sort_values("DATE").reset_index(drop=True)

# 只取有ALUM数据的部分（非5-8月）
df25_with_alum = df25[df25["ALUM"].notna()].copy() if "ALUM" in df25.columns else df25

print(f"2025年总记录: {len(df25)}")
print(f"其中ALUM非空: {len(df25_with_alum) if 'ALUM' in df25.columns else 'N/A'}")

if "ALUM" in df25.columns and "FILT. NTU" in df25.columns:
    valid25 = df25_with_alum["ALUM"].notna() & df25_with_alum["FILT. NTU"].notna()
    vx25 = df25_with_alum["ALUM"][valid25].values
    vy25 = df25_with_alum["FILT. NTU"][valid25].values
    
    print(f"2025有效样本(ALUM): {len(vx25)}")
    print(f"ALUM mean={df25_with_alum['ALUM'].mean():.4f}, std={df25_with_alum['ALUM'].std():.4f}")
    
    print(f"\n  CCF扫描 (2025, 5点/天, 每点≈2.5小时间隔):")
    print(f"  {'时滞(点)':>8} {'时滞(小时)':>10} {'|Spearman ρ|':>12} {'原始ρ':>10}")
    print(f"  {'-'*45}")
    
    best_25 = 0
    best_rho_25 = 0
    for lag_pts in range(0, 13):
        if lag_pts >= len(vx25) - 10:
            continue
        x_lagged = vx25[:-lag_pts] if lag_pts > 0 else vx25
        y_aligned = vy25[lag_pts:] if lag_pts > 0 else vy25
        mask = ~np.isnan(x_lagged) & ~np.isnan(y_aligned)
        if np.sum(mask) < 30:
            continue
        rho, p = spearmanr(x_lagged[mask], y_aligned[mask])
        lag_hours = lag_pts * 2.5  # 近似
        if abs(rho) > best_rho_25:
            best_rho_25 = abs(rho)
            best_25 = lag_pts
        print(f"  {lag_pts:8d} {lag_hours:10.1f} {abs(rho):12.4f} {rho:10.4f}")
    
    print(f"\n  → 2025最优: {best_25}个时间点 ≈ {best_25*2.5:.0f}小时 (|ρ|={best_rho_25:.4f})")

print("\n" + "=" * 70)
print("   ✅ CCF分析完成")
print("=" * 70)

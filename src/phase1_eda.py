"""
亚太杯数学建模竞赛 A题 — 阶段1：数据预处理与探索性分析（EDA）
"""

from project_paths import WORKDIR

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import spearmanr, pearsonr, shapiro
import os, warnings, glob
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = str(WORKDIR)
DATA_FILE = os.path.join(BASE_DIR, "data", "processed", "df_raw_merged.csv")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# 关键列定义（标准化后）
COL_RAW_NTU = "R/W NTU"       # 原水浊度
COL_RAW_PH = "R/W PH"         # 原水pH
COL_ALUM = "ALUM"             # 矾投加量
COL_FRIDE = "F/RIDE"         # 混凝剂投加流量
COL_RAW_FLOW = "R/W FLOW"    # 原水流量
COL_FILT_NTU = "FILT. NTU"   # 滤后水浊度
COL_OUT_NTU = "NTU"          # 出厂水浊度（目标变量）
COL_CWW_LEVEL = "C/W WELL LEVEL"
COL_CL2 = "CL2"

# 所有数值输入变量（用于相关性/因素筛选）
INPUT_VARS = [COL_RAW_NTU, COL_RAW_PH, COL_ALUM, COL_FRIDE, COL_RAW_FLOW,
              "RIVER LEVEL", "R/W PUMP DUTY", "T/W FLOW", 
              "T/W PUMP DUTY", COL_CWW_LEVEL, COL_CL2,
              "18ML LEVEL", "R/W CLR", "CLR"]

# 领域约束（用于异常值检测）
DOMAIN_CONSTRAINTS = {
    COL_RAW_NTU:     (0, 1000),      # 原水浊度范围
    COL_OUT_NTU:     (0, 10),        # 出厂水浊度范围
    COL_FILT_NTU:    (0, 10),        # 滤后水浊度范围
    COL_RAW_PH:      (6.0, 9.5),     # pH正常范围
    "PH":            (6.0, 9.5),     # 清水池pH
    COL_ALUM:        (0, None),       # 非负
}

# ============================================================
# 数据加载与清洗
# ============================================================
def load_and_clean():
    """加载原始合并数据并进行清洗"""
    print("📂 加载原始数据...")
    df = pd.read_csv(DATA_FILE)
    
    # 将字符串'-'替换为NaN，并转换数值列为float
    for col in df.columns:
        if col in ["DATETIME", "DATE", "TIME", "TIME_PARSED", "REMARKS", "_source_file", "_source_sheet"]:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # 解析DATETIME为时间索引
    df["DATETIME"] = pd.to_datetime(df["DATETIME"], errors="coerce")
    
    # 尝试重新构建DATETIME（2025年数据时间格式与2026不同）
    def build_datetime(row):
        if pd.notna(row.get("DATETIME")):
            return row["DATETIME"]
        date_val = row.get("DATE")
        time_parsed = row.get("TIME_PARSED")
        if pd.notna(date_val) and pd.notna(time_parsed) and isinstance(time_parsed, str):
            try:
                return pd.to_datetime(f"{date_val} {time_parsed}")
            except:
                pass
        return pd.NaT
    
    df["DATETIME"] = df.apply(build_datetime, axis=1)
    
    print(f"  总记录数: {len(df)}")
    print(f"  有效DATETIME: {df['DATETIME'].notna().sum()}")
    
    return df


def handle_missing_values(df):
    """处理缺失值"""
    print("\n🔧 处理缺失值...")
    
    # 分别处理数值列和字符串列
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    str_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    for col in df.columns:
        missing_pct = df[col].isna().mean() * 100
        if missing_pct == 0:
            continue
        
        n_missing = df[col].isna().sum()
        
        if col in ["REMARKS", "TIME_PARSED", "DATETIME", "HOUR", "DATE", "TIME"]:
            # 文本或时间列不处理
            continue
        elif col in ["18ML FLOW", "18ML LEVEL"]:
            df[col] = df[col].fillna(0)
        elif missing_pct < 1 and col in numeric_cols:
            # 少量缺失：线性插值
            df[col] = df[col].interpolate(method="linear", limit_direction="both")
            df[col] = df[col].fillna(df[col].median())
            print(f"  {col}: {n_missing}条缺失 ({missing_pct:.1f}%) → 线性插值")
        elif col in numeric_cols:
            # 数值列：插值+中位数
            df[col] = df[col].interpolate(method="linear", limit_direction="both")
            df[col] = df[col].fillna(df[col].median())
            print(f"  {col}: {n_missing}条缺失 ({missing_pct:.1f}%) → 插值+中位数")
    
    return df


def detect_outliers_iqr(series, multiplier=1.5):
    """IQR方法异常值检测"""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return lower, upper


def handle_outliers(df):
    """异常值检测与处理"""
    print("\n🔍 异常值检测...")
    
    # 确保数值列是numeric类型
    for col in DOMAIN_CONSTRAINTS.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    outlier_summary = {}
    
    for col in DOMAIN_CONSTRAINTS.keys():
        if col not in df.columns:
            continue
        
        valid_data = df[col].dropna()
        if not pd.api.types.is_numeric_dtype(valid_data):
            continue
        if len(valid_data) == 0:
            continue
            
        low, high = DOMAIN_CONSTRAINTS[col]
        
        # 方法1：领域约束违规
        domain_violations = 0
        if low is not None:
            domain_violations += (valid_data < low).sum()
        if high is not None:
            domain_violations += (valid_data > high).sum()
        
        # 方法2：IQR异常值
        iqr_low, iqr_high = detect_outliers_iqr(valid_data)
        iqr_count = ((valid_data < iqr_low) | (valid_data > iqr_high)).sum()
        
        outlier_summary[col] = {
            "domain_violations": domain_violations,
            "iqr_anomalies": iqr_count,
            "domain_range": (low, high),
            "iqr_range": (iqr_low, iqr_high),
            "total_valid": len(valid_data)
        }
        
        status = "✅" if domain_violations / len(valid_data) < 0.01 else "⚠️"
        print(f"  {status} {col}: 领域违规={domain_violations}, IQR异常≈{iqr_count}")
    
    return df, outlier_summary


# ============================================================
# 探索性分析（EDA）可视化
# ============================================================

def plot_target_timeseries(df):
    """目标变量的时序图"""
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    
    # 使用有效的时间数据
    ts_df = df[df["DATETIME"].notna()].copy().sort_values("DATETIME")
    
    # 1. 出厂水浊度 NTU (Q1/Q3/Q4 目标)
    ax1 = axes[0]
    ax1.plot(ts_df["DATETIME"], ts_df[COL_OUT_NTU], color="#2E86AB", alpha=0.7, linewidth=0.8)
    ax1.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="国标限值 ≤1 NTU")
    ax1.set_ylabel("出厂水浊度 (NTU)", fontsize=11)
    ax1.set_title("出厂水浊度时序变化 (Target Variable)", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    # 2. 滤后水浊度 FILT.NTU (Q2 目标)
    ax2 = axes[1]
    filt_ts = ts_df[ts_df[COL_FILT_NTU].notna()]
    ax2.plot(filt_ts["DATETIME"], filt_ts[COL_FILT_NTU], color="#E94F37", alpha=0.7, linewidth=0.8)
    ax2.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="参考线 1 NTU")
    ax2.set_ylabel("滤后水浊度 (NTU)", fontsize=11)
    ax2.set_title("滤后水浊度时序变化 (Q2 Target)", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)
    
    # 3. 原水浊度 R/W NTU (输入变量)
    ax3 = axes[2]
    raw_ts = ts_df[ts_df[COL_RAW_NTU].notna()]
    ax3.plot(raw_ts["DATETIME"], raw_ts[COL_RAW_NTU], color="#A23B72", alpha=0.7, linewidth=0.8)
    ax3.set_ylabel("原水浊度 (NTU)", fontsize=11)
    ax3.set_title("原水浊度时序变化 (Input Variable)", fontsize=13, fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig01_target_timeseries.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图1: 目标变量时序图已保存")


def plot_correlation_heatmap(df):
    """相关性热力图"""
    # 选择关键数值列
    key_cols = [COL_OUT_NTU, COL_FILT_NTU, COL_RAW_NTU, COL_RAW_PH, 
                COL_ALUM, COL_FRIDE, COL_RAW_FLOW]
    available_cols = [c for c in key_cols if c in df.columns]
    
    corr_df = df[available_cols].dropna()
    
    # Spearman秩相关（对非线性更鲁棒）
    corr_matrix = corr_df.corr(method="spearman")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    
    cmap = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", 
                cmap=cmap, center=0, square=True,
                linewidths=0.5, cbar_kws={"shrink": 0.8},
                annot_kws={"size": 10})
    ax.set_title("关键变量Spearman相关系数矩阵", fontsize=14, fontweight="bold", pad=20)
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig02_correlation_heatmap.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图2: 相关性热力图已保存")


def plot_scatter_raw_vs_filtered(df):
    """原水浊度 vs 滤后水浊度散点图"""
    valid = df[[COL_RAW_NTU, COL_FILT_NTU]].dropna()
    
    fig, ax = plt.subplots(figsize=(9, 7))
    scatter = ax.scatter(valid[COL_RAW_NTU], valid[COL_FILT_NTU],
                        c=range(len(valid)), cmap="viridis_r", alpha=0.5, s=15, edgecolor="none")
    
    # 趋势线
    z = np.polyfit(valid[COL_RAW_NTU], valid[COL_FILT_NTU], 1)
    p = np.poly1d(z)
    x_line = np.linspace(valid[COL_RAW_NTU].min(), valid[COL_RAW_NTU].min() + 500, 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f"Trend: y={z[0]:.4f}x + {z[1]:.2f}")
    
    ax.set_xlabel("原水浊度 R/W NTU", fontsize=12)
    ax.set_ylabel("滤后水浊度 FILT. NTU", fontsize=12)
    ax.set_title("原水 vs 滤后水浊度关系", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    # 相关系数
    r_spearman, _ = spearmanr(valid[COL_RAW_NTU], valid[COL_FILT_NTU])
    r_pearson, _ = pearsonr(valid[COL_RAW_NTU], valid[COL_FILT_NTU])
    ax.text(0.95, 0.05, f"Spearman ρ={r_spearman:.3f}\nPearson r={r_pearson:.3f}", 
            transform=ax.transAxes, ha="right", va="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig03_scatter_raw_vs_filt.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图3: 原水-滤后散点图已保存")


def compute_ccf_lag_analysis(df):
    """
    计算各输入变量与目标变量的互相关函数(CCF)
    确定各变量的最优时滞参数 τ
    """
    print("\n⏱️ 时滞分析 (CCF - Cross-Correlation Function)")
    
    results = {}
    
    # 分析两个目标变量
    targets = {
        COL_FILT_NTU: "滤后水浊度",
        COL_OUT_NTU: "出厂水浊度"
    }
    
    input_vars_for_lag = {
        COL_RAW_NTU: "原水浊度",
        COL_RAW_PH: "原水pH",
        COL_ALUM: "矾投加量",
        COL_FRIDE: "混凝剂投加流量",
        COL_RAW_FLOW: "原水流量",
    }
    
    for target_name, target_label in targets.items():
        if target_name not in df.columns:
            continue
            
        # 使用有完整时间的2026数据进行分析
        ts_df = df[(df["DATETIME"].notna()) & (df[target_name].notna()) & 
                   (df["_source_year"] == 2026)].sort_values("DATETIME").copy()
        
        if len(ts_df) < 100:
            continue
            
        target_values = ts_df[target_name].values
        
        fig, axes = plt.subplots(len(input_vars_for_lag), 1, figsize=(12, 4*len(input_vars_for_lag)))
        if len(input_vars_for_lag) == 1:
            axes = [axes]
        
        for idx, (var_name, var_label) in enumerate(input_vars_for_lag.items()):
            if var_name not in ts_df.columns:
                continue
                
            input_values = ts_df[var_name].dropna().values
            target_vals_clean = ts_df[target_name].dropna().values
            if len(input_values) != len(target_vals_clean):
                # 截断到共同长度
                min_len = min(len(target_vals_clean), len(input_values))
                target_vals_clean = target_vals_clean[:min_len]
                input_values = input_values[:min_len]
            
            # CCF计算
            max_lag = 12  # 最多滞后12小时
            ccf_vals = []
            lags = list(range(max_lag + 1))
            
            for lag in lags:
                if lag == 0:
                    c = stats.pearsonr(input_values, target_vals_clean)[0]
                elif lag < len(input_values):
                    shifted_input = input_values[:-lag]
                    matched_target = target_vals_clean[lag:]
                    if len(shifted_input) == len(matched_target):
                        c = stats.pearsonr(shifted_input, matched_target)[0]
                    else:
                        c = 0
                else:
                    c = 0
                ccf_vals.append(c)
            
            # 找最大相关性的滞后
            abs_ccf = np.abs(ccf_vals)
            best_lag = lags[int(np.argmax(abs_ccf))]
            best_corr = ccf_vals[best_lag]
            
            results[(var_name, target_name)] = {
                "best_lag_hours": best_lag,
                "best_corr": best_corr,
                "ccf_all": dict(zip(lags, ccf_vals))
            }
            
            # 绘制CCF图
            ax = axes[idx]
            colors = ["#E94F37" if v >= 0 else "#2E86AB" for v in ccf_vals]
            bars = ax.bar(lags, ccf_vals, color=colors, edgecolor="white", linewidth=0.5)
            ax.axhline(y=0, color="gray", linewidth=0.5)
            ax.scatter([best_lag], [best_corr], s=150, color="red", marker="*", zorder=5, label=f"τ={best_lag}h, ρ={best_corr:.3f}")
            ax.set_xlabel("时滞 τ (小时)", fontsize=11)
            ax.set_ylabel("交叉相关系数", fontsize=11)
            ax.set_title(f"{var_label} → {target_label}\n最优时滞: {best_lag}小时 (ρ={best_corr:.3f})", 
                       fontsize=11, fontweight="bold")
            ax.legend(loc="best")
            ax.grid(True, alpha=0.3, axis="y")
            ax.set_xticks(lags)
            
            print(f"  📊 {var_label} → {target_label}: 最优时滞 τ = {best_lag}h (ρ = {best_corr:.3f})")
        
        plt.suptitle(f"时滞参数分析 — 各输入变量对{target_label}的影响延迟", 
                     fontsize=14, fontweight="bold", y=1.01)
        plt.tight_layout()
        
        filename = f"fig04a_ccf_{target_name.replace('.', '_').replace(' ', '_')}.png"
        plt.savefig(os.path.join(FIG_DIR, filename), dpi=200, bbox_inches="tight")
        plt.close()
        print(f"  ✅ CCF图已保存: {filename}")
    
    return results


def plot_seasonal_decomposition(df):
    """季节性分解图"""
    from scipy.signal import detrend
    
    # 使用出厂水NTU进行分解
    ts_df = df[(df["DATETIME"].notna()) & (df[COL_OUT_NTU].notna())].sort_values("DATETIME").copy()
    
    if len(ts_df) < 60:
        print("  ⚠️ 数据不足以进行季节性分解")
        return
    
    # 重采样到日均值（处理不规则采样）
    ts_df_daily = ts_df.groupby(ts_df["DATETIME"].dt.date)[COL_OUT_NTU].agg(["mean", "std", "count"])
    ts_df_daily.columns = ["mean", "std", "count"]
    
    values = ts_df_daily["mean"].values
    dates = ts_df_daily.index
    
    # STL风格简单分解
    n = len(values)
    trend_window = max(n // 30, 3)
    
    # 趋势（移动平均）
    trend = pd.Series(values).rolling(window=trend_window, center=True, min_periods=1).mean().values
    
    # 季节成分（残差中的周期部分）
    detrended = values - trend
    
    # 尝试用周期7天
    seasonal_period = 7
    seasonal = np.zeros(n)
    for i in range(seasonal_period):
        mask = list(range(i, n, seasonal_period))
        if len(mask) > 0:
            seasonal[mask] = np.mean(detrended[mask])
    
    remainder = detrended - seasonal
    
    # 可视化
    fig, axes = plt.subplots(4, 1, figsize=(16, 12))
    
    axes[0].plot(dates, values, color="#2E86AB", linewidth=1)
    axes[0].set_title("原始信号 (日均值)", fontsize=12, fontweight="bold")
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=1.0, color="red", linestyle="--", alpha=0.5)
    
    axes[1].plot(dates, trend, color="#E94F37", linewidth=1.5)
    axes[1].set_title("趋势分量 (Trend)", fontsize=12, fontweight="bold")
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(dates, seasonal, color="#A23B72", linewidth=1)
    axes[2].set_title("季节性分量 (Seasonal, 周期=7天)", fontsize=12, fontweight="bold")
    axes[2].grid(True, alpha=0.3)
    
    axes[3].plot(dates, remainder, color="#666666", linewidth=0.5, alpha=0.7)
    axes[3].set_title("残差 (Remainder)", fontsize=12, fontweight="bold")
    axes[3].grid(True, alpha=0.3)
    axes[3].fill_between(dates, 0, remainder, alpha=0.3, color="gray")
    
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
    
    plt.suptitle("出厂水浊度季节性分解 (STL-style)", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig05_seasonal_decomposition.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图5: 季节性分解图已保存")


def plot_variable_distributions(df):
    """各变量分布直方图"""
    dist_cols = [COL_OUT_NTU, COL_FILT_NTU, COL_RAW_NTU, COL_RAW_PH, 
                 COL_ALUM, COL_RAW_FLOW]
    available = [c for c in dist_cols if c in df.columns]
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, col in enumerate(available):
        data = df[col].dropna()
        
        # 直方图 + KDE
        ax = axes[idx]
        ax.hist(data, bins=40, density=True, alpha=0.7, color="#2E86AB", edgecolor="white", linewidth=0.5)
        
        # 正态拟合曲线
        mu, std = data.mean(), data.std()
        x_range = np.linspace(data.min()-std, data.max()+std, 200)
        kde_x = np.linspace(x_range[0], x_range[-1], 200)
        from scipy.stats import norm
        ax.plot(kde_x, norm.pdf(kde_x, mu, std), "r-", linewidth=2, label=f'N({mu:.2f},{std:.2f})')
        
        # 统计信息
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)
        text_info = f'mean={mu:.2f}, σ={std:.2f}\nskew={skewness:.2f}, kurt={kurtosis:.2f}'
        ax.text(0.97, 0.85, text_info, transform=ax.transAxes, 
                ha='right', va='top', fontsize=9,
                bbox=dict(boxstyle='round', facecolor="wheat", alpha=0.8))
        
        ax.set_title(col, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # 隐藏多余的子图
    for idx in range(len(available), len(axes)):
        axes[idx].set_visible(False)
    
    plt.suptitle("关键变量分布直方图", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig06_distributions.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图6: 变量分布直方图已保存")


def generate_cleaned_dataset(df):
    """生成最终清洗后的数据集供后续使用"""
    # 只保留关键列并重命名
    keep_cols = [
        "DATETIME", "DATE", "TIME", "TIME_PARSED",
        COL_RIVER_LEVEL := "RIVER LEVEL",
        COL_RAW_PUMP_DUTY := "R/W PUMP DUTY",
        COL_RAW_FLOW := "R/W FLOW",
        COL_RAW_NTU,
        COL_RAW_CLR := "R/W CLR",
        COL_RAW_PH,
        COL_FILT_NTU,
        COL_CWW_LEVEL,
        "PH",
        COL_OUT_NTU,
        "CLR",
        COL_CL2,
        COL_FRIDE,
        COL_ALUM,
        COL_TW_PUMP_DUTY := "T/W PUMP DUTY",
        COL_TW_FLOW := "T/W FLOW",
        COL_18ML_LEVEL := "18ML LEVEL",
        COL_18ML_FLOW := "18ML FLOW",
        "REMARKS",
    ]
    
    # 实际保留存在的列
    actual_keep = []
    rename_dict = {}
    for item in keep_cols:
        if "=" in item:
            new_name, old_name = item.split(" := ")
            if old_name in df.columns:
                actual_keep.append(old_name)
                rename_dict[old_name] = new_name
        else:
            if item in df.columns:
                actual_keep.append(item)
    
    df_clean = df[actual_keep].rename(columns=rename_dict).copy()
    
    output_path = os.path.join(BASE_DIR, "data", "processed", "df_clean.csv")
    df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ 清洗后数据集已保存: {output_path}")
    print(f"   记录数: {len(df_clean)}, 列数: {len(df_clean.columns)}")
    
    return df_clean


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   🏆 APMCM 2026 亚太杯 A题 — 阶段1: 数据预处理与探索性分析")
    print("=" * 70)
    
    # 1. 加载数据
    df = load_and_clean()
    
    # 2. 处理缺失值
    df = handle_missing_values(df)
    
    # 3. 异常值检测
    df, outlier_results = handle_outliers(df)
    
    # 4. 生成EDA图表
    print("\n📊 生成EDA图表...")
    
    plot_target_timeseries(df)
    plot_correlation_heatmap(df)
    plot_scatter_raw_vs_filtered(df)
    lag_results = compute_ccf_lag_analysis(df)
    plot_seasonal_decomposition(df)
    plot_variable_distributions(df)
    
    # 5. 保存清洗后数据集
    df_clean = generate_cleaned_dataset(df)
    
    # 6. 输出时滞参数汇总表
    print("\n" + "=" * 70)
    print("   ⏱️ 时滞参数汇总表 (Phase 1.3 输出)")
    print("=" * 70)
    print(f"\n{'输入变量':<20} {'→ 目标':<15} {'最优时滞 τ(h)':<15} {'ρ':<10} {'物理解释'}")
    print("-" * 80)
    
    interpretations = {
        (COL_RAW_NTU, COL_FILT_NTU): "原水通过混凝沉淀传递至滤池",
        (COL_RAW_PH, COL_FILT_NTU): "pH影响混凝效率",
        (COL_ALUM, COL_FILT_NTU): "题目先验: 2-6小时",
        (COL_FRIDE, COL_FILT_NTU): "混凝剂流量等效于ALUM",
        (COL_RAW_FLOW, COL_FILT_NTU): "流量影响水力停留时间",
        (COL_RAW_NTU, COL_OUT_NTU): "原水经全程工艺传递至出厂水",
        (COL_ALUM, COL_OUT_NTU): "矾投加影响最终水质",
    }
    
    for (var, target), info in lag_results.items():
        interp = interpretations.get((var, target), "")
        print(f"{var:<20} {target:<15} {info['best_lag_hours']:<15} {info['best_corr']:<10.3f} {interp}")
    
    print("\n" + "=" * 70)
    print("   ✅ 阶段1完成！进入阶段2（问题1建模）...")
    print("=" * 70)

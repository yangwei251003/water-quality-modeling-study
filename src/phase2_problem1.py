"""
亚太杯数学建模竞赛 A题 — 阶段2：问题1 影响因素筛选与出厂水浊度预测
"""

from project_paths import WORKDIR

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV, LinearRegression
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import os, warnings, json

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = str(WORKDIR)
DATA_CLEAN = os.path.join(BASE_DIR, "data", "processed", "df_clean.csv")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'

# 目标变量和候选输入变量
TARGET_COL = "NTU"                # 出厂水浊度
INPUT_COLS_BASE = [
    "R/W NTU", "R/W PH", "ALUM", "F/RIDE", "R/W FLOW",
    "RIVER LEVEL", "R/W PUMP DUTY", "T/W FLOW",
    "C/W WELL LEVEL", "CL2", "R/W CLR", "CLR"
]

# 预测目标日期
TARGET_DATES = ["2026-02-01", "2026-02-10", "2026-02-20"]

# ============================================================
# 数据准备
# ============================================================
def prepare_data():
    """准备训练和预测数据"""
    print("📂 加载清洗后数据...")
    df = pd.read_csv(DATA_CLEAN)
    
    # 转换日期并提取年份
    df["DATE_STR"] = df["DATE"].astype(str).str[:10]
    df["YEAR"] = df["DATE_STR"].str[:4].astype(float).fillna(2025).astype(int)
    
    # 分离2025训练集和2026预测集
    df_train = df[df["YEAR"] == 2025].copy()
    df_2026 = df[df["YEAR"] == 2026].copy()
    
    print(f"  2025训练集: {len(df_train)} 条")
    print(f"  2026数据: {len(df_2026)} 条")
    
    # 准备特征矩阵
    available_inputs = [c for c in INPUT_COLS_BASE if c in df_train.columns and df_train[c].notna().any()]
    
    # 训练数据
    X_train_raw = df_train[available_inputs].copy()
    y_train_raw = df_train[TARGET_COL].copy()
    
    # 清除无效行
    valid_mask = y_train_raw.notna() & (~np.isinf(y_train_raw.replace([np.inf, -np.inf], np.nan)))
    for col in available_inputs:
        valid_mask &= X_train_raw[col].notna() & (~np.isinf(X_train_raw[col].replace([np.inf, -np.inf], np.nan)))
    
    X = X_train_raw[valid_mask].values
    y = y_train_raw[valid_mask].values
    
    print(f"  清洗后训练样本: {len(y)}")
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = np.nan_to_num(X_scaled, nan=0)
    
    # 准备2026年预测数据
    pred_data = {}
    for date in TARGET_DATES:
        mask = df_2026["DATE_STR"] == date
        if mask.sum() == 0:
            # 尝试其他格式
            mask = df_2026["DATE"].astype(str).str.contains(date.replace("-", "")) |\
                   (df_2026["DATE_STR"] == date.replace("2026-", "2026/"))
        
        if mask.sum() > 0:
            X_pred = df_2026.loc[mask, available_inputs].copy()
            X_pred = X_pred.apply(pd.to_numeric, errors="coerce").fillna(
                df_train[available_inputs].median()
            )
            X_pred_scaled = scaler.transform(X_pred.values)
            X_pred_scaled = np.nan_to_num(X_pred_scaled, nan=0)
            pred_data[date] = X_pred_scaled
    
    return X_scaled, y, available_inputs, scaler, pred_data, df_train, df_2026


# ============================================================
# 方法1：Spearman相关系数
# ============================================================
def factor_screening_spearman(X_scaled, y, feature_names):
    """Spearman秩相关系数分析"""
    print("\n📊 方法1: Spearman秩相关系数分析")
    results = []
    for i, name in enumerate(feature_names):
        rho, pval = spearmanr(X_scaled[:, i], y, nan_policy="omit")
        results.append({"Feature": name, "Spearman_rho": rho, "p_value": pval})
    
    df_results = pd.DataFrame(results).sort_values("Spearman_rho", key=abs, ascending=False)
    
    for _, row in df_results.iterrows():
        stars = "***" if row["p_value"] < 0.001 else "**" if row["p_value"] < 0.01 else "*" if row["p_value"] < 0.05 else ""
        print(f"  {row['Feature']:<20} ρ={row['Spearman_rho']:+.3f}  p={row['p_value']:.4f} {stars}")
    
    return df_results


# ============================================================
# 方法2：随机森林特征重要性
# ============================================================
def factor_screening_rf(X_scaled, y, feature_names):
    """随机森林特征重要性分析"""
    print("\n🌲 方法2: 随机森林特征重要性")
    
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, y)
    
    importance = rf.feature_importances_
    sorted_idx = np.argsort(importance)[::-1]
    
    results = []
    for idx in sorted_idx:
        results.append({"Feature": feature_names[idx], "RF_Importance": importance[idx]})
        print(f"  {feature_names[idx]:<20} Importance = {importance[idx]:.4f}")
    
    df_results = pd.DataFrame(results)
    return df_results, rf


# ============================================================
# 方法3：Lasso回归（稀疏特征选择）
# ============================================================
def factor_screening_lasso(X_scaled, y, feature_names):
    """Lasso回归特征选择"""
    print("\n🎯 方法3: Lasso回归特征选择")
    
    lasso = LassoCV(cv=5, random_state=42, max_iter=5000, n_alphas=100)
    lasso.fit(X_scaled, y)
    
    nonzero = np.abs(lasso.coef_) > 1e-6
    results = []
    for i, name in enumerate(feature_names):
        results.append({
            "Feature": name,
            "Lasso_Coef": lasso.coef_[i],
            "Selected": nonzero[i]
        })
    
    df_results = pd.DataFrame(results).sort_values("Lasso_Coef", key=abs, ascending=False)
    
    for _, row in df_results.iterrows():
        mark = "✓" if row["Selected"] else "✗"
        print(f"  {row['Feature']:<20} coef={row['Lasso_Coef']:+8.4f}  [{mark}]")
    
    print(f"  Lasso选择了 {nonzero.sum()}/{len(feature_names)} 个特征，α={lasso.alpha_:.4f}")
    
    return df_results, lasso


# ============================================================
# 综合因素重要性结论
# ============================================================
def comprehensive_factor_ranking(spearman_df, rf_df, lasso_df, feature_names):
    """综合三种方法得出最终排名"""
    print("\n" + "=" * 70)
    print("🏆 综合因素重要性排名（三种方法融合）")
    print("=" * 70)
    
    # 归一化各评分到[0,1]
    scores = pd.DataFrame(index=feature_names)
    
    # Spearman归一化
    sp_dict = dict(zip(spearman_df["Feature"], spearman_df["Spearman_rho"]))
    sp_abs = [abs(sp_dict.get(f, 0)) for f in feature_names]
    if max(sp_abs) > 0:
        scores["Spearman"] = [abs(sp_dict.get(f, 0))/max(sp_abs) for f in feature_names]
    else:
        scores["Spearman"] = 0
    
    # RF归一化
    rf_dict = dict(zip(rf_df["Feature"], rf_df["RF_Importance"]))
    scores["RF"] = [rf_dict.get(f, 0)/max(rf_dict.values()) for f in feature_names]
    
    # Lasso归一化
    la_dict = dict(zip(lasso_df["Feature"], lasso_df["Lasso_Coef"]))
    la_abs = [abs(la_dict.get(f, 0)) for f in feature_names]
    if max(la_abs) > 0:
        scores["Lasso"] = [abs(la_dict.get(f, 0))/max(la_abs) for f in feature_names]
    else:
        scores["Lasso"] = 0
    
    scores["Composite"] = scores.mean(axis=1)
    scores = scores.sort_values("Composite", ascending=False)
    
    print(f"\n{'Rank':<5} {'Feature':<20} {'Spearman':>8} {'RF':>8} {'Lasso':>8} {'综合':>8}")
    print("-" * 65)
    for rank, (feat, row) in enumerate(scores.iterrows(), 1):
        print(f"  {rank:<3} {feat:<20} {row['Spearman']:8.3f} {row['RF']:8.3f} {row['Lasso']:8.3f} {row['Composite']:8.3f}")
    
    top5 = scores.head(5).index.tolist()
    print(f"\n  ✅ Top-5 主要影响因素: {', '.join(top5)}")
    
    return scores, top5


# ============================================================
# 预测模型构建
# ============================================================
def build_and_evaluate_models(X_scaled, y, feature_names, top5_features):
    """建立并评估多个预测模型"""
    print("\n" + "=" * 70)
    print("🔧 预测模型构建与评估")
    print("=" * 70)
    
    # 只使用Top-5特征
    top5_idx = [list(feature_names).index(f) for f in top5_features if f in feature_names]
    if not top5_idx:
        top5_idx = list(range(min(5, X_scaled.shape[1])))
    X_top5 = X_scaled[:, top5_idx]
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X_top5, y, test_size=0.2, random_state=42
    )
    
    models = {}
    results = {}
    
    # 模型A：多元线性回归
    print("\n📈 模型A: 多元线性回归 (基线模型)")
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    
    models["LinearRegression"] = lr
    results["LinearRegression"] = {
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred_lr)),
        "R2": r2_score(y_test, y_pred_lr),
        "MAE": mean_absolute_error(y_test, y_pred_lr),
    }
    cv_scores = cross_val_score(lr, X_top5, y, cv=5, scoring="r2")
    results["LinearRegression"]["CV_R2_mean"] = cv_scores.mean()
    results["LinearRegression"]["CV_R2_std"] = cv_scores.std()
    print(f"  RMSE={results['LinearRegression']['RMSE']:.4f}, R²={results['LinearRegression']['R2']:.4f}, CV_R²={cv_scores.mean():.4f}±{cv_scores.std():.4f}")
    
    # 模型B：XGBoost
    print("\n🚀 模型B: XGBoost回归 (主力模型)")
    xgb_params = {
        "n_estimators": 200, "max_depth": 6, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 42
    }
    xgb_model = xgb.XGBRegressor(**xgb_params)
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    
    models["XGBoost"] = xgb_model
    results["XGBoost"] = {
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred_xgb)),
        "R2": r2_score(y_test, y_pred_xgb),
        "MAE": mean_absolute_error(y_test, y_pred_xgb),
    }
    cv_scores_xgb = cross_val_score(xgb_model, X_top5, y, cv=5, scoring="r2")
    results["XGBoost"]["CV_R2_mean"] = cv_scores_xgb.mean()
    results["XGBoost"]["CV_R2_std"] = cv_scores_xgb.std()
    print(f"  RMSE={results['XGBoost']['RMSE']:.4f}, R²={results['XGBoost']['R2']:.4f}, CV_R²={cv_scores_xgb.mean():.4f}±{cv_scores_xgb.std():.4f}")
    
    # 模型C：SVR
    print("\n📊 模型C: SVR回归 (对比模型)")
    svr = SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.01)
    svr.fit(X_train, y_train)
    y_pred_svr = svr.predict(X_test)
    
    models["SVR"] = svr
    results["SVR"] = {
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred_svr)),
        "R2": r2_score(y_test, y_pred_svr),
        "MAE": mean_absolute_error(y_test, y_pred_svr),
    }
    cv_scores_svr = cross_val_score(svr, X_top5, y, cv=5, scoring="r2")
    results["SVR"]["CV_R2_mean"] = cv_scores_svr.mean()
    results["SVR"]["CV_R2_std"] = cv_scores_svr.std()
    print(f"  RMSE={results['SVR']['RMSE']:.4f}, R²={results['SVR']['R2']:.4f}, CV_R²={cv_scores_svr.mean():.4f}±{cv_scores_svr.std():.4f}")
    
    # 模型对比表
    print("\n📊 模型性能对比:")
    print(f"{'Model':<20} {'RMSE':>10} {'R²':>10} {'MAE':>10} {'CV R²':>15}")
    print("-" * 70)
    for name, metrics in results.items():
        cv_str = f"{metrics['CV_R2_mean']:.4f}±{metrics['CV_R2_std']:.4f}"
        print(f"  {name:<18} {metrics['RMSE']:10.4f} {metrics['R2']:10.4f} {metrics['MAE']:10.4f} {cv_str}")
    
    return models, results, X_train, X_test, y_train, y_test, top5_idx


def plot_model_comparison(models, results, X_test, y_test, top5_idx):
    """模型预测对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    model_names = list(models.keys())
    colors = {"LinearRegression": "#2E86AB", "XGBoost": "#E94F37", "SVR": "#A23B72"}
    
    # 预测值 vs 真实值
    for idx, name in enumerate(model_names):
        ax = axes[idx // 2, idx % 2]
        y_pred = models[name].predict(X_test)
        
        ax.scatter(y_test, y_pred, alpha=0.5, s=20, color=colors[name], edgecolor="none")
        
        # 45度线
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], "k--", linewidth=1, alpha=0.5)
        
        # 标注指标
        rmse = results[name]["RMSE"]
        r2 = results[name]["R2"]
        ax.text(0.05, 0.95, f"RMSE = {rmse:.4f}\nR² = {r2:.4f}", 
                transform=ax.transAxes, va="top", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
        
        ax.set_xlabel("真实值", fontsize=11)
        ax.set_ylabel("预测值", fontsize=11)
        ax.set_title(f"{name}", fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.3)
    
    # 残差图
    ax_resid = axes[1, 1]
    for name in model_names:
        y_pred = models[name].predict(X_test)
        residuals = y_test - y_pred
        ax_resid.scatter(y_pred, residuals, alpha=0.3, s=15, color=colors[name], label=name)
    ax_resid.axhline(y=0, color="k", linestyle="--", linewidth=1)
    ax_resid.set_xlabel("预测值", fontsize=11)
    ax_resid.set_ylabel("残差", fontsize=11)
    ax_resid.set_title("残差分析", fontsize=12, fontweight="bold")
    ax_resid.legend()
    ax_resid.grid(True, alpha=0.3)
    
    plt.suptitle("问题1 — 模型预测性能对比", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig07_model_comparison.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图7: 模型预测对比图已保存")


def plot_feature_importance(scores_df):
    """因素重要性排序图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    top_features = scores_df.head(8)
    features = top_features.index.tolist()[::-1]
    values = top_features["Composite"].values[::-1]
    
    colors_list = plt.cm.RdYlGn(values / max(values))
    bars = ax.barh(range(len(features)), values, color=colors_list, edgecolor="white", linewidth=0.5)
    
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=11)
    ax.set_xlabel("综合重要性得分", fontsize=12)
    ax.set_title("问题1 — 出厂水浊度影响因素综合排名", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")
    
    for i, v in enumerate(values):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=10)
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig08_factor_importance.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print("  ✅ 图8: 因素重要性排序图已保存")


# ============================================================
# 预测目标日期
# ============================================================
def predict_target_dates(models, pred_data, scaler, top5_features, feature_names):
    """预测三个目标日期的NTU值"""
    print("\n" + "=" * 70)
    print("🎯 预测: 2026年2月1日、10日、20日出厂水浊度NTU")
    print("=" * 70)
    
    top5_idx = [list(feature_names).index(f) for f in top5_features if f in feature_names]
    if not top5_idx:
        top5_idx = list(range(min(5, pred_data.get(TARGET_DATES[0], np.zeros((1,1))).shape[1])))
    
    all_predictions = []
    
    # 选择最佳模型 (XGBoost)
    best_model = models.get("XGBoost", list(models.values())[0])
    
    for date in TARGET_DATES:
        X_pred = pred_data.get(date)
        if X_pred is None:
            print(f"  ⚠️ 未找到{date}的预测数据")
            continue
        
        X_pred_top5 = X_pred[:, top5_idx] if X_pred.shape[1] >= len(top5_idx) else X_pred
        
        # 所有模型预测
        preds = {}
        for name, model in models.items():
            y_pred = model.predict(X_pred_top5)
            preds[name] = y_pred
            print(f"\n  📅 {date} - {name}:")
            for i, val in enumerate(y_pred[:12]):
                hour = i * 2 if len(y_pred) > 6 else [7, 9, 11, 13, 15][i] if i < 5 else i
                print(f"    {hour:02d}:00  NTU = {val:.4f}")
        
        # 汇总
        for i in range(len(preds["XGBoost"])):
            hour_info = i * 2 if len(preds["XGBoost"]) > 6 else [7, 9, 11, 13, 15, 17, 19][i] if i < 7 else i
            date_str = f"{date} {hour_info}:00" if isinstance(hour_info, int) else f"{date} 0{hour_info}:00"
            record = {
                "Date": date,
                "Time": f"{hour_info:02d}:00" if isinstance(hour_info, int) else f"0{hour_info}:00",
                "XGBoost_NTU": float(preds["XGBoost"][i]),
                "LinearReg_NTU": float(preds.get("LinearRegression", [0])[i]),
                "SVR_NTU": float(preds.get("SVR", [0])[i]),
            }
            all_predictions.append(record)
    
    # 保存预测结果
    df_pred = pd.DataFrame(all_predictions)
    pred_path = os.path.join(OUTPUT_DIR, "Q1_predictions.csv")
    df_pred.to_csv(pred_path, index=False, encoding="utf-8-sig")
    print(f"\n  ✅ 预测结果已保存: {pred_path}")
    
    return df_pred


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   🏆 APMCM 2026 — 阶段2: 问题1 影响因素筛选与出厂水浊度预测")
    print("=" * 70)
    
    # 1. 数据准备
    X_scaled, y, feature_names, scaler, pred_data, df_train, df_2026 = prepare_data()
    
    # 2. 因素筛选
    print("\n" + "=" * 70)
    print("📊 第一部分: 影响因素筛选（三种方法）")
    print("=" * 70)
    
    spearman_df = factor_screening_spearman(X_scaled, y, feature_names)
    rf_df, rf_model = factor_screening_rf(X_scaled, y, feature_names)
    lasso_df, lasso_model = factor_screening_lasso(X_scaled, y, feature_names)
    
    # 3. 综合排名
    scores_df, top5 = comprehensive_factor_ranking(spearman_df, rf_df, lasso_df, feature_names)
    plot_feature_importance(scores_df)
    
    # 4. 模型构建
    models, model_results, X_train_final, X_test_final, y_train_final, y_test_final, top5_idx = build_and_evaluate_models(
        X_scaled, y, feature_names, top5
    )
    plot_model_comparison(models, model_results, X_test_final, y_test_final, top5_idx)
    
    # 5. 预测
    df_predictions = predict_target_dates(models, pred_data, scaler, top5, feature_names)
    
    # 6. 保存因素分析结果
    scores_df.to_csv(os.path.join(OUTPUT_DIR, "Q1_factor_ranking.csv"), 
                     encoding="utf-8-sig")
    
    print("\n" + "=" * 70)
    print("   ✅ 阶段2完成！进入阶段3（问题2动态时滞模型）...")
    print("=" * 70)

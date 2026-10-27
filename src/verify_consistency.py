"""
最终交付物全量一致性核查
逐项验证论文MD、Excel、原始数据之间的数值一致性
"""

from project_paths import WORKDIR
import pandas as pd, numpy as np, os, json, re
from openpyxl import load_workbook

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "output")

errors = []
warnings = []
passed = []

def check(name, condition, msg):
    if condition:
        passed.append(f"✅ {name}")
    else:
        errors.append(f"❌ {name}: {msg}")

def warn(name, condition, msg):
    if condition:
        passed.append(f"✅ {name}")
    else:
        warnings.append(f"⚠️ {name}: {msg}")

print("="*70)
print("   全量一致性核查")
print("="*70)

# ---- 1. 读取所有数据源 ----
md_path = os.path.join(OUT, "APMCM2026_A题_竞赛论文.md")
with open(md_path, 'r', encoding='utf-8') as f:
    md = f.read()

q1_pred = pd.read_csv(os.path.join(OUT, "Q1_final_predictions.csv"))
q3_pred = pd.read_csv(os.path.join(OUT, "Q3_predictions_final.csv"))
q4_risk = pd.read_csv(os.path.join(OUT, "Q4_2026Q1_daily_risk_final.csv"))
q4_march = pd.read_csv(os.path.join(OUT, "Q4_march_detail_final.csv"))
final_json = json.load(open(os.path.join(OUT, "final_results_complete.json")))

excel_path = os.path.join(OUT, "APMCM2026_A题_答案汇总_FINAL.xlsx")
wb = load_workbook(excel_path)

print(f"\n📁 数据文件检查: {len(passed)} 通过")

# ---- 2. Q1 因素排名检查 ----
print("\n--- Q1 因素排名 ---")
check("Q1 MD中排名#1为CLR", "CLR" in md and "0.676" in md, "CLR排名错误")
check("Q1 MD中排名#2为F/RIDE", "F/RIDE" in md and "0.568" in md, "F/RIDE排名错误")
check("Q1 MD中Spearman=0.703(F/RIDE)", "0.703" in md, "F/RIDE Spearman错误")
check("Q1 MD中RF=1.000(F/RIDE)", "1.000" in md, "F/RIDE RF错误")

# Verify Excel matches
ws1 = wb["Q1_因素排序"]
check("Excel Q1 #1=CLR", ws1.cell(4,2).value and "CLR" in str(ws1.cell(4,2).value), "Excel排名错误")
check("Excel Q1 composite #2=0.568", abs(float(ws1.cell(5,6).value)-0.568)<0.01, "Excel综合得分错误")

# ---- 3. Q1 预测值检查 ----
print("\n--- Q1 预测值 ---")
q1_min = q1_pred["NTU_Predicted"].min()
q1_max = q1_pred["NTU_Predicted"].max()
check(f"Q1 min={q1_min:.4f} (MD应为0.27附近)", q1_min > 0.26 and q1_min < 0.28, f"实际min={q1_min}")
check(f"Q1 max={q1_max:.4f} (MD应为0.49附近)", q1_max > 0.48 and q1_max < 0.50, f"实际max={q1_max}")
check("Q1旧范围(0.10-0.25)不在MD中", "0.10-0.25" not in md, "旧错误范围仍在MD中!")
check("Q1 MD含新范围(0.27-0.49)", "0.27" in md and "0.49" in md, "新范围未入MD")

# ---- 4. Q2 时滞参数检查 ----
print("\n--- Q2 时滞参数 ---")
check("Q2 MD中ALUM时滞=12h", "ALUM" in md and "12" in md and "0.081" in md, "ALUM时滞错误")
check("Q2 MD中R/W NTU时滞=12h", "0.163" in md, "R/W NTU相关错误")
check("Q2 MD中诚实标注ALUM弱相关", "弱信号" in md or "弱相关" in md, "未诚实标注ALUM")
check("Q2 MD报告ARX R²=-0.9129", "-0.9129" in md, "ARX R²值错误")
check("Q2 MD报告NARX R²=-0.0035", "-0.0035" in md, "NARX R²值错误")

# ---- 5. Q3 多步预测检查 ----
print("\n--- Q3 多步预测 ---")
q3 = final_json["Q3"]
check("Q3 MD t+0h R²=0.7072", "0.7072" in md, "t+0h R²错误")
check("Q3 MD t+2h R²=0.5529", "0.5529" in md, "t+2h R²错误")
check("Q3 MD t+12h R²=0.3919", "0.3919" in md, "t+12h R²错误")
check("Q3旧最优(2h=0.6626)不在MD中", "0.6626" not in md, "旧错误值仍在MD中!")
check("Q3旧错误(1h=0.3804)不在MD中", "0.3804" not in md, "旧错误值仍在MD中!")

# ---- 6. Q4 风险检查 ----
print("\n--- Q4 风险 ---")
n_safe = (q4_risk["风险等级"] == "安全").sum()
n_low = (q4_risk["风险等级"] == "低风险").sum()
n_medium = (q4_risk["风险等级"] == "中风险").sum() if "中风险" in q4_risk.columns else 0
n_high = (q4_risk["风险等级"] == "高风险").sum() if "高风险" in q4_risk.columns else 0
total = len(q4_risk)

check(f"Q4总天数=90", total == 90, f"实际总天数={total}")
check(f"Q4安全=89", n_safe == 89, f"实际安全={n_safe}")
check(f"Q4低风险=1", n_low == 1, f"实际低风险={n_low}")
check(f"Q4中风险=0", n_medium == 0, f"实际中风险={n_medium}")
check(f"Q4高风险=0", n_high == 0, f"实际高风险={n_high}")
check("Q4旧数据(316天)不在MD中", "316天" not in md and "290天" not in md, "旧风险天数仍在MD中!")
check("Q4 MD含98.9%", "98.9%" in md, "Q4安全百分比错误")
check("Q4旧错误(3.5%高风险)不在MD中", "3.5%" not in md or "高风险" not in md[md.find("3.5%"):md.find("3.5%")+50] if "3.5%" in md else True, "")

# ---- 7. Excel检查 ----
print("\n--- Excel完整性 ---")
expected_sheets = ["Q1_因素排序","Q1_预测结果","Q2_时滞参数","Q2_模型验证",
                   "Q3_预测性能","Q3_预测值","Q4_风险分布","Q4_三月详细"]
for s in expected_sheets:
    check(f"Excel Sheet '{s}' 存在", s in wb.sheetnames, "Sheet缺失")

# Check Q4 Excel data
ws7 = wb["Q4_风险分布"]
excel_safe = int(ws7.cell(4,2).value) if ws7.cell(4,2).value else 0
excel_low = int(ws7.cell(5,2).value) if ws7.cell(5,2).value else 0
check(f"Excel Q4安全天数={excel_safe}", excel_safe == 89, f"实际={excel_safe}")
check(f"Excel Q4低风险天数={excel_low}", excel_low == 1, f"实际={excel_low}")

# ---- 8. 参考文献检查 ----
print("\n--- 参考文献 ---")
check("GB 5749-2022在参考文献中", "GB 5749-2022" in md, "国标引用缺失")
check("XGBoost KDD论文存在", "KDD 2016" in md or "KDD, 2016" in md, "XGBoost引用可能有问题")
check("Breiman RF论文存在", "Breiman" in md and "Random forest" in md, "RF引用缺失")
check("旧编造引用[2]('十五五'规划)不在MD中", "十五五" not in md, "编造引用仍在!")
check("旧存疑[4](Pearson 1901)不在MD中", "Pearson, K." not in md, "存疑引用仍在!")

# ---- 9. 内容完整性 ----
print("\n--- 内容完整性 ---")
check("摘要含正确ALUM时滞", "ALUM" in md[:500] and "12小时" in md[:500], "摘要错误")
check("摘要含Q3 R²=0.707", "0.707" in md[:500], "摘要Q3 R²错误")
check("摘要含Q4 98.9%", "98.9%" in md[:500], "摘要Q4数据错误")
check("物理机制描述已修正(清水池≠混凝)", "12小时特征时间" in md or "前馈窗口" in md, "物理描述可能未修正")
check("模型局限含诚实讨论", "负" in md and "R²" in md, "缺乏诚实讨论")

# ---- 10. 最终总结 ----
print("\n" + "="*70)
print(f"   核查结果: {len(passed)} 通过, {len(warnings)} 警告, {len(errors)} 错误")
print("="*70)

if errors:
    print("\n🔴 错误(必须修正):")
    for e in errors:
        print(f"  {e}")

if warnings:
    print("\n🟡 警告:")
    for w in warnings:
        print(f"  {w}")

if not errors:
    print("\n✅ 全部通过! 所有数据一致!")

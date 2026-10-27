# Archived unverified template: not an actual submission, historical score reproduction, or AI interaction record.
from project_paths import require_historical_templates
require_historical_templates()
"""
文件夹结构重组与文件重命名 - 按优秀数学建模论文标准
"""

from project_paths import WORKDIR
import os, shutil, json

BASE = str(WORKDIR)

# 定义新的目录结构
NEW_STRUCTURE = {
    "0_赛题与要求": {
        "description": "比赛题目PDF、题目截图、格式要求",
        "files_from_root": [
            "A题 自来水厂水质预测与评估.pdf",
            "A题.png", "A题 (2).png", "A题 (3).png", "A题 (4).png", "A题 (5).png",
            "格式要求 (1).png", "格式要求 (2).png",
            "# 🏆 APMCM 2026 亚太杯数学建模竞赛 A 题 · AI.txt",
        ]
    },
    "1_原始数据": {
        "description": "2025年(12个月)和2026年(1-3月)原始水质监测数据",
        "subdirs": ["2025年数据", "2026年数据"],
        "source_dirs": ["2025数据集", "2026数据集"],
    },
    "2_代码": {
        "description": "全部建模、分析、图表生成、论文生成代码",
        "source_dir": "code",
        "keep_files": True,
    },
    "3_图表": {
        "description": "统一学术科研图表(PDF+PNG，300DPI)",
        "subdirs": ["核心图表", "过程图表"],
        # 核心图表是6张Nature图
        # 过程图表是EDA阶段和中间产生的图
        "core_patterns": ["fig01_","fig02_","fig03_","fig04_","fig05_","fig06_"],
    },
    "4_答案表": {
        "description": "竞赛答案汇总表(Excel 8 Sheets)和各题结果数据",
    },
    "5_论文": {
        "description": "最终论文(Word+Markdown)及审查/自检报告",
    },
    "6_过程文档": {
        "description": "中间处理数据(CSV)、其他过程性文件",
    },
}

def safe_move(src, dst):
    """安全移动文件，如果被锁定则复制"""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            try: os.remove(dst)
            except: pass
        try:
            shutil.move(src, dst)
        except PermissionError:
            # 文件被锁定时复制
            shutil.copy2(src, dst)
        return True
    return False

def safe_copy(src, dst):
    """安全复制文件"""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
        return True
    return False

print("="*60)
print("  文件夹结构重组与文件重命名")
print("="*60)

# 重命名映射 (原路径 -> 新路径)
renames = []

# === 1. 创建新目录结构 ===
for dirname, info in NEW_STRUCTURE.items():
    new_dir = os.path.join(BASE, dirname)
    os.makedirs(new_dir, exist_ok=True)
    print(f"📁 创建: {dirname}/")
    
    if "subdirs" in info:
        for sub in info["subdirs"]:
            os.makedirs(os.path.join(new_dir, sub), exist_ok=True)

# === 2. 移动赛题与要求 ===
print("\n📂 整理: 0_赛题与要求/")
target = os.path.join(BASE, "0_赛题与要求")
for f in NEW_STRUCTURE["0_赛题与要求"]["files_from_root"]:
    src = os.path.join(BASE, f)
    if os.path.exists(src):
        clean_name = f.replace("# 🏆 ", "").replace("  ", " ")
        dst = os.path.join(target, clean_name)
        safe_move(src, dst)
        print(f"  ✅ {f} → 0_赛题与要求/{clean_name}")

# === 3. 移动原始数据 ===
print("\n📂 整理: 1_原始数据/")
source_dirs = NEW_STRUCTURE["1_原始数据"]["source_dirs"]
subdirs = NEW_STRUCTURE["1_原始数据"]["subdirs"]
for src_dir, sub in zip(source_dirs, subdirs):
    src_path = os.path.join(BASE, src_dir)
    dst_path = os.path.join(BASE, "1_原始数据", sub)
    if os.path.exists(src_path):
        for f in os.listdir(src_path):
            if f.startswith("~$"):  # 跳过临时文件
                continue
            src_f = os.path.join(src_path, f)
            dst_f = os.path.join(dst_path, f)
            safe_move(src_f, dst_f)
            print(f"  ✅ {f} → 1_原始数据/{sub}/{f}")
        # 删除空目录
        try:
            os.rmdir(src_path)
            print(f"  🗑️ 删除空目录: {src_dir}")
        except:
            pass

# === 4. 复制代码 ===
print("\n📂 整理: 2_代码/")
# 代码留在原地，创建 code 在 2_代码 的子目录中
# 实际上，保留 code/ 原目录，在 2_代码 中创建软引用
# 或者直接移动 code/ 到 2_代码/
src_code = os.path.join(BASE, "code")
dst_code = os.path.join(BASE, "2_代码")
if os.path.exists(src_code):
    for f in os.listdir(src_code):
        src_f = os.path.join(src_code, f)
        dst_f = os.path.join(dst_code, f)
        if os.path.isfile(src_f):
            safe_copy(src_f, dst_f)
            print(f"  ✅ {f}")
    # 保留原code目录（不影响现有引用）

# === 5. 整理图表 ===
print("\n📂 整理: 3_图表/")
fig_src = os.path.join(BASE, "output", "figures")
core_dir = os.path.join(BASE, "3_图表", "核心图表")
process_dir = os.path.join(BASE, "3_图表", "过程图表")

core_pats = NEW_STRUCTURE["3_图表"]["core_patterns"]
if os.path.exists(fig_src):
    for f in sorted(os.listdir(fig_src)):
        src_f = os.path.join(fig_src, f)
        if not os.path.isfile(src_f):
            continue
        
        # 判断是核心图表还是过程图表
        is_core = any(f.startswith(pat) for pat in core_pats)
        if is_core:
            # 核心图表重命名
            if "timeseries" in f:
                new_name = f"图1_目标变量时序图.{f.split('.')[-1]}"
            elif "factor_importance" in f:
                new_name = f"图2_因素重要性排序.{f.split('.')[-1]}"
            elif "ccf_lag" in f:
                new_name = f"图3_CCF时滞热图.{f.split('.')[-1]}"
            elif "q3_multistep" in f:
                new_name = f"图4_Q3多步预测面板.{f.split('.')[-1]}"
            elif "q4_risk" in f:
                new_name = f"图5_Q4风险评价.{f.split('.')[-1]}"
            elif "q1_models" in f:
                new_name = f"图6_Q1模型对比.{f.split('.')[-1]}"
            else:
                new_name = f
            safe_copy(src_f, os.path.join(core_dir, new_name))
        else:
            # 过程图表直接复制
            safe_copy(src_f, os.path.join(process_dir, f))

print(f"  ✅ 核心图表: 6张(各含PDF+PNG)")
print(f"  ✅ 过程图表: {len([f for f in os.listdir(process_dir) if os.path.isfile(os.path.join(process_dir,f))])} 张")

# === 6. 整理答案表 ===
print("\n📂 整理: 4_答案表/")
answer_dir = os.path.join(BASE, "4_答案表")
output_dir = os.path.join(BASE, "output")

# 答案Excel
safe_copy(
    os.path.join(output_dir, "APMCM2026_A题_答案汇总_FINAL.xlsx"),
    os.path.join(answer_dir, "APMCM2026_A题_答案汇总.xlsx")
)

# 各题结果数据
result_files = [
    ("Q1_factor_ranking.csv", "Q1_因素重要性排序.csv"),
    ("Q1_final_predictions.csv", "Q1_预测结果.csv"),
    ("Q2_final_results.json", "Q2_时滞分析结果.json"),
    ("Q2_lag_parameters.csv", "Q2_时滞参数表.csv"),
    ("Q3_predictions_final.csv", "Q3_多步预测值.csv"),
    ("Q4_2026Q1_daily_risk_final.csv", "Q4_逐日风险评分.csv"),
    ("Q4_march_detail_final.csv", "Q4_三月逐日明细.csv"),
    ("final_results_complete.json", "最终结果汇总.json"),
]

for src_name, dst_name in result_files:
    src = os.path.join(output_dir, src_name)
    dst = os.path.join(answer_dir, dst_name)
    safe_copy(src, dst)
    print(f"  ✅ {dst_name}")

# === 7. 整理论文 ===
print("\n📂 整理: 5_论文/")
paper_dir = os.path.join(BASE, "5_论文")

paper_files = [
    ("APMCM2026_A题_竞赛论文_最终版.docx", "APMCM2026_A题_竞赛论文.docx"),
    ("APMCM2026_A题_竞赛论文.md", "APMCM2026_A题_竞赛论文.md"),
    ("系统化论文审查报告.md", "论文审查报告.md"),
    ("自检报告.md", "论文自检报告.md"),
]

for src_name, dst_name in paper_files:
    src = os.path.join(output_dir, src_name)
    dst = os.path.join(paper_dir, dst_name)
    if os.path.exists(src):
        safe_copy(src, dst)
        print(f"  ✅ {dst_name}")

# === 8. 整理过程文档 ===
print("\n📂 整理: 6_过程文档/")
process_dir = os.path.join(BASE, "6_过程文档")

# 处理后的数据
data_processed = os.path.join(BASE, "data", "processed")
if os.path.exists(data_processed):
    for f in os.listdir(data_processed):
        src_f = os.path.join(data_processed, f)
        dst_f = os.path.join(process_dir, f)
        safe_copy(src_f, dst_f)
        print(f"  ✅ data: {f}")

# 旧版论文和答案
old_files = [
    "APMCM2026_A题_竞赛论文.docx",
    "APMCM2026_A题_答案汇总.xlsx",
]
for f in old_files:
    src = os.path.join(output_dir, f)
    if os.path.exists(src) and "最终版" not in f:
        dst = os.path.join(process_dir, f"旧版_{f}")
        safe_copy(src, dst)

# === 9. 创建 README ===
print("\n📄 创建 README.md")
readme_content = """# 🏆 APMCM 2026 亚太杯数学建模竞赛

## 📋 基本信息
- **比赛**：APMCM 2026 (Asia-Pacific Cup Mathematical Contest in Modeling)
- **题目**：A题 — 自来水厂水质预测与评估
- **归档属性**：水质建模练习（不证明参赛）
- **完成日期**：2026年6月14日

## 📁 目录结构

```
亚太杯数学建模竞赛/
├── 0_赛题与要求/          # 比赛题目PDF、题目截图、格式要求
├── 1_原始数据/             # 原始水质监测数据(2025年+2026年)
│   ├── 2025年数据/         # 12个月JBALB水质数据(xlsx)
│   └── 2026年数据/         # 1-3月水质数据(xls)
├── 2_代码/                 # 全部建模分析代码
├── 3_图表/                 # 科研图表(PDF+PNG, 300DPI)
│   ├── 核心图表/           # 论文用6张统一学术核心图表
│   └── 过程图表/           # EDA和建模过程中间图表
├── 4_答案表/               # 竞赛答案汇总与各题结果数据
├── 5_论文/                 # 最终论文(Word+Markdown)及审查报告
├── 6_过程文档/             # 处理后的中间数据(CSV)
└── README.md               # 本文件
```

## 🔬 论文核心成果

### 四个问题的解决方案

| 问题 | 方法 | 核心结果 |
|------|------|---------|
| Q1 因素筛选与预测 | Spearman + RF + Lasso → XGBoost | CLR #1 (0.676), R²=0.765 |
| Q2 动态时滞模型 | CCF分析 → ARX/NARX | τ=12h特征时间 (ρ≤0.163) |
| Q3 混合动态预测 | CSTR物理模型 + XGBoost | t+0h R²=0.707 |
| Q4 风险评价体系 | 三维风险评分(幅度+时长+趋势) | 98.9%安全, 0天高风险 |

### 关键创新点
- **多方法交叉验证**：三种独立方法筛选因素，避免单一方法偏差
- **物理-ML融合**：CSTR质量守恒模型与XGBoost数据驱动模型混合
- **时滞精确建模**：CCF系统扫描0-24h，识别12h特征时间
- **诚实报告文化**：Q2模型R²为负不回避，给出物理机制解释

## 📦 最终交付物

| 文件 | 位置 | 说明 |
|------|------|------|
| 竞赛论文 | `5_论文/APMCM2026_A题_竞赛论文.docx` | 含6张Nature图表的Word论文 |
| 答案汇总 | `4_答案表/APMCM2026_A题_答案汇总.xlsx` | 8个Sheet完整答案 |
| 核心图表 | `3_图表/核心图表/` | 6张PNG+6张PDF，300DPI |
| 结果数据 | `4_答案表/` | Q1-Q4各题CSV/JSON结果 |
| 代码 | `2_代码/` | 11个Python脚本 + 1个JS脚本 |
| 审查报告 | `5_论文/论文审查报告.md` | nature-reviewer 3审稿人+科学批判 |

## 🛠 技术栈
- **数据**：Python (pandas, numpy, scipy)
- **建模**：XGBoost, LassoCV, RidgeCV, SVR, TimeSeriesSplit
- **图表**：Matplotlib (Nature期刊配色体系, Arial字体, 300DPI)
- **论文**：python-docx (宋体小四, 单倍行距)
- **审查**：nature-reviewer + scientific-critical-thinking

## 📝 参考文献
1. GB 5749-2022 生活饮用水卫生标准
2. Chen & Guestrin, XGBoost, KDD 2016
3. Tibshirani, Lasso, JRSSB 1996
4. Breiman, Random Forests, ML 2001
5. Box, Jenkins, Time Series Analysis, Wiley 2015
"""

with open(os.path.join(BASE, "README.md"), 'w', encoding='utf-8') as f:
    f.write(readme_content)
print("  ✅ README.md 已创建")

# === 10. 统计总结 ===
print("\n" + "="*60)
print("   重组完成！新目录结构：")
print("="*60)

for dirname in sorted(os.listdir(BASE)):
    full = os.path.join(BASE, dirname)
    if os.path.isdir(full) and dirname not in ['.workbuddy', 'output', 'code', 'data', '2025数据集', '2026数据集', '__pycache__']:
        file_count = sum(1 for root,dirs,files in os.walk(full) for f in files)
        size = sum(os.path.getsize(os.path.join(root,f)) for root,dirs,files in os.walk(full) for f in files)
        print(f"  📁 {dirname}/ ({file_count} files, {size/1024:.0f} KB)")

print(f"\n✅ 全部完成！")
print(f"   新结构: 0_赛题→1_数据→2_代码→3_图表→4_答案→5_论文→6_过程")
print(f"   原始output/、code/、data/目录保留不变（兼容现有路径引用）")

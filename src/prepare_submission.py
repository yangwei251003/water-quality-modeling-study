# Archived unverified template: not an actual submission, historical score reproduction, or AI interaction record.
from project_paths import require_historical_templates
require_historical_templates()
"""
准备APMCM 2026 A题最终提交材料
1. Word → PDF (AEXAMPLE_TEAM_ID.pdf)
2. 支撑材料 ZIP (AEXAMPLE_TEAM_IDfj.zip)
3. 清理旧文件
"""

from project_paths import WORKDIR
import os, sys, shutil, zipfile
from pathlib import Path

BASE = str(WORKDIR)
SUBMIT_DIR = os.path.join(BASE, "提交材料")
os.makedirs(SUBMIT_DIR, exist_ok=True)

TEAM_ID = "EXAMPLE_TEAM_ID"
PROBLEM = "A"
PDF_NAME = f"{PROBLEM}{TEAM_ID}.pdf"
ZIP_NAME = f"{PROBLEM}{TEAM_ID}fj.zip"

print("=" * 60)
print("  APMCM 2026 最终提交材料准备")
print(f"  参赛编号: {TEAM_ID}")
print(f"  题目: {PROBLEM}题")
print("=" * 60)

# ============================================================
# Step 1: 论文Word → PDF
# ============================================================
print("\n📄 Step 1: 论文转PDF...")

paper_docx = os.path.join(BASE, "5_论文", "APMCM2026_A题_竞赛论文_最终排版版.docx")
if not os.path.exists(paper_docx):
    paper_docx = os.path.join(BASE, "5_论文", "APMCM2026_A题_竞赛论文.docx")
    print(f"  使用备选: {paper_docx}")

pdf_output = os.path.join(SUBMIT_DIR, PDF_NAME)

try:
    from docx2pdf import convert
    convert(paper_docx, pdf_output)
    pdf_size = os.path.getsize(pdf_output)
    print(f"  ✅ PDF已生成: {PDF_NAME} ({pdf_size/1024:.0f} KB)")
except Exception as e:
    print(f"  ⚠️ docx2pdf失败: {e}")
    print(f"  尝试备用方案...")
    try:
        import subprocess
        # Try using PowerShell to call Word COM
        ps_script = f'''
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $doc = $word.Documents.Open("{paper_docx}")
        $doc.SaveAs([ref]"{pdf_output}", [ref]17)
        $doc.Close()
        $word.Quit()
        '''
        with open(os.path.join(BASE, "temp_convert.ps1"), 'w') as f:
            f.write(ps_script)
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", 
                                 os.path.join(BASE, "temp_convert.ps1")],
                                capture_output=True, text=True, timeout=60)
        os.remove(os.path.join(BASE, "temp_convert.ps1"))
        if os.path.exists(pdf_output):
            pdf_size = os.path.getsize(pdf_output)
            print(f"  ✅ PDF已生成: {PDF_NAME} ({pdf_size/1024:.0f} KB)")
        else:
            # Fallback: just copy the docx and rename
            shutil.copy2(paper_docx, pdf_output)
            print(f"  ⚠️ PDF转换失败，已复制DOCX作为备选: {PDF_NAME}")
    except Exception as e2:
        print(f"  ❌ 备用方案也失败: {e2}")
        shutil.copy2(paper_docx, pdf_output)
        print(f"  ⚠️ 已复制DOCX: {PDF_NAME}（请手动在Word中另存为PDF）")

# ============================================================
# Step 2: 打包支撑材料
# ============================================================
print("\n📦 Step 2: 打包支撑材料...")

zip_path = os.path.join(SUBMIT_DIR, ZIP_NAME)
support_files = []

# 收集支撑文件（排除原始数据）
include_dirs = {
    "2_代码": "代码文件",
    "3_图表": "科研图表",
    "4_答案表": "答案汇总与结果",
    "5_论文": "论文与审查报告",
    "6_过程文档": "处理数据（中间产物）",
}

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dir_name, dir_label in include_dirs.items():
        dir_path = os.path.join(BASE, dir_name)
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                if f.startswith('~$'):  # 跳过临时文件
                    continue
                full_path = os.path.join(root, f)
                arc_name = os.path.relpath(full_path, BASE)
                zf.write(full_path, arc_name)
                support_files.append(arc_name)
    
    # 也添加根目录的README
    readme_path = os.path.join(BASE, "README.md")
    if os.path.exists(readme_path):
        zf.write(readme_path, "README.md")

zip_size = os.path.getsize(zip_path)
print(f"  ✅ 支撑材料已打包: {ZIP_NAME} ({zip_size/1024:.0f} KB)")
print(f"  📁 包含 {len(support_files)} 个文件")

# ============================================================
# Step 3: 清理旧文件
# ============================================================
print("\n🧹 Step 3: 清理旧文件...")

# 要删除的文件和目录
to_delete = [
    # 旧数据目录（已迁移到1_原始数据）
    "2025数据集",
    # 旧的代码副本和原始output
    # (保留code/和output/因为它们被代码路径引用，但可以精简output中的旧文件)
]

# 清理output中的旧版文件
old_output_files = [
    "APMCM2026_A题_竞赛论文.docx",
    "APMCM2026_A题_竞赛论文.md", 
    "APMCM2026_A题_答案汇总.xlsx",
    "Q1_predictions.csv",
    "Q2_results.json",
    "Q3_results.json",
    "Q4_risk_assessment.csv",
    "Q4_risk_final.csv",
    "~$MCM2026_A题_竞赛论文.docx",
    "~$MCM2026_A题_竞赛论文_最终版.docx",
]

deleted_count = 0
saved_count = 0

# 删除旧的output文件
for fname in old_output_files:
    fpath = os.path.join(BASE, "output", fname)
    if os.path.exists(fpath):
        try:
            os.remove(fpath)
            deleted_count += 1
            print(f"  🗑️ output/{fname}")
        except:
            saved_count += 1

# 删除旧的数据目录
for dname in to_delete:
    dpath = os.path.join(BASE, dname)
    if os.path.exists(dpath):
        try:
            shutil.rmtree(dpath)
            deleted_count += 1
            print(f"  🗑️ {dname}/")
        except:
            saved_count += 1
            print(f"  ⚠️ 无法删除 {dname}/ (跳过)")

# 清理output/figures中的旧版fig文件（保留figS*和fig0*新文件）
old_fig_patterns = ["fig07_model_comparison", "fig08_factor_importance", 
                    "fig09_q2_dynamic_model", "fig10_q3_multistep_prediction",
                    "fig11_q4_risk_assessment", "fig_nature_factor_ranking",
                    "fig_nature_q2_lag_model", "fig_nature_risk_panel",
                    "fig_nature_q1_pred_vs_obs", "fig_nature_q3_multistep",
                    "fig04a_ccf_FILT", "fig04a_ccf_NTU",
                    "fig01_target_timeseries", "fig02_correlation_heatmap",
                    "fig03_scatter_raw_vs_filt", "fig05_seasonal_decomposition",
                    "fig06_distributions"]
for fname in os.listdir(os.path.join(BASE, "output", "figures")):
    for pat in old_fig_patterns:
        if fname.startswith(pat):
            fpath = os.path.join(BASE, "output", "figures", fname)
            try:
                os.remove(fpath)
                deleted_count += 1
                break
            except:
                pass

print(f"\n  共删除 {deleted_count} 个旧文件/目录, {saved_count} 个正在使用")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("  ✅ 提交材料准备完成！")
print("=" * 60)
print(f"""
📁 提交材料目录: 提交材料/
  ├── {PDF_NAME}  ← 论文PDF
  └── {ZIP_NAME}  ← 支撑材料 ({zip_size/1024:.0f} KB)

📋 提交步骤：
  1. 打开官网提交页面
  2. 上传论文: 提交材料/{PDF_NAME}
  3. 上传支撑材料: 提交材料/{ZIP_NAME}
  4. 确认提交
""")

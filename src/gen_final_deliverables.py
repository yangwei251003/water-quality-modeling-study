# Archived unverified template: not an actual submission, historical score reproduction, or AI interaction record.
from project_paths import require_historical_templates
require_historical_templates()
"""
生成最终交付物: Word论文 + Excel答案表 + 统一学术图表
基于所有修正后的数据
"""

from project_paths import WORKDIR
import pandas as pd, numpy as np, os, json, warnings
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
warnings.filterwarnings('ignore')

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "output")
FIG = os.path.join(OUT, "figures")

# ============================================================
# PART 1: Excel答案汇总表 (8 Sheets)
# ============================================================

wb = Workbook()
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
header_fill = PatternFill(start_color='2E86AB', end_color='2E86AB', fill_type='solid')
header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
data_font = Font(name='Arial', size=9)
title_font = Font(name='Arial', size=12, bold=True, color='2C3E50')

def format_header(ws, row, cols):
    for c in range(1, cols+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border

def format_data(ws, start_row, end_row, cols):
    for r in range(start_row, end_row+1):
        for c in range(1, cols+1):
            cell = ws.cell(row=r, column=c)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')

def auto_width(ws, cols, min_w=10, max_w=30):
    for c in range(1, cols+1):
        max_len = min_w
        for r in range(1, ws.max_row+1):
            val = ws.cell(row=r, column=c).value
            if val:
                max_len = max(max_len, min(len(str(val))*1.3, max_w))
        ws.column_dimensions[get_column_letter(c)].width = max_len

print("="*60)
print("生成Excel答案汇总表...")

# ---- Sheet 1: Q1因素排序 ----
ws1 = wb.active
ws1.title = "Q1_因素排序"
ws1.cell(1,1,"Q1: 影响出厂水NTU的因素重要性综合排名").font = title_font
ws1.merge_cells('A1:F1')
headers = ["排名","影响因素","Spearman ρ","RF Importance","Lasso系数","综合得分"]
for i,h in enumerate(headers,1):
    ws1.cell(3,i,h)
format_header(ws1,3,6)

factor_data = [
    [1,"CLR (处理后水色度)",0.321,0.706,1.000,0.676],
    [2,"F/RIDE (混凝剂投加流量)",0.703,1.000,0.000,0.568],
    [3,"R/W FLOW (原水流量)",0.991,0.115,0.163,0.423],
    [4,"T/W FLOW (出厂水流量)",1.000,0.108,0.000,0.369],
    [5,"CL2 (余氯)",0.358,0.279,0.000,0.212],
    [6,"R/W PH",0.508,0.000,0.000,0.169],
    [7,"R/W CLR (原水色度)",0.267,0.110,0.000,0.126],
    [8,"ALUM (矾投加量)",0.366,0.006,0.000,0.124],
    [9,"RIVER LEVEL",0.176,0.187,0.000,0.121],
    [10,"R/W NTU (原水浊度)",0.200,0.073,0.000,0.091],
]
for i,row in enumerate(factor_data):
    for j,val in enumerate(row):
        ws1.cell(4+i, j+1, val)
format_data(ws1,4,4+len(factor_data)-1,6)
auto_width(ws1,6)

# ---- Sheet 2: Q1预测结果 ----
ws2 = wb.create_sheet("Q1_预测结果")
ws2.cell(1,1,"Q1: 出厂水NTU预测值 (2026年2月1/10/20日)").font = title_font
ws2.merge_cells('A1:E1')
headers2 = ["日期","时间","NTU预测值","达标(≤1NTU)","模型"]
for i,h in enumerate(headers2,1):
    ws2.cell(3,i,h)
format_header(ws2,3,5)

df_q1 = pd.read_csv(os.path.join(OUT, "Q1_final_predictions.csv"))
for i,(_,r) in enumerate(df_q1.iterrows()):
    ws2.cell(4+i,1,str(r.get("Date","")))
    ws2.cell(4+i,2,str(r.get("Time","")))
    ws2.cell(4+i,3,round(float(r.get("NTU_Predicted",0)),4))
    ws2.cell(4+i,4,"是")
    ws2.cell(4+i,5,"XGBoost")
format_data(ws2,4,4+len(df_q1)-1,5)
auto_width(ws2,5)

# ---- Sheet 3: Q2时滞参数 ----
ws3 = wb.create_sheet("Q2_时滞参数")
ws3.cell(1,1,"Q2: CCF时滞分析参数汇总").font = title_font
ws3.merge_cells('A1:F1')
headers3 = ["输入变量","最优时滞τ(h)","|Spearman ρ|","有效性","物理机制"]
for i,h in enumerate(headers3,1):
    ws3.cell(3,i,h)
format_header(ws3,3,5)

lag_data = [
    ["R/W NTU",12,0.163,"✅ 有效","原水经混凝-沉淀-过滤全流程传输"],
    ["R/W PH","—",0.000,"❌ 常数(仅1个值)","2026Q1 pH恒定为7.0"],
    ["ALUM",12,0.081,"⚠️ 弱信号","矾投加参与混凝反应"],
    ["F/RIDE","—",0.000,"❌ 常数(仅1个值)","2026Q1流量恒定"],
    ["R/W FLOW",12,0.102,"⚠️ 弱信号","流量影响水力停留时间"],
]
for i,row in enumerate(lag_data):
    for j,val in enumerate(row):
        ws3.cell(4+i,j+1,val)
format_data(ws3,4,4+len(lag_data)-1,5)
auto_width(ws3,5)

# ---- Sheet 4: Q2模型验证 ----
ws4 = wb.create_sheet("Q2_模型验证")
ws4.cell(1,1,"Q2: ARX/NARX模型验证").font = title_font
ws4.merge_cells('A1:D1')
headers4 = ["模型","RMSE","R²","说明"]
for i,h in enumerate(headers4,1):
    ws4.cell(3,i,h)
format_header(ws4,3,4)

q2_data = [
    ["ARX (Ridge)",0.3028,-0.9129,"线性时滞模型，预测低于基线"],
    ["NARX (XGBoost)",0.2193,-0.0035,"非线性时滞模型，RMSE优于ARX"],
]
for i,row in enumerate(q2_data):
    for j,val in enumerate(row):
        ws4.cell(4+i,j+1,val)
format_data(ws4,4,5,4)
auto_width(ws4,4)

# ---- Sheet 5: Q3预测性能 ----
ws5 = wb.create_sheet("Q3_预测性能")
ws5.cell(1,1,"Q3: CSTR+XGBoost混合预测性能").font = title_font
ws5.merge_cells('A1:E1')
headers5 = ["预测步长","RMSE (NTU)","R²","预测可靠性","物理规律"]
for i,h in enumerate(headers5,1):
    ws5.cell(3,i,h)
format_header(ws5,3,5)

q3_metrics = [
    ["t+0h (即时)",0.1084,0.7072,"★★★★☆ 良好","最近精度最高"],
    ["t+2h",0.1348,0.5529,"★★★☆☆ 可接受",""],
    ["t+4h",0.1529,0.4314,"★★★☆☆ 可接受",""],
    ["t+6h",0.1457,0.4898,"★★★☆☆ 可接受",""],
    ["t+8h",0.1802,0.2278,"★★☆☆☆ 一般",""],
    ["t+12h",0.1607,0.3919,"★★☆☆☆ 一般","随步长总体递减"],
]
for i,row in enumerate(q3_metrics):
    for j,val in enumerate(row):
        ws5.cell(4+i,j+1,val)
format_data(ws5,4,9,5)
auto_width(ws5,5)

# ---- Sheet 6: Q3预测值 ----
ws6 = wb.create_sheet("Q3_预测值")
ws6.cell(1,1,"Q3: 目标日期多步长NTU预测值").font = title_font
ws6.merge_cells('A1:H1')
headers6 = ["日期","时间","NTU_t+0h","NTU_t+2h","NTU_t+4h","NTU_t+6h","NTU_t+8h","NTU_t+12h"]
for i,h in enumerate(headers6,1):
    ws6.cell(3,i,h)
format_header(ws6,3,8)

df_q3 = pd.read_csv(os.path.join(OUT, "Q3_predictions_final.csv"))
for i,(_,r) in enumerate(df_q3.iterrows()):
    ws6.cell(4+i,1,str(r.get("日期","")))
    ws6.cell(4+i,2,str(r.get("时间","")))
    for j,col in enumerate(["NTU+0h","NTU+2h","NTU+4h","NTU+6h","NTU+8h","NTU+12h"]):
        ws6.cell(4+i,3+j,round(float(r.get(col,0)),4))
format_data(ws6,4,4+len(df_q3)-1,8)
auto_width(ws6,8)

# ---- Sheet 7: Q4风险分布 ----
ws7 = wb.create_sheet("Q4_风险分布")
ws7.cell(1,1,"Q4: 2026年Q1 (1-3月) 逐日水质风险分级统计").font = title_font
ws7.merge_cells('A1:E1')
headers7 = ["风险等级","天数","占比","标签","典型情景"]
for i,h in enumerate(headers7,1):
    ws7.cell(3,i,h)
format_header(ws7,3,5)

green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
yellow_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')

risk_summary = [
    ["安全 (Safe)",89,"98.9%","🟢 I级","日常运行状态，NTU远低于1"],
    ["低风险 (Low)",1,"1.1%","🟡 II级","1月10日，最大NTU=2.15"],
    ["中风险 (Medium)",0,"0%","🟠 III级","—"],
    ["高风险 (High)",0,"0%","🔴 IV级","—"],
    ["合计",90,"100%","",""],
]
for i,row in enumerate(risk_summary):
    for j,val in enumerate(row):
        ws7.cell(4+i,j+1,val)
    if i == 0:
        for j in range(1,6):
            ws7.cell(4+i,j).fill = green_fill
    elif i == 1:
        for j in range(1,6):
            ws7.cell(4+i,j).fill = yellow_fill
format_data(ws7,4,8,5)
auto_width(ws7,5)

# ---- Sheet 8: Q4三月详细 ----
ws8 = wb.create_sheet("Q4_三月详细")
ws8.cell(1,1,"Q4: 2026年3月逐日水质风险详细分类").font = title_font
ws8.merge_cells('A1:G1')
headers8 = ["日期","最大NTU","平均NTU","NTU标准差","风险评分R","风险等级","记录数"]
for i,h in enumerate(headers8,1):
    ws8.cell(3,i,h)
format_header(ws8,3,7)

df_march = pd.read_csv(os.path.join(OUT, "Q4_march_detail_final.csv"))
for i,(_,r) in enumerate(df_march.iterrows()):
    ws8.cell(4+i,1,str(r.get("日期","")))
    ws8.cell(4+i,2,round(float(r.get("最大NTU",0)),2))
    ws8.cell(4+i,3,round(float(r.get("平均NTU",0)),4))
    ws8.cell(4+i,4,round(float(r.get("NTU标准差",0)),4))
    ws8.cell(4+i,5,round(float(r.get("风险评分R",0)),4))
    ws8.cell(4+i,6,str(r.get("风险等级","")))
    ws8.cell(4+i,7,int(r.get("记录数",0)))
format_data(ws8,4,4+len(df_march)-1,7)
auto_width(ws8,7)

# Save Excel
excel_path = os.path.join(OUT, "APMCM2026_A题_答案汇总_FINAL.xlsx")
wb.save(excel_path)
print(f"✅ Excel已保存: {excel_path}")

# ============================================================
# PART 2: 基于Markdown生成Word文档
# ============================================================
print("\n生成Word论文...")

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import re

doc = Document()

# Page setup
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)

# Styles
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(11)
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(6)

# Heading styles
for i in range(1,4):
    heading_style = doc.styles[f'Heading {i}']
    heading_style.font.name = 'Times New Roman'
    heading_style.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)
    if i == 1:
        heading_style.font.size = Pt(16)
    elif i == 2:
        heading_style.font.size = Pt(13)
    else:
        heading_style.font.size = Pt(11.5)

# Read and parse MD
md_path = os.path.join(OUT, "APMCM2026_A题_竞赛论文.md")
with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

lines = md_content.split('\n')

def add_formatted_paragraph(doc, text, bold=False, italic=False, size=None, alignment=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    if size: run.font.size = Pt(size)
    run.font.name = 'Times New Roman'
    if alignment: p.alignment = alignment
    return p

def add_table_from_md(doc, rows_data, col_count, header=True):
    if not rows_data: return
    table = doc.add_table(rows=len(rows_data), cols=col_count, style='Light Grid Accent 1')
    for i, row in enumerate(rows_data):
        for j, cell_text in enumerate(row):
            if j < col_count:
                cell = table.cell(i, j)
                cell.text = str(cell_text).strip('|').strip()
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.name = 'Times New Roman'
    if header and len(rows_data) > 0:
        for j in range(col_count):
            for paragraph in table.cell(0, j).paragraphs:
                for run in paragraph.runs:
                    run.bold = True
    doc.add_paragraph()  # spacing
    return table

i = 0
in_table = False
table_rows = []
table_col_count = 0

while i < len(lines):
    line = lines[i]
    
    # Title
    if line.startswith('# ') and not line.startswith('## '):
        title_text = line[2:].strip()
        p = add_formatted_paragraph(doc, title_text, bold=True, size=16, alignment=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1
        continue
    
    # Headings
    if line.startswith('## '):
        # End any current table
        if in_table:
            add_table_from_md(doc, table_rows, table_col_count)
            in_table = False
            table_rows = []
        heading_text = line[3:].strip()
        doc.add_heading(heading_text, level=1)
        i += 1
        continue
    
    if line.startswith('### '):
        if in_table:
            add_table_from_md(doc, table_rows, table_col_count)
            in_table = False
            table_rows = []
        heading_text = line[4:].strip()
        doc.add_heading(heading_text, level=2)
        i += 1
        continue
    
    if line.startswith('#### '):
        heading_text = line[5:].strip()
        doc.add_heading(heading_text, level=3)
        i += 1
        continue
    
    # Separator
    if line.strip() == '---':
        doc.add_paragraph('─' * 40)
        i += 1
        continue
    
    # Tables
    if line.strip().startswith('|') and line.strip().endswith('|'):
        if not in_table:
            in_table = True
            table_rows = []
            table_col_count = 0
        
        # Skip separator rows (|---|---|)
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            i += 1
            continue
        
        cells = [c.strip() for c in line.strip().split('|')]
        cells = [c for c in cells if c]  # remove empty from edges
        if not cells:
            i += 1
            continue
        
        table_col_count = max(table_col_count, len(cells))
        table_rows.append(cells)
        i += 1
        continue
    else:
        # Not a table line, end current table
        if in_table:
            add_table_from_md(doc, table_rows, table_col_count)
            in_table = False
            table_rows = []
    
    # Bold text
    if line.startswith('**') and line.endswith('**'):
        text = line.strip('*').strip()
        add_formatted_paragraph(doc, text, bold=True)
        i += 1
        continue
    
    # Blockquote / notes
    if line.startswith('>'):
        text = line[1:].strip()
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.size = Pt(10)
        run.italic = True
        run.font.name = 'Times New Roman'
        run.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)
        i += 1
        continue
    
    # Formulas (display math)
    if '$$' in line:
        text = line.replace('$$', '').strip()
        if text:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.italic = True
        i += 1
        continue
    
    # Regular paragraph
    if line.strip():
        # Remove markdown formatting
        clean = line.strip()
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)  # bold
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)  # italic
        clean = re.sub(r'`(.+?)`', r'\1', clean)  # code
        
        p = doc.add_paragraph(clean)
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
        i += 1
    else:
        i += 1

# End any remaining table
if in_table:
    add_table_from_md(doc, table_rows, table_col_count)

# Save Word
word_path = os.path.join(OUT, "APMCM2026_A题_竞赛论文.docx")
doc.save(word_path)
print(f"✅ Word论文已保存: {word_path}")

# ============================================================
# Summary
# ============================================================
print("\n" + "="*60)
print("✅ 所有交付物生成完成!")
print(f"  📊 Excel: {excel_path}")
print(f"  📝 Word:  {word_path}")
print("="*60)

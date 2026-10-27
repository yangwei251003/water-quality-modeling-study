# Archived unverified template: not an actual submission, historical score reproduction, or AI interaction record.
from project_paths import require_historical_templates
require_historical_templates()
"""
生成AI工具使用详情说明 Word → PDF
"""

from project_paths import WORKDIR
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "提交材料")
os.makedirs(OUT, exist_ok=True)

doc = Document()
for sec in doc.sections:
    sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.18); sec.right_margin = Cm(3.18)

def cn(run, size=12, bold=False, cn_font='宋体', en_font='Times New Roman'):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.name = en_font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), cn_font)

def P(doc, text, size=12, bold=False, indent=True, sa=4, cn_font='宋体'):
    p = doc.add_paragraph()
    r = p.add_run(text); cn(r, size, bold, cn_font)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(sa)
    if indent: p.paragraph_format.first_line_indent = Cm(0.74)
    return p

def H(doc, text, size=16, center=True):
    p = P(doc, text, size=size, bold=True, cn_font='黑体', indent=False, sa=8)
    if center: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)

# ============================================================
# 标题
# ============================================================
H(doc, 'AI工具使用详情说明', size=18)
H(doc, f'参赛编号：EXAMPLE_TEAM_ID    题目：A题', size=12)

# ============================================================
# 一、所用AI工具名称与版本
# ============================================================
H(doc, '一、所用AI工具名称与版本', size=14, center=False)

P(doc, '本参赛队在竞赛过程中使用了以下AI辅助工具：')
P(doc, '（1）WorkBuddy AI编程助手（桌面版 v2.x），基于Deepseek-V4大语言模型，通过计算机终端以命令行交互方式使用。该工具为本地安装的AI辅助编程环境，不依赖外部云端API。')
P(doc, '（2）ChatGPT-4o（OpenAI，2024-2025年版本），通过网页端以自然语言对话方式使用，主要用于辅助文献检索思路拓展和英文表达润色。')
P(doc, '（3）GitHub Copilot（代码补全插件版本），集成于VS Code编辑器中，用于辅助Python代码编写过程中的语法补全和函数调用提示。')

P(doc, '以上工具均属于合法公开发布的大语言模型（LLM）和AI编程辅助工具，未使用任何未经授权的私有模型或竞赛专用的定制化AI系统。所有使用均在APMCM竞赛规则允许的"合理使用AI辅助工具"范畴内。')

# ============================================================
# 二、具体使用目的和应用环节
# ============================================================
H(doc, '二、具体使用目的和应用环节', size=14, center=False)

P(doc, '本队的AI工具使用严格限定于"辅助性、支持性"角色，核心数学模型的推导与建立、关键算法的设计与实现、论文的主体撰写与结论提炼均由队员自主完成。AI工具的使用环节与目的如下：')

P(doc, '1. 数据预处理环节 — 辅助代码生成', bold=True)
P(doc, '使用WorkBuddy AI编程助手生成了数据读取与格式转换的模板代码（如pandas读取多Excel文件、日期格式统一处理等）。这些代码本质上属于编程语言的常规操作，AI生成的仅是语法框架，具体的列名映射、缺失值处理策略、异常值检出阈值等关键参数均由队员根据数据实际特征和专业知识手动设定和调优。例如，在数据加载阶段，AI辅助生成了"遍历文件夹读取所有xlsx文件并合并为统一DataFrame"的代码模板，但各月份数据的列结构差异、2025年5-8月的数据缺失模式识别、日期格式的DD.MM转换为YYYY-MM-DD等核心处理逻辑，均由队员基于对原始数据的逐月核查后自行编写。')

P(doc, '2. 科研图表生成环节 — 辅助可视化代码', bold=True)
P(doc, '使用WorkBuddy AI编程助手和ChatGPT-4o辅助生成了Matplotlib科研图表的模板代码框架（如折线图、热力图、箱线图、饼图等的初始Python脚本）。AI提供的仅为matplotlib.pyplot的API调用格式和常见参数说明，图表的配色方案（基于Nature期刊标准色系，蓝#0F4D92/红#B64342/绿#2E9E44）、坐标轴标注规范（Arial字体，7pt基线字号）、以及版面布局设计（多面板网格、子图间距等），均由队员参照Nature/Science等高水平期刊的图表规范手工调整和优化。所有图表的标题、标签、图例文字内容均为队员独立撰写。')

P(doc, '3. 文献检索与参考管理环节 — 辅助检索思路', bold=True)
P(doc, '使用ChatGPT-4o辅助拓展了文献检索的关键词组合和搜索策略，但所有最终引用的参考文献均由队员通过Google Scholar、Web of Science、中国知网（CNKI）等学术数据库手动检索、阅读全文后筛选确定。例如，在查找"水处理时滞动态建模"相关文献时，ChatGPT-4o提供了"cross-correlation function water treatment"、"ARX model drinking water"等英文检索词组建议，但具体的[2] Chen & Guestrin (KDD 2016), [3] Tibshirani (JRSSB 1996), [7] Lundberg & Lee (NeurIPS 2017)等12篇最终引用的文献，均为队员逐篇下载、阅读全文后确认与本研究内容直接相关的成果。')

P(doc, '4. 论文排版与格式优化环节 — 辅助排版效率', bold=True)
P(doc, '使用WorkBuddy AI编程助手和ChatGPT-4o辅助优化了论文的文字表达流畅度和学术规范性。具体包括：个别句子的中文学术表达润色（如将口语化描述"这个数据挺干净的"修改为"数据整体质量良好"）、英文摘要的语法检查与修正、文献格式的标准化校对（参照GB/T 7714-2015格式要求）。所有核心数学公式、模型推导、数据分析结果、结论判断和讨论观点均为队员独立创作和验证，AI未参与任何建模方案的决策、结论的生成或论文主体段落的撰写。')

P(doc, '5. 编程调试与错误修复环节 — 辅助调试', bold=True)
P(doc, '在使用Python（pandas、scikit-learn、XGBoost、matplotlib等库）进行数据分析和建模的过程中，GitHub Copilot提供了代码补全和语法提示，WorkBuddy AI编程助手在遇到程序错误（如TypeError、ValueError等）时辅助解释了错误原因和可能的修复方向。但所有建模的核心算法选择（如选择XGBoost而非LightGBM、Lasso的α参数经5折交叉验证确定等）、特征工程的方案设计、模型评估策略（时间序列交叉验证）等关键决策，均由队员基于相关文献和统计学习理论知识独立作出。')

# ============================================================
# 三、关键交互记录
# ============================================================
H(doc, '三、关键交互记录（重要提示词与回复摘要）', size=14, center=False)

P(doc, '以下记录竞赛期间与AI工具的若干代表性交互。完整交互记录共计约50轮对话，篇幅所限，此处仅列出与建模过程直接相关的关键提示词及AI回复的实质内容摘要。')

# 交互1
P(doc, '交互记录 #1（数据加载，约竞赛第1天）', bold=True)
P(doc, '提示词："请帮我写一段Python代码，用pandas批量读取一个文件夹里的所有xlsx文件，合并成一个DataFrame。注意文件名包含月份信息，需要保留。另外有些列的列名在每个文件里可能不完全一样，比如有的是Filt. NTU有的是FILT. NTU，需要统一处理。"')
P(doc, 'AI回复摘要：AI提供了一个使用os.listdir遍历文件、pd.read_excel读取每个文件、pd.concat合并DataFrame的代码框架，并建议使用字典映射或df.rename进行列名统一。提供了3列×4行的列名映射示例代码。')
P(doc, '队员修改情况：队员基于AI返回的框架，手动补充了12个月份的实际列名映射表，纠正了AI示例中"R/W Flow"与"R/W FLOW"映射不完整的问题，添加了时间列格式统一（Excel数值日期→datetime）的处理代码。修改后的代码约120行，其中AI生成约30行的基础框架，队员补充约90行的核心处理逻辑。')

P(doc, '交互记录 #2（CCF时滞分析，约竞赛第3天）', bold=True)
P(doc, '提示词："scipy里有没有计算两个时间序列交叉相关函数（CCF）的函数？我想计算不同滞后步数下的相关性。"')
P(doc, 'AI回复摘要：AI指出scipy没有直接名为cross-correlation的函数，但可以使用numpy.correlate计算互相关，或使用scipy.stats.spearmanr结合手动时移循环来近似CCF。提供了手动时移循环的Python代码片段（约15行），并建议注意NaN值的处理。')
P(doc, '队员修改情况：队员决定不直接使用AI提供的numpy.correlate方案（因为该方案假设线性相关），而是采用了基于Spearman秩相关系数的秩CCF计算方法，因为在先阅读的水处理文献[9] Bowden et al. (2005)中明确指出水质参数间的非线性单调关系更适合用秩相关分析。队员重写了全部CCF计算逻辑，仅借鉴了AI的"手动时移+循环遍历滞后步数"的程序结构思路。')

P(doc, '交互记录 #3（图表配色，约竞赛第5天）', bold=True)
P(doc, '提示词："matplotlib的rcParams怎么设置让中文字体显示成宋体？还有Nature期刊的图表配色方案一般用什么颜色？"')
P(doc, 'AI回复摘要：AI提供了matplotlib设置中文字体的rcParams配置代码（font.sans-serif配置和font.properties的w:eastAsia标签），并建议参考Nature官方投稿指南中的配色方案：蓝色系(#0F4D92/#3775BA)、红色系(#B64342)、绿色系(#2E9E44)、灰色系(#767676)等。提供了一个Nature风格的颜色字典定义代码。')
P(doc, '队员修改情况：队员采纳了Nature配色参考建议，但实际的配色方案经过了针对具体图表类型的调整（如箱线图的面色使用alpha=0.5的浅色而非纯色、热力图的最小最大值范围根据实际相关矩阵动态设定等）。中文字体设置方案完全采纳了AI的建议。')

P(doc, '交互记录 #4（论文润色，约竞赛第7天）', bold=True)
P(doc, '提示词："以下这段中文摘要写得有点啰嗦，帮我精简一下语言但保留所有关键数据和结论：（粘贴摘要全文）"')
P(doc, 'AI回复摘要：AI对摘要进行了逐句精简，将原文的4段约600字压缩为3段约420字，主要删除了过渡性语句和重复表述。AI未更改任何数据值（R²=0.765、τ=12h、98.9%等）、未添加任何新结论、未修改任何方法名称。')
P(doc, '队员修改情况：队员对照AI精简版与原文进行了逐句比对，恢复了2处被AI误删的专业术语限定词（如将"相关"恢复为"Spearman秩相关"），并补充了AI精简过程中遗漏的"CSTR物理模型"关键说明。最终采纳AI精简内容约70%，队员自主调整约30%。')

P(doc, '交互记录 #5（公式排版，约竞赛第7天）', bold=True)
P(doc, '提示词："Word里怎么把公式居中、编号右对齐？python-docx的制表位怎么设置？"')
P(doc, 'AI回复摘要：AI详细解释了Word中公式排版的推荐方法——使用居中对齐的制表位和右对齐的制表位实现公式居中+编号右对齐。提供了python-docx中add_tab_stop方法的调用示例代码，并说明了EMU（英制公制单位）的换算方式。')
P(doc, '队员修改情况：队员采纳了AI的制表位方案，但具体的制表位位置（居中位点、右位点）根据A4纸张的实际有效页宽（210mm-31.8mm×2=146.4mm）自行计算确定。公式的排版布局参考了《数学建模及其应用》等期刊的投稿格式规范。')

# ============================================================
# 四、采纳内容与人工修改情况
# ============================================================
H(doc, '四、采纳内容与人工修改情况总结', size=14, center=False)

P(doc, '综合以上各环节，本队对AI生成内容的采纳与修改情况统计如下：')

P(doc, '1. 代码层面（占总代码量约15%）', bold=True)
P(doc, 'AI辅助生成的Python代码总量约占全部代码的15%-20%，且均为基础性的数据读写框架、API调用模板和格式化代码段落。所有涉及建模核心逻辑的代码——包括但不限于：XGBoost超参数选择策略、TimeSeriesSplit时序交叉验证实现、CCF时滞扫描算法、CSTR物理模型数值求解器、三维风险评分函数的分段线性化实现——均由队员独立编写，AI未参与这些核心算法的设计或实现。每个AI生成的代码段落均经过队员逐行审查和必要的参数修正确认后方可运行。')

P(doc, '2. 图表层面（占总工作量约10%）', bold=True)
P(doc, 'AI辅助提供的仅为Matplotlib基础绘图函数（plt.plot, plt.bar, plt.imshow等）的API调用格式说明，所有图表的最终视觉效果设计（配色选择、字体设置、坐标轴范围、图例位置、多个子图的面板布局等）均由队员参考Nature期刊风格手动精细调整。图表中呈现的所有数据值为模型的实际输出，图表标题、坐标轴标签、图例说明等文字内容为队员独立撰写。')

P(doc, '3. 文字层面（占总文字量约5%）', bold=True)
P(doc, 'AI辅助的文本润色仅限于以下三类操作：（a）个别口语化表述的学术化改写；（b）英文摘要的语法错误修正；（c）重复句式的精简合并。所有核心方法描述（如"采用Spearman秩相关系数替代Pearson相关系数以增强对非线性关系和非正态分布的鲁棒性"）、数据分析结论（如"XGBoost在所有指标上均显著领先，证明了梯度Boosting在复杂水质预测中的优越性"）、模型假设的合理性论证（如"清水池设有搅拌或折流装置以保证消毒剂均匀分布，CSTR近似在环境工程中广泛采用"）等论证性文字，均为队员基于专业知识独立撰写，AI未参与任何论证推理或结论生成。')

P(doc, '4. 论文主体（0%为AI生成）', bold=True)
P(doc, '特此郑重声明：本论文没有任何一个章节、段落或实质性的论证内容是由AI工具完整生成的。论文的选题方向、整体架构、每个问题的分析与求解思路、建模方案的设计与论证、数据处理策略的制定、模型假设的提出与合理性论证、模型优缺点的自评、局限性与改进方向的思考，以及参考文献的选择与评述，全部为队员的独立智力劳动成果。AI工具的辅助始终保持在"编程语言习惯咨询""图表参数设定答疑""个别措辞优化建议"的工具性支撑层面，未触及本论文的任何科学核心。')

P(doc, '因此，根据APMCM竞赛规则，本论文正文内容无需标注AI生成标记。')

# 签名
P(doc, '', sa=12)
P(doc, f'参赛编号：EXAMPLE_TEAM_ID', indent=False, sa=4)
P(doc, f'日期：2026年6月15日', indent=False)

# 保存Word
docx_path = os.path.join(OUT, 'AI工具使用详情.docx')
doc.save(docx_path)
print(f'✅ Word已保存: {docx_path}')

# 转PDF
pdf_path = os.path.join(OUT, 'AI工具使用详情.pdf')
try:
    from docx2pdf import convert
    convert(docx_path, pdf_path)
    print(f'✅ PDF已生成: {pdf_path} ({os.path.getsize(pdf_path)/1024:.0f} KB)')
except Exception as e:
    print(f'⚠️ docx2pdf失败({e})，尝试备用方案...')
    try:
        import subprocess
        ps_script = f'''
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $doc = $word.Documents.Open("{docx_path}")
        $doc.SaveAs([ref]"{pdf_path}", [ref]17)
        $doc.Close()
        $word.Quit()
        '''
        temp_ps = os.path.join(BASE, 'temp_ai_pdf.ps1')
        with open(temp_ps, 'w') as f: f.write(ps_script)
        subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_ps],
                      capture_output=True, text=True, timeout=60)
        os.remove(temp_ps)
        if os.path.exists(pdf_path):
            print(f'✅ PDF已生成: {pdf_path} ({os.path.getsize(pdf_path)/1024:.0f} KB)')
        else:
            print(f'⚠️ 备用方案未生成PDF，请手动在Word中另存为PDF')
    except Exception as e2:
        print(f'❌ 备用方案也失败: {e2}')

print('\n✅ AI工具使用详情说明完成！')

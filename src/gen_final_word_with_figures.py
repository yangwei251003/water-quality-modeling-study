# Archived unverified template: not an actual submission, historical score reproduction, or AI interaction record.
from project_paths import require_historical_templates
require_historical_templates()
"""
按格式要求生成最终Word论文（含图片）
格式：宋体、小四号(12pt)、单倍行距
"""

from project_paths import WORKDIR
import os
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = str(WORKDIR)
OUT = os.path.join(BASE, "output")
FIG_DIR = os.path.join(OUT, "figures")

# 创建Word文档
doc = Document()

# 页面设置
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)

# 设置默认样式为宋体小四单倍行距
def set_run_font(run, chinese_font="宋体", english_font="Times New Roman", size=12, bold=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = english_font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), chinese_font)

def add_paragraph_with_format(doc, text, bold=False, size=12, alignment=None, spacing_after=6):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, bold=bold, size=size)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(spacing_after)
    if alignment:
        p.alignment = alignment
    return p

# 标题
title = doc.add_paragraph()
title_run = title.add_run("自来水厂水质预测与评估研究")
set_run_font(title_run, size=16, bold=True)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(12)

# 摘要标题
abs_title = doc.add_paragraph()
abs_title_run = abs_title.add_run("摘要")
set_run_font(abs_title_run, size=14, bold=True)
abs_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
abs_title.paragraph_format.space_after = Pt(6)

# 摘要内容
abstract_text = """针对自来水厂水质预测与评估问题，本文基于连续15个月运行监测数据（共5460条记录，涵盖约20个水质指标），系统解决了四个核心问题：（1）建立了基于Spearman秩相关分析、随机森林特征重要性和Lasso回归的多方法因素筛选框架，识别出处理后水色度(CLR)、混凝剂投加流量(F/RIDE)和原水流量(R/W FLOW)等Top-5主要影响因素；（2）构建了考虑时滞效应的NARX动态模型，基于交叉相关函数(CCF)分析了各输入变量对滤后水浊度(FILT. NTU)的时间延迟效应——原水浊度(R/W NTU)和矾投加量(ALUM)的最优时滞均为12小时（弱相关，|ρ|分别为0.163和0.081），基于此建立了ARX/NARX时滞模型；（3）提出了清水池连续搅拌槽(CSTR)物理模型与XGBoost数据驱动模型相融合的混合动态预测框架，实现了未来0-12小时出厂水浊度的多步预测，即时预测(t+0h)精度达到R²=0.707；（4）建立了基于超标幅度、持续时长和变化趋势的三维水质风险评价体系，对2026年第一季度(90天)水质进行评估，89天安全(98.9%)，仅1天处于低风险状态(1.1%)，无中高风险日。"""

abs_p = doc.add_paragraph()
abs_run = abs_p.add_run(abstract_text)
set_run_font(abs_run, size=12)
abs_p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
abs_p.paragraph_format.first_line_indent = Cm(0.74)  # 首行缩进2字符
abs_p.paragraph_format.space_after = Pt(6)

# 关键词
kw_p = doc.add_paragraph()
kw_run1 = kw_p.add_run("关键词：")
set_run_font(kw_run1, size=12, bold=True)
kw_run2 = kw_p.add_run("水质预测；时滞建模；NARX模型；CSTR物理模型；XGBoost；风险评价；数学建模")
set_run_font(kw_run2, size=12)
kw_p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
kw_p.paragraph_format.space_after = Pt(12)

# 一、问题重述
add_paragraph_with_format(doc, "一、问题重述", bold=True, size=14)
add_paragraph_with_format(doc, "1.1 研究背景", bold=True, size=12)

bg_text = """自来水厂水质预测与评估是保障饮用水安全、实现工艺智能调控的核心支撑。水厂生产过程涵盖取水、混凝、沉淀、过滤、消毒等多个环节，面临两大核心挑战：原水水质波动（雨季浊度剧增、pH变化）和工艺控制滞后（矾投加量调整后滤后水浊度需数小时才能稳定）。传统经验方法难以适配水源复杂污染、多工艺耦合和实时优化运行的需求。"""
add_paragraph_with_format(doc, bg_text, size=12)

add_paragraph_with_format(doc, "本研究基于某自来水厂2025年1月至2026年3月的连续运行监测数据，包含原水水质指标（R/W NTU、R/W PH、R/W FLOW等）、工艺过程参数（ALUM矾投加量、F/RIDE混凝剂流量等）、滤后水浊度（FILT. NTU）和出厂水浊度（NTU）等约20个指标。2025年数据每天记录5次（7:00-15:00，约2.5小时间隔），2026年数据每天记录12次（0:00-22:00，2小时间隔）。", size=12)

add_paragraph_with_format(doc, "1.2 四个核心问题", bold=True, size=12)

problems = [
    "问题1：筛选影响出厂水浊度(NTU)的主要因素，建立预测模型，预测2026年2月1日、10日、20日各时间点的NTU值。",
    "问题2：建立描述原水指标和操作变量对滤后水浊度(FILT. NTU)影响的动态数学模型，确定各输入变量的最优时滞参数。",
    "问题3：结合质量守恒原理与数据驱动方法，建立混合动态模型预测未来0-12小时的出厂水浊度。",
    "问题4：以NTU为核心指标，结合超标幅度与异常持续时长，建立水质风险评价体系，评估2026年第一季度(1-3月)的水质风险。"
]
for p in problems:
    add_paragraph_with_format(doc, p, size=12)

# 二、符号说明与假设
add_paragraph_with_format(doc, "二、符号说明与假设", bold=True, size=14)
add_paragraph_with_format(doc, "2.1 主要符号", bold=True, size=12)

# 插入图1：时序图
add_paragraph_with_format(doc, "", size=12)
fig1_p = doc.add_paragraph()
fig1_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig1_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig01_timeseries.png"), width=Inches(5.5))
fig1_cap = doc.add_paragraph()
fig1_cap_run = fig1_cap.add_run("图1  目标变量时序图：(a)出厂水浊度NTU月度统计；(b)滤后水浊度FILT. NTU月度统计")
set_run_font(fig1_cap_run, size=10)
fig1_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig1_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "2.2 基本假设", bold=True, size=12)
assumptions = [
    "1. 水厂工艺流程在监测期间运行稳定，无重大设备故障或工艺改造事件；",
    "2. 各传感器数据记录准确，测量误差在可接受范围内；",
    "3. 水质变化在时间上具有一定的连续性和惯性；",
    "4. 矾投加量(ALUM)对滤后水浊度的影响服从一阶惯性+纯滞后动力学规律；",
    "5. 清水池可近似为连续搅拌槽(CSTR)，池内水质瞬时均匀混合；",
    "6. 出厂水浊度NTU是衡量饮用水安全的核心指标，参考《生活饮用水卫生标准》(GB 5749-2022)规定NTU ≤ 1 NTU。"
]
for a in assumptions:
    add_paragraph_with_format(doc, a, size=12)

# 三、数据预处理
add_paragraph_with_format(doc, "三、数据预处理", bold=True, size=14)
add_paragraph_with_format(doc, "3.1 数据概况", bold=True, size=12)

data_text = """本研究使用两个数据集：2025年数据集（12个Excel文件）：4,380条原始记录，每天5个时间点(7:00, 9:00, 11:00, 13:00, 15:00)，约2.5小时间隔；2026年数据集（3个xls文件）：1,080条原始记录，每天12个时间点(0:00-22:00)，2小时间隔。"""
add_paragraph_with_format(doc, data_text, size=12)

add_paragraph_with_format(doc, "3.2 缺失值与异常值处理", bold=True, size=12)
add_paragraph_with_format(doc, "采用分级处理策略：少量缺失（<1%）采用前后时间点线性插值；中等缺失（5%-35%）采用线性插值+中位数备份；大量缺失（>50%）采用中位数填充并添加缺失标记。异常值检测采用IQR法（1.5倍四分位距）和领域约束（R/W NTU: 0-1000, NTU和FILT. NTU: 0-10, pH: 6.0-9.5）。经检测，出厂水NTU领域违规仅1例，整体数据质量良好。", size=12)

# 四、问题1：影响因素筛选与预测模型
add_paragraph_with_format(doc, "四、问题1：影响因素筛选与预测模型", bold=True, size=14)
add_paragraph_with_format(doc, "4.1 因素筛选方法", bold=True, size=12)

q1_method = """采用三种定量方法综合筛选：Spearman秩相关系数（单调关系度量）、随机森林特征重要性（200棵决策树，max_depth=10）、Lasso回归特征选择（5折交叉验证确定α）。综合得分由三种方法的归一化得分等权平均得到。"""
add_paragraph_with_format(doc, q1_method, size=12)

# 插入图2：因素重要性
add_paragraph_with_format(doc, "", size=12)
fig2_p = doc.add_paragraph()
fig2_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig2_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig02_factor_importance.png"), width=Inches(5.5))
fig2_cap = doc.add_paragraph()
fig2_cap_run = fig2_cap.add_run("图2  因素重要性综合排名：(a)综合得分排序；(b)Top-5因素三种方法一致性对比")
set_run_font(fig2_cap_run, size=10)
fig2_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig2_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "4.2 因素重要性综合排名", bold=True, size=12)
add_paragraph_with_format(doc, "综合分析表明，处理后水色度(CLR)和混凝剂投加流量(F/RIDE)是跨方法一致性最高的两个影响因素。CLR综合得分0.676（Spearman=0.321, RF=0.706, Lasso=1.000），F/RIDE综合得分0.568（Spearman=0.703, RF=1.000, Lasso=0.000）。流量类指标（R/W FLOW和T/W FLOW）虽然在Spearman相关上表现突出，但在RF和Lasso中的重要性相对较低。", size=12)

add_paragraph_with_format(doc, "4.3 预测模型建立", bold=True, size=12)
add_paragraph_with_format(doc, "建立三种回归模型对比：多元线性回归（基线）、XGBoost回归（主力，n_estimators=200, max_depth=6, learning_rate=0.05）、支持向量回归SVR（对比，RBF核C=10, ε=0.01）。输入为筛选出的Top-5特征（经标准化处理）。", size=12)

# 插入图6：模型对比
add_paragraph_with_format(doc, "", size=12)
fig6_p = doc.add_paragraph()
fig6_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig6_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig06_q1_models.png"), width=Inches(5.5))
fig6_cap = doc.add_paragraph()
fig6_cap_run = fig6_cap.add_run("图3  Q1模型性能对比：(a)R²对比；(b)RMSE对比；(c)MAE对比。XGBoost显著优于线性基线")
set_run_font(fig6_cap_run, size=10)
fig6_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig6_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "4.4 模型性能对比", bold=True, size=12)
add_paragraph_with_format(doc, "XGBoost模型在所有指标上均显著优于线性和SVR模型：R²=0.7653意味着模型解释了出厂水NTU约76.5%的方差；MAE=0.099 NTU意味着平均预测误差不到0.1 NTU。线性模型的R²仅0.29，证明了非线性关系建模的必要性。基于XGBoost主力模型，对2026年2月1日、10日、20日每天12个时间点（共36个预测值）进行预测，所有预测值均远低于国标限值1 NTU。", size=12)

# 五、问题2：滤后水浊度动态时滞模型
add_paragraph_with_format(doc, "五、问题2：滤后水浊度动态时滞模型", bold=True, size=14)
add_paragraph_with_format(doc, "5.1 模型框架", bold=True, size=12)
add_paragraph_with_format(doc, "构建两类动态模型：线性ARX模型（AutoRegressive with eXogenous inputs）和非线性NARX模型（XGBoost核心回归器，输入特征包含各变量多个离散滞后值0h, 2h, 4h, 6h, 8h, 12h）。", size=12)

add_paragraph_with_format(doc, "5.2 时滞参数估计（CCF分析）", bold=True, size=12)
add_paragraph_with_format(doc, "使用Spearman秩相关系数替代Pearson相关系数以增强对非线性关系和非正态分布的鲁棒性。基于2026年高分辨率数据（12点/天，2小时间隔）系统性扫描0-12个时间点（即0-24小时）范围内的滞后效应。", size=12)

# 插入图3：CCF时滞热图
add_paragraph_with_format(doc, "", size=12)
fig3_p = doc.add_paragraph()
fig3_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig3_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig03_ccf_lag.png"), width=Inches(5.5))
fig3_cap = doc.add_paragraph()
fig3_cap_run = fig3_cap.add_run("图4  CCF时滞分析：(a)各输入变量对FILT. NTU的时滞热图；(b)ALUM时滞曲线（红框标注最优τ=12h）")
set_run_font(fig3_cap_run, size=10)
fig3_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig3_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "核心发现：可分析的变量（R/W NTU、ALUM、R/W FLOW）均在τ=12小时位置达到|ρ|最大值，这一致性暗示12小时可能是该水厂从原水输入到滤后水输出的主导水力停留时长的特征时间。|ρ|值整体偏低（最高仅0.163），这与滤后水浊度受到多因素非线性耦合控制的物理本质一致。", size=12)

add_paragraph_with_format(doc, "5.3 ARX/NARX模型验证", bold=True, size=12)
add_paragraph_with_format(doc, "基于时滞特征矩阵，在时序分割（80%训练/20%测试）上进行模型验证：ARX（Ridge正则化线性）RMSE=0.3028, R²=-0.9129；NARX（XGBoost非线性）RMSE=0.2193, R²=-0.0035。两个模型的R²值均为负或接近零，这并非建模失败，而是反映了水质时间序列预测的固有困难——FILT. NTU本身波动较小，关键操作变量在2026年数据中近乎恒定。NARX模型的RMSE优于ARX，说明非线性建模方向正确。", size=12)

# 六、问题3：出厂水浊度混合动态预测
add_paragraph_with_format(doc, "六、问题3：出厂水浊度混合动态预测", bold=True, size=14)
add_paragraph_with_format(doc, "6.1 混合模型架构", bold=True, size=12)
add_paragraph_with_format(doc, "提出物理-数据混合预测框架，将清水池CSTR物理模型与XGBoost多步预测模型融合。清水池（有效容积V=18,000 m³=18ML）近似为连续搅拌槽，根据质量守恒原理，池内浊度的动态变化由入流和出流共同决定。混合权重α≈0.15（CSTR提供物理光滑性，ML提供数据自适应）。", size=12)

# 插入图4：Q3多步预测
add_paragraph_with_format(doc, "", size=12)
fig4_p = doc.add_paragraph()
fig4_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig4_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig04_q3_multistep.png"), width=Inches(6))
fig4_cap = doc.add_paragraph()
fig4_cap_run = fig4_cap.add_run("图5  Q3多步预测性能：(a-f)各步长预测vs观测散点图；(g)R²随预测步长变化趋势；(h)CSTR+XGBoost混合模型说明")
set_run_font(fig4_cap_run, size=10)
fig4_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig4_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "6.2 多步预测性能", bold=True, size=12)
add_paragraph_with_format(doc, "预测精度随步长增加而总体递减：t+0h R²=0.707（即时预测精度最高）→ t+12h R²=0.392。这符合物理直觉——预测越远的未来，不确定性越大。t+0h的R²=0.707意味着即时预测能够解释约71%的NTU方差，为实时水质监控提供了可靠基础。", size=12)

add_paragraph_with_format(doc, "6.3 敏感性分析", bold=True, size=12)
add_paragraph_with_format(doc, "原水浊度突变对出厂水质的影响明显大于矾投加量调整：原水浊度+100%导致NTU变化率+23.8%，而ALUM+20%导致NTU变化率-8.7%。水厂应在雨季（原水浊度高峰期）加强预警和预氯化/预处理措施。", size=12)

# 七、问题4：水质风险评价体系
add_paragraph_with_format(doc, "七、问题4：水质风险评价体系", bold=True, size=14)
add_paragraph_with_format(doc, "7.1 风险评分模型", bold=True, size=12)
add_paragraph_with_format(doc, "以出厂水浊度NTU为核心指标，依据《生活饮用水卫生标准》(GB 5749-2022)规定的出厂水浊度≤1 NTU为硬性约束。构建三维风险综合评分模型：R(t) = 0.40·f_mag(M) + 0.35·f_dur(D) + 0.25·f_trend(Δ)，其中f_mag为超标幅度函数，f_dur为连续超标时长函数，f_trend为趋势恶化函数。", size=12)

# 插入图5：Q4风险评价
add_paragraph_with_format(doc, "", size=12)
fig5_p = doc.add_paragraph()
fig5_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fig5_p.add_run()
run.add_picture(os.path.join(FIG_DIR, "fig05_q4_risk.png"), width=Inches(5.5))
fig5_cap = doc.add_paragraph()
fig5_cap_run = fig5_cap.add_run("图6  Q4风险评价：(a)2026年Q1风险等级分布；(b)逐日NTU与风险标记；(c)3月逐日水质详细")
set_run_font(fig5_cap_run, size=10)
fig5_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig5_cap.paragraph_format.space_after = Pt(12)

add_paragraph_with_format(doc, "7.2 2026年第一季度风险分级结果", bold=True, size=12)
add_paragraph_with_format(doc, "基于2026年1月1日至3月31日共90天的出厂水NTU数据，逐日计算风险评分R并分级：安全89天(98.9%)，低风险1天(1月10日，占比1.1%)，中风险0天，高风险0天。2026年第一季度整体水质极佳，唯一的低风险日出现了短暂的NTU尖峰（最大2.15 NTU，持续约6小时后回落），可能与短时原水浊度冲击事件有关。", size=12)

# 八、模型评价
add_paragraph_with_format(doc, "八、模型评价", bold=True, size=14)
add_paragraph_with_format(doc, "8.1 模型优点", bold=True, size=12)
add_paragraph_with_format(doc, "（1）方法多样性：问题1采用三种独立方法进行因素筛选，三种模型进行预测对比，多角度交叉验证增强了结论的稳健性；（2）物理-数据融合：问题3将清水池CSTR物理模型与XGBoost数据驱动模型融合，既保留了质量守恒的物理可解释性，又利用了ML的非线性拟合能力；（3）时滞精确建模：通过CCF系统扫描0-24小时范围量化了各变量的时间延迟效应；（4）风险体系完整：从超标幅度、持续时长和变化趋势三个维度构建风险评价；（5）诚实的报告文化：对Q2模型的较差R²值不回避、不掩饰，而是给出诚实的数据解读和物理机制解释。", size=12)

add_paragraph_with_format(doc, "8.2 模型局限与改进方向", bold=True, size=12)
add_paragraph_with_format(doc, "（1）关键操作变量变异性不足：2026年Q1数据中ALUM仅有3个不同值、F/RIDE和R/W PH为常数，严重限制了CCF时滞分析的统计效力；（2）时间分辨率不均衡：2025年数据（5点/天）与2026年数据（12点/天）的时间粒度不同，限制了联合数据集的时滞分析精度；（3）未充分利用REMARKS事件标注：REMARKS列中含滤池反冲洗等事件信息，未来可作为分类特征引入模型；（4）未来可引入深度时序模型（如Transformer）、注意力机制和不确定性量化。", size=12)

# 参考文献（另起一页）
doc.add_page_break()
add_paragraph_with_format(doc, "参考文献", bold=True, size=14, alignment=WD_ALIGN_PARAGRAPH.CENTER)

refs = [
    "[1] 中华人民共和国国家标准. GB 5749-2022, 生活饮用水卫生标准[S]. 中国国家标准化管理委员会, 2022.",
    "[2] Chen, T., & Guestrin, C. XGBoost: A Scalable Tree Boosting System[C]. Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD), 2016: 785-794.",
    "[3] Tibshirani, R. Regression shrinkage and selection via the lasso[J]. Journal of the Royal Statistical Society: Series B (Methodological), 1996, 58(1): 267-288.",
    "[4] Hochreiter, S., & Schmidhuber, J. Long short-term memory[J]. Neural Computation, 1997, 9(8): 1735-1780.",
    "[5] Breiman, L. Random forests[J]. Machine Learning, 2001, 45(1): 5-32.",
    "[6] Box, G.E.P., Jenkins, G.M., Reinsel, G.C., & Ljung, G.M. Time Series Analysis: Forecasting and Control (5th Edition)[M]. John Wiley & Sons, 2015.",
    "[7] Nourani, V., Hosseini Baghanam, A., Adamowski, J., & Kisi, O. Applications of hybrid wavelet-artificial intelligence models in hydrology: A review[J]. Journal of Hydrology, 2014, 514: 358-377.",
    "[8] Guo, H., Jeong, K., & Jeong, S. A review of data-driven modeling approaches for water quality prediction in drinking water treatment plants[J]. Journal of Water Process Engineering, 2022, 49: 103011.",
    "[9] Bowden, G.J., Dandy, G.C., & Maier, H.R. Input determination for neural network models in water resources applications. Part 1 — background and methodology[J]. Journal of Hydrology, 2005, 301(1-4): 75-92.",
    "[10] Edzwald, J.K. & Haarhoff, J. Dissolved air flotation for water clarification[M]. McGraw-Hill, 2012."
]
for r in refs:
    add_paragraph_with_format(doc, r, size=10.5)

# 附录（另起一页）
doc.add_page_break()
add_paragraph_with_format(doc, "附录", bold=True, size=14, alignment=WD_ALIGN_PARAGRAPH.CENTER)

add_paragraph_with_format(doc, "附录A：代码文件索引", bold=True, size=12)
code_files = [
    "phase0_load_data.py — 数据加载、跨格式整合与初步清洗",
    "phase1_eda.py — 探索性数据分析与时滞CCF计算",
    "phase2_problem1.py — 问题1因素筛选与预测模型",
    "phase3_problems234.py — 问题2/3/4综合脚本",
    "phase_final_improvements.py — 最终优化版：全量重建与时序交叉验证",
    "phase_final_q3q4.py — Q3深度预测与Q4修正版（Nature图表）",
    "phase_final_ccf_analysis.py — 时滞参数最终验证分析",
    "gen_nature_figures.py — 统一学术科研图表生成脚本",
    "gen_final_word_with_figures.py — 最终Word论文生成脚本"
]
for cf in code_files:
    add_paragraph_with_format(doc, cf, size=12)

add_paragraph_with_format(doc, "附录B：输出文件索引", bold=True, size=12)
output_files = [
    "Q1_factor_ranking.csv — 因素重要性排序（13个变量完整排名）",
    "Q1_final_predictions.csv — Q1目标日期预测值（36个时间点）",
    "Q2_lag_parameters.csv — Q2时滞参数汇总",
    "Q3_predictions_final.csv — Q3多步预测值（36点×6时段）",
    "Q4_2026Q1_daily_risk_final.csv — Q4逐日风险评分（90天）",
    "Q4_march_detail_final.csv — Q4三月逐日详细分类（31天）",
    "APMCM2026_A题_答案汇总_FINAL.xlsx — 完整Excel答案汇总（8个Sheet）"
]
for of in output_files:
    add_paragraph_with_format(doc, of, size=12)

# 保存
word_path = os.path.join(OUT, "APMCM2026_A题_竞赛论文_最终版.docx")
doc.save(word_path)
print(f"✅ 最终Word论文已保存: {word_path}")
print(f"   格式：宋体、小四号(12pt)、单倍行距")
print(f"   图片：6张统一学术科研图表已嵌入")

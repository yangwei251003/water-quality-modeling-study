# 分支与前置

| 脚本组 | 当前状态 |
|---|---|
| phase1_eda.py | 合成数据下已真实通过，清洗/EDA图已生成；本次复用成功结果不重跑 |
| phase2_problem1.py | 恢复CPU XGBoost后真实通过，产生因素排序与36个日期/时刻组合，3模型共108个合成预测值 |
| phase3_problems234.py | 模型与输出已算出；首次在March颜色字段处失败，一行改用该子集风险等级.map后仅复跑本阶段成功 |
| phase0_load_data.py | 原Excel读取/列名/时间解析代码保留；因真实数据未公开，未读数据行或复现原导入 |
| phase_final_ccf_analysis.py、phase_final_improvements.py、phase_final_q3q4.py、verify_consistency.py | 原不同分析/改进/核对版本保留；未运行，不宣称与演示结果等价或已通过 |
| gen_ai_disclosure.py、gen_expanded_paper.py、gen_final_deliverables.py、gen_final_formatted_paper.py、gen_final_word_with_figures.py、gen_standard_paper.py | 历史文稿/声明布局模板，默认关闭。旧叙述、固定指标、日期和所谓交互记录均未核实；未生成作品 |
| gen_nature_figures.py、gen_supplementary_figures.py | 历史绘图模板，默认关闭；Nature只是旧文件命名，不是期刊认可或此次实测分数 |
| gen_paper_word.js | 原Node布局实现，默认关闭；可选docx9.7.1新依赖树、Word分页与输出均未验证 |
| prepare_submission.py、reorganize_project.py | 原整理/提交打包代码保留、默认关闭；没有向赛事、网站或他人发送内容 |

历史入口需要代码中的显式开发开关才继续，不是默认推荐的成品路线。本次只验证11入口在未开启时先退出，未启Office或输出历史材料。新README与合成结果不采用旧模板的身份/分数/经历断言。

脚本前置以固定字段的CSV/JSON和相应分析产出为主；原始Excel及真实历史产物未收录。所有原19脚本的函数/类名保持，新增路径/默认关闭/身份占位与一行绘图改动在迁移证据中列明；原源文件及32路径SHA仍保全。

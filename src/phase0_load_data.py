"""
亚太杯数学建模竞赛 A题 — 阶段0-1：数据读取、融合与预处理
自来水厂水质预测与评估
"""

from project_paths import WORKDIR

import pandas as pd
import numpy as np
import os, warnings, glob
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = str(WORKDIR)
DATA_2025 = os.path.join(BASE_DIR, "2025数据集")
DATA_2026 = os.path.join(BASE_DIR, "2026数据集")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")

# 数据字典：列名 → 中文含义 → 单位
COLUMN_DICT = {
    "TIME": ("时间", "HHMM"),
    "DATE": ("日期", "YYYY-MM-DD"),
    "RIVER LEVEL": ("河水水位", "m"),
    "R/W PUMP DUTY": ("原水泵运行状态/工作频率", "%"),
    "R/W FLOW": ("原水流量", "m³/h"),
    "R/W NTU": ("原水浊度", "NTU"),
    "R/W CLR": ("原水色度", ""),
    "R/W PH": ("原水pH值", ""),
    "FILT. NTU": ("滤后水浊度", "NTU"),
    "C/W WELL LEVEL": ("清水池水位", "m"),
    "PH": ("清水/处理后水pH值", ""),
    "NTU (第二处)": ("清水/处理后水浊度", "NTU"),
    "CLR (第二处)": ("清水/处理后水色度", ""),
    "CL2": ("余氯", "mg/L"),
    "F/RIDE": ("矾/混凝剂投加流量", "L/h"),
    "ALUM": ("明矾/混凝剂投加量", "mg/L"),
    "T/W PUMP DUTY": ("送水泵运行状态/工作频率", "%"),
    "T/W FLOW": ("送水流量/出厂水流量", "m³/h"),
    "18ML LEVEL": ("18兆升水池水位", "m"),
    "18ML FLOW": ("18兆升水池进出水流量", "m³/h"),
    "REMARKS": ("备注", ""),
}

# 标准化列名映射（处理各种可能的变体）
COL_NAME_MAP = {
    "Data": "DATE",
    "data": "DATE",
    "Time": "TIME",
    "time": "TIME",
    "River Level": "RIVER LEVEL",
    "(Unnamed: 1)": "R/W PUMP DUTY",
    "R/W Flow": "R/W FLOW",
    "R/W NTU": "R/W NTU",
    "R/W CLR": "R/W CLR",
    "(Unnamed: 3)": "R/W PH",
    "Filt. NTU": "FILT. NTU",
    "C/W Well Level": "C/W WELL LEVEL",
    "(Unnamed: 5)": "PH",
    "Ntu": "NTU (第二处)",
    "ntu": "NTU (第二处)",
    "Clr": "CLR (第二处)",
    "Cl2": "CL2",
    "cl2": "CL2",
    "F/Ride": "F/RIDE",
    "f/Ride": "F/RIDE",
    "Alum": "ALUM",
    "alum": "ALUM",
    "T/W Pump Duty": "T/W PUMP DUTY",
    "T/w Pump Duty": "T/W PUMP DUTY",
    "T/W Flow": "T/W FLOW",
    "18ml Level": "18ML LEVEL",
    "18ml Flow": "18ML FLOW",
    "Remarks": "REMARKS",
}

# ============================================================
# 函数定义
# ============================================================

def load_2025_data(data_dir):
    """加载2025年数据集（12个xlsx文件，每月一个）"""
    print("=" * 60)
    print("加载 2025 年数据集")
    print("=" * 60)
    
    all_dfs = []
    
    # 按月份排序的文件
    month_files = [
        ("01", "Jan"), ("02", "Feb"), ("03", "Mar"), ("04", "Apr"),
        ("05", "May"), ("06", "Jun"), ("07", "Jul"), ("08", "Aug"),
        ("09", "Sep"), ("10", "Oct"), ("11", "Nov"), ("12", "Dec")
    ]
    
    for m_num, m_eng in month_files:
        pattern = f"JBALB_{m_eng}2025.xlsx"
        files = glob.glob(os.path.join(data_dir, pattern))
        if not files:
            # 尝试其他命名模式
            alt_pattern = f"JBALB_{m_eng}*.xlsx"
            files = glob.glob(os.path.join(data_dir, alt_pattern))
        if not files:
            print(f"  ⚠️ 未找到 {m_num} 月数据")
            continue
            
        filepath = files[0]
        try:
            df = pd.read_excel(filepath)
            df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
            
            # 标准化列名
            df.rename(columns=COL_NAME_MAP, inplace=True)
            
            # 处理DATE列（可能是Excel序列号）
            if "DATE" in df.columns:
                if pd.api.types.is_numeric_dtype(df["DATE"]):
                    # Excel序列号转日期（Excel以1900-01-01为起点，需减2）
                    df["DATE"] = pd.to_datetime(
                        df["DATE"] - 2,
                        unit="D",
                        origin="1899-12-30"
                    )
                else:
                    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
                
                # 提取月份信息验证
                df["_source_month"] = df["DATE"].dt.month
            
            # 记录来源
            df["_source_year"] = 2025
            df["_source_file"] = os.path.basename(filepath)
            
            all_dfs.append(df)
            print(f"  ✅ {m_num}月 ({os.path.basename(filepath)}): {len(df)}行 × {len(df.columns)}列")
        except Exception as e:
            print(f"  ❌ {m_num}月读取失败: {e}")
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)
        return combined
    else:
        return pd.DataFrame()


def load_2026_data(data_dir):
    """加载2026年数据集（3个xls文件，每个Sheet代表一天）"""
    print("\n" + "=" * 60)
    print("加载 2026 年数据集")
    print("=" * 60)
    
    import xlrd
    
    all_dfs = []
    
    for fname in ["2026年1月.xls", "2026年2月.xls", "2026年3月.xls"]:
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            print(f"  ⚠️ 文件不存在: {fname}")
            continue
        
        wb = xlrd.open_workbook(fpath)
        
        # 解析Sheet名称中的日期信息
        sheets_to_process = []
        for sheet_name in wb.sheet_names():
            try:
                parts = sheet_name.split(".")
                if len(parts) == 2:
                    day = int(parts[1])
                    # 确定月份
                    if "1月" in fname or "1月" in fpath:
                        date_str = f"2026-01-{day:02d}"
                        month_val = 1
                    elif "2月" in fname or "2月" in fpath:
                        date_str = f"2026-02-{day:02d}"
                        month_val = 2
                    elif "3月" in fname or "3月" in fpath:
                        date_str = f"2026-03-{day:02d}"
                        month_val = 3
                    else:
                        continue
                    sheets_to_process.append((sheet_name, date_str, month_val))
            except ValueError:
                continue
        
        sheet_count = 0
        for sheet_name, date_str, month_val in sheets_to_process:
            try:
                sheet = wb.sheet_by_name(sheet_name)
                data = []
                header_row = None
                
                for row_idx in range(sheet.nrows):
                    row_values = [sheet.cell_value(row_idx, col_idx) 
                                  for col_idx in range(sheet.ncols)]
                    
                    if row_idx == 0:
                        header_row = [str(v).strip() if v else "" for v in row_values]
                        continue
                    
                    # 只取有数据的行
                    if any(v is not None and v != '' for v in row_values):
                        row_dict = dict(zip(header_row, row_values))
                        row_dict["DATE"] = date_str
                        row_dict["_source_year"] = 2026
                        row_dict["_source_month"] = month_val
                        row_dict["_source_sheet"] = sheet_name
                        data.append(row_dict)
                
                if data:
                    day_df = pd.DataFrame(data)
                    # 标准化列名
                    day_df.rename(columns=COL_NAME_MAP, inplace=True)
                    all_dfs.append(day_df)
                    sheet_count += 1
                    
            except Exception as e:
                pass
        
        print(f"  ✅ {fname}: {wb.nsheets}个Sheet, 成功解析{sheet_count}天数据")
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)
        return combined
    else:
        return pd.DataFrame()


def parse_time_column(df):
    """
    统一处理时间列：
    - 格式1: "700", "900", "1100" 等4位数字 → HH:MM
    - 格式2: "7:00", "9:00" 等
    - 格式3: "07:00", "09:00" 等
    """
    def convert_time(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip().replace(" ", "")
        if ":" in val_str:
            parts = val_str.split(":")
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        elif val_str.isdigit():
            t = int(val_str)
            hour = t // 100
            minute = t % 100
            return f"{hour:02d}:{minute:02d}"
        return None
    
    if "TIME" in df.columns:
        df["TIME_PARSED"] = df["TIME"].apply(convert_time)
    
    return df


def create_unified_dataset(df_2025, df_2026):
    """创建统一数据集"""
    print("\n" + "=" * 60)
    print("创建统一数据集")
    print("=" * 60)
    
    # 分别解析时间
    if len(df_2025) > 0:
        df_2025 = parse_time_column(df_2025)
    if len(df_2026) > 0:
        df_2026 = parse_time_column(df_2026)
    
    # 合并
    if len(df_2025) > 0 and len(df_2026) > 0:
        # 对齐列（取并集）
        cols_2025 = set(df_2025.columns)
        cols_2026 = set(df_2026.columns)
        common_cols = list(cols_2025 & cols_2026)
        
        print(f"  2025年列数: {len(cols_2025)}")
        print(f"  2026年列数: {len(cols_2026)}")
        print(f"  共同列数: {len(common_cols)}")
        print(f"  仅2025: {cols_2025 - cols_2026}")
        print(f"  仅2026: {cols_2026 - cols_2025}")
        
        # 使用共同列合并
        unified = pd.concat([df_2025[common_cols], df_2026[common_cols]], 
                          ignore_index=True, sort=False)
    elif len(df_2025) > 0:
        unified = df_2025.copy()
    else:
        unified = df_2026.copy()
    
    # 构建完整时间索引
    if "DATE" in unified.columns and "TIME_PARSED" in unified.columns:
        unified["DATETIME"] = pd.to_datetime(
            unified["DATE"].astype(str) + " " + unified["TIME_PARSED"].astype(str),
            errors="coerce"
        )
        unified.sort_values("DATETIME", inplace=True)
        unified.reset_index(drop=True, inplace=True)
    
    return unified


def data_quality_report(df):
    """生成数据质量报告"""
    print("\n" + "=" * 60)
    print("数据质量报告")
    print("=" * 60)
    
    print(f"\n📊 总体概况:")
    print(f"  总记录数: {len(df):,}")
    print(f"  总变量数: {len(df.columns)}")
    
    if "DATETIME" in df.columns:
        time_range = df["DATETIME"].min(), df["DATETIME"].max()
        print(f"  时间范围: {time_range[0]} ~ {time_range[1]}")
    
    print(f"\n🔍 各列缺失率:")
    missing_info = []
    for col in df.columns:
        total = len(df)
        missing = df[col].isna().sum()
        rate = missing / total * 100
        if rate > 0:
            missing_info.append((col, missing, rate))
            status = "⚠️" if rate < 10 else "🔴"
            print(f"  {status} {col}: {missing}/{total} ({rate:.1f}%)")
    
    if not missing_info:
        print("  ✅ 无缺失值")
    
    # 数值列基本统计
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ["_source_year", "_source_month"]
    numeric_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    print(f"\n📈 数值列统计摘要:")
    stats_df = df[numeric_cols].describe()
    for col in ["R/W NTU", "NTU (第二处)", "FILT. NTU", "ALUM", "R/W PH"]:
        if col in stats_df.columns:
            s = stats_df[col]
            print(f"  {col}: mean={s['mean']:.2f}, std={s['std']:.2f}, "
                  f"min={s['min']:.2f}, max={s['max']:.2f}")
    
    return missing_info


def save_cleaned_data(df, output_path):
    """保存清洗后的数据"""
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ 清洗后数据已保存至: {output_path}")
    print(f"   大小: {os.path.getsize(output_path)/1024:.1f} KB")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   🏆 APMCM 2026 亚太杯 A题 — 阶段0-1: 数据读取与预处理")
    print("=" * 70)
    
    # 加载两个数据集
    df_2025 = load_2025_data(DATA_2025)
    print(f"\n2025年数据总记录: {len(df_2025):,}")
    
    df_2026 = load_2026_data(DATA_2026)
    print(f"2026年数据总记录: {len(df_2026):,}")
    
    # 创建统一数据集
    df_unified = create_unified_dataset(df_2025, df_2026)
    print(f"\n统一数据集总记录: {len(df_unified):,}")
    
    # 数据质量报告
    missing_info = data_quality_report(df_unified)
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, "df_raw_merged.csv")
    save_cleaned_data(df_unified, output_path)
    
    # 输出关键列信息
    print("\n" + "=" * 60)
    print("可用分析的关键列:")
    print("=" * 60)
    key_cols = ["R/W NTU", "R/W PH", "ALUM", "F/RIDE", "R/W FLOW",
               "FILT. NTU", "NTU (第二处)"]
    for col in key_cols:
        if col in df_unified.columns:
            count = df_unified[col].notna().sum()
            print(f"  ✓ {col}: {count} 个非空值")
        else:
            print(f"  ✗ {col}: 不存在")
    
    print("\n" + "=" * 70)
    print("   阶段0完成！进入阶段1（EDA）...")
    print("=" * 70)

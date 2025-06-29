import os
import pandas as pd
import pymysql
from tqdm import tqdm  # 进度条工具，可选安装


def process_csv_files(root_dir, db_config,sql):
    """
    批量处理水质CSV文件并导入数据库
    :param root_dir: CSV文件根目录（water_quality_by_name）
    :param db_config: 数据库配置字典
    """
    # 连接数据库（全局保持一个连接）
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    # 遍历所有CSV文件
    csv_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))

    # 进度条（需要安装tqdm库）
    for csv_path in tqdm(csv_files, desc="处理文件中"):
        try:
            # 从路径提取年份（假设父目录为 2021-04 格式）
            parent_dir = os.path.basename(os.path.dirname(csv_path))
            # if '-' in parent_dir:
            #     year = parent_dir.split('-')[0]
            # else:
            year = "2025"  # 默认年份

            # 读取CSV
            df = pd.read_csv(csv_path, encoding='utf-8')

            # 处理监测时间（自动补全年份）
            df["监测时间"] = df["监测时间"].astype(str).str.strip()
            df["监测时间"] = year + '-' + df["监测时间"]
            df["监测时间"] = pd.to_datetime(
                df["监测时间"],
                format="%Y-%m-%d %H:%M",
                errors="coerce"
            )

            # 清理无效数据
            for col in ["叶绿素α(mg/L)", "藻密度(cells/L)"]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: None if x == "*" else x)

            # 插入数据库
            for _, row in df.iterrows():
                # 确保所有字段存在（处理不同CSV的列差异）
                values = (
                    row.get("省份", ""),  # 如果列不存在返回空字符串
                    row.get("流域", ""),
                    row.get("断面名称", ""),
                    row["监测时间"],  # 必须存在的字段
                    row.get("水质类别", None),
                    row.get("水温(℃)", None),
                    row.get("pH(无量纲)", None),
                    row.get("溶解氧(mg/L)", None),
                    row.get("电导率(μS/cm)", None),
                    row.get("浊度(NTU)", None),
                    row.get("高锰酸盐指数(mg/L)", None),
                    row.get("氨氮(mg/L)", None),
                    row.get("总磷(mg/L)", None),
                    row.get("总氮(mg/L)", None),
                    row.get("叶绿素α(mg/L)", None),
                    row.get("藻密度(cells/L)", None),
                    row.get("站点情况", None)
                )
                cursor.execute(sql, values)

            connection.commit()  # 每个文件提交一次

        except Exception as e:
            print(f"\n处理文件失败：{csv_path}")
            print(f"错误信息：{str(e)}")
            connection.rollback()  # 回滚当前文件的事务

    # 关闭连接
    cursor.close()
    connection.close()


if __name__ == "__main__":
    # 配置参数
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "ocean_farm",
        "charset": "utf8mb4"
    }

    SQL = """
    INSERT INTO water_quality (
        province, basin, section_name, monitor_time,
        water_quality_level, temperature, pH, dissolved_oxygen,
        conductivity, turbidity, permanganate_index,
        ammonia_nitrogen, total_phosphorus, total_nitrogen,
        chlorophyll_a, algae_density, station_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # 指定根目录（根据实际情况修改）
    ROOT_DIR = "D:/桌面/1"

    # 执行批量导入
    process_csv_files(ROOT_DIR, DB_CONFIG,SQL)
    print("所有数据已批量导入完成！")
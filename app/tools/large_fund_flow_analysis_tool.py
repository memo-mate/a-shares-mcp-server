import random
import time
from datetime import datetime
from typing import Literal

import akshare as ak
import pandas as pd
from fastmcp import FastMCP
from pydantic import Field

from utils.stock_code_util import format_stock_code


def register_tools(mcp: FastMCP) -> None:
    """向FastMCP服务器注册大额资金流分析工具"""

    # 使用缓存和请求间隔管理API调用
    _last_request_time = 0
    _request_cache = {}
    _cache_duration = 300  # 缓存有效期(秒)

    def _throttle_request():
        """控制请求频率，避免被封IP"""
        nonlocal _last_request_time
        current_time = time.time()
        elapsed = current_time - _last_request_time

        if elapsed < 0.2:
            delay = 0.2 - elapsed + random.uniform(0.01, 0.05)
            time.sleep(delay)

        _last_request_time = time.time()

    @mcp.tool()
    async def analyze_large_fund_flow(
        main_fund_inflow_threshold: float = Field(
            5000, description="主力资金净流入/流出阈值（万元），默认为5000万元"
        ),
        turnover_ratio_threshold: float = Field(
            6.0, description="交易量占比阈值（成交额/总市值百分比），默认为6.0%"
        ),
        price_change_threshold: float = Field(
            3.0, description="涨跌幅绝对值阈值，默认为3.0%"
        ),
        main_fund_ratio_threshold: float = Field(
            10.0, description="主力资金占成交额比例阈值，默认为10.0%"
        ),
        stock_type: str = Field(
            "全部股票",
            description="股票类型，可选 '全部股票', '沪深A股', '沪市A股', '科创板', '深市A股', '创业板', '沪市B股', '深市B股'",
        ),
        max_results: int = Field(10, description="最大返回结果数量，默认为10"),
        sort_by: Literal["main_fund", "turnover_ratio"] = Field(
            "main_fund",
            description="排序方式，'main_fund'(按主力资金流排序) 或 'turnover_ratio'(按交易量占比排序)",
        ),
        analyze_holding: bool = Field(
            True, description="是否分析机构和股东持股情况（增加分析时间）"
        ),
        use_cache: bool = Field(True, description="是否使用缓存数据"),
    ) -> dict:
        """
        分析大额资金流入/流出的股票

        该工具基于以下标准分析大额资金流动情况：
        1. 主力资金净流入/流出 ≥ 指定阈值（默认5000万元）
        2. 交易量占比（成交额/总市值）≥ 指定阈值（默认6%）
        3. 涨跌幅绝对值 ≥ 指定阈值（默认3%）
        4. 主力资金占成交额比例 ≥ 指定阈值（默认10%）
        5. 机构/股东持股变化（辅助确认资金意图）

        Args:
            main_fund_inflow_threshold (float): 主力资金净流入/流出阈值（万元），默认为5000万元
            turnover_ratio_threshold (float): 交易量占比阈值（成交额/总市值百分比），默认为6.0%
            price_change_threshold (float): 涨跌幅绝对值阈值，默认为3.0%
            main_fund_ratio_threshold (float): 主力资金占成交额比例阈值，默认为10.0%
            stock_type (str): 股票类型，可选"全部股票", "沪深A股", "沪市A股", "科创板", "深市A股", "创业板", "沪市B股", "深市B股"。其中"全部股票"是包括所有 A 股和 B 股在内的全部股票
            max_results (int): 最大返回结果数量，默认为10
            sort_by (str): 排序方式，'main_fund'(按主力资金流排序) 或 'turnover_ratio'(按交易量占比排序)
            analyze_holding (bool): 是否分析机构和股东持股情况，默认为True
            use_cache (bool): 是否使用缓存数据

        Returns:
            dict: 分析结果，包含符合条件的股票列表及其详细指标
        """
        cache_key = (
            f"large_fund_{main_fund_inflow_threshold}_{turnover_ratio_threshold}_"
            f"{price_change_threshold}_{main_fund_ratio_threshold}_{stock_type}_{sort_by}_{analyze_holding}"
        )
        current_time = time.time()

        # 检查缓存
        if use_cache and cache_key in _request_cache:
            cache_data, cache_time = _request_cache[cache_key]
            if current_time - cache_time < _cache_duration:
                return cache_data

        # 持股数据独立缓存 - 更长的缓存时间，因为这类数据变化较慢
        _holding_cache = {}
        _holding_cache_duration = 86400  # 24小时

        try:
            # 1. 获取主力资金流数据
            _throttle_request()
            df_main_fund = ak.stock_main_fund_flow(symbol=stock_type)
            if df_main_fund.empty:
                return {"message": "未查询到主力资金流数据", "data": []}

            # 2. 获取A股实时行情数据
            _throttle_request()
            df_quote = ak.stock_zh_a_spot_em()
            if df_quote.empty:
                return {"message": "未查询到A股实时行情数据", "data": []}

            # 3. 从行情数据获取市值信息
            if "代码" in df_quote.columns and "总市值" in df_quote.columns:
                df_indicator_processed = df_quote[["代码", "总市值"]]
            else:
                return {
                    "message": "市值数据格式异常",
                    "columns": list(df_quote.columns),
                    "data": [],
                }

            # 4. 处理主力资金流数据
            df_main_fund_processed = df_main_fund.copy()
            if "代码" in df_main_fund_processed.columns:
                column_mapping = {
                    "今日排行榜-主力净占比": "主力净流入-净占比",
                }
                df_main_fund_processed.rename(columns=column_mapping, inplace=True)

                if (
                    "主力净流入-净占比" in df_main_fund_processed.columns
                    and "成交额" in df_quote.columns
                ):
                    df_main_fund_with_turnover = pd.merge(
                        df_main_fund_processed,
                        df_quote[["代码", "成交额"]],
                        on="代码",
                        how="inner",
                    )
                    df_main_fund_with_turnover["主力净流入-净额"] = (
                        df_main_fund_with_turnover["成交额"]
                        * df_main_fund_with_turnover["主力净流入-净占比"]
                        / 100
                    )

                    df_main_fund_processed = df_main_fund_with_turnover[
                        ["代码", "名称", "主力净流入-净额", "主力净流入-净占比"]
                    ]

                    df_main_fund_processed["主力净流入-万元"] = (
                        df_main_fund_processed["主力净流入-净额"] / 10000
                    )
                else:
                    df_main_fund_processed = df_main_fund_processed[
                        ["代码", "名称", "主力净流入-净占比"]
                    ]
                    df_main_fund_processed["主力净流入-净额"] = 0
                    df_main_fund_processed["主力净流入-万元"] = 0
            else:
                return {
                    "message": "主力资金流数据格式异常",
                    "columns": list(df_main_fund.columns),
                    "data": [],
                }

            # 5. 处理行情数据
            df_quote_processed = df_quote[
                ["代码", "名称", "最新价", "涨跌幅", "成交量", "成交额"]
            ]
            df_quote_processed["成交额-万元"] = df_quote_processed["成交额"] / 10000

            # 6. 合并所有数据
            merged_df = pd.merge(
                df_main_fund_processed,
                df_quote_processed,
                on=["代码", "名称"],
                how="inner",
            )
            merged_df = pd.merge(
                merged_df, df_indicator_processed, on="代码", how="inner"
            )

            # 7. 计算分析指标
            merged_df["交易量占比"] = (
                merged_df["成交额-万元"] * 10000 / merged_df["总市值"] * 100
            )  # 转换为百分比
            merged_df["主力资金占比"] = (
                abs(merged_df["主力净流入-万元"]) / merged_df["成交额-万元"] * 100
            )  # 转换为百分比
            merged_df["资金流向"] = merged_df["主力净流入-万元"].apply(
                lambda x: "流入" if x > 0 else "流出"
            )

            # 8. 应用筛选条件
            filtered_df = merged_df[
                (
                    abs(merged_df["主力净流入-万元"]) >= main_fund_inflow_threshold
                )  # 主力资金净流入/流出阈值
                & (
                    merged_df["交易量占比"] >= turnover_ratio_threshold
                )  # 交易量占比阈值
                & (
                    abs(merged_df["涨跌幅"]) >= price_change_threshold
                )  # 涨跌幅绝对值阈值
                & (
                    merged_df["主力资金占比"] >= main_fund_ratio_threshold
                )  # 主力资金占成交额比例阈值
            ]

            # 9. 排序并限制结果数量
            if sort_by == "main_fund":
                sorted_df = filtered_df.sort_values(
                    by="主力净流入-万元", key=abs, ascending=False
                )
            else:
                sorted_df = filtered_df.sort_values(by="交易量占比", ascending=False)

            result_df = sorted_df.head(max_results)

            # 10. 格式化结果
            result_df["主力净流入-万元"] = result_df["主力净流入-万元"].round(2)
            result_df["交易量占比"] = result_df["交易量占比"].round(2)
            result_df["涨跌幅"] = result_df["涨跌幅"].round(2)
            result_df["主力资金占比"] = result_df["主力资金占比"].round(2)

            # 11. 分析持股情况
            holding_info = {}
            if analyze_holding and not result_df.empty:
                current_date = datetime.now()
                current_year = current_date.year
                current_month = current_date.month

                # 一季报(Q1):4月底前发布, 二季报(Q2):8月底前发布, 三季报(Q3):10月底前发布, 年报(Q4):次年4月底前发布
                # 动态构建要尝试的季度列表
                quarters_to_try = []

                if current_month >= 4:  # 4月及以后，可能有当年一季报
                    quarters_to_try.append(f"{current_year}1")  # 当年一季报

                if current_month >= 8:  # 8月及以后，可能有当年中报
                    quarters_to_try.insert(
                        0, f"{current_year}2"
                    )  # 当年中报（插入到最前面）

                if current_month >= 10:  # 10月及以后，可能有当年三季报
                    quarters_to_try.insert(
                        0, f"{current_year}3"
                    )  # 当年三季报（插入到最前面）

                quarters_to_try.append(f"{current_year - 1}4")  # 上一年年报

                if (
                    current_month <= 4
                ):  # 如果当前是1-4月，可能当年一季报还没出，上一年年报是最新的
                    quarters_to_try.insert(
                        0, f"{current_year}1"
                    )  # 尝试当年一季报（有可能刚发布）

                # 再添加更早的季度报告作为备选
                quarters_to_try.extend(
                    [
                        f"{current_year - 1}3",  # 上一年三季报
                        f"{current_year - 1}2",  # 上一年中报
                        f"{current_year - 1}1",  # 上一年一季报
                    ]
                )

                quarters_to_try = list(dict.fromkeys(quarters_to_try))

                for stock_code in result_df["代码"].unique():
                    clean_code = format_stock_code(stock_code=stock_code)

                    holding_cache_key = f"holding_{clean_code}"
                    if holding_cache_key in _holding_cache:
                        cache_data, cache_time = _holding_cache[holding_cache_key]
                        if current_time - cache_time < _holding_cache_duration:
                            holding_info[stock_code] = cache_data
                            continue

                    try:
                        stock_holding = {"机构持股": {}, "股东持股": {}}

                        # 11.1 获取机构持股数据
                        try:
                            available_data = []

                            for i, quarter in enumerate(quarters_to_try):
                                if i >= 3:
                                    break
                                if len(available_data) > 1:
                                    break

                                _throttle_request()
                                df_quarter = ak.stock_institute_hold_detail(
                                    stock=clean_code, quarter=quarter
                                )

                                if not df_quarter.empty:
                                    year = quarter[:4]
                                    q_num = quarter[4]
                                    quarter_name = {
                                        "1": "一季报",
                                        "2": "中报",
                                        "3": "三季报",
                                        "4": "年报",
                                    }[q_num]

                                    # 计算总持股比例和机构数量
                                    total_ratio = (
                                        df_quarter["最新持股比例"].sum()
                                        if "最新持股比例" in df_quarter.columns
                                        else df_quarter["持股比例"].sum()
                                    )
                                    institute_count = len(df_quarter)

                                    available_data.append(
                                        {
                                            "报告期": f"{year}年{quarter_name}",
                                            "持股比例": total_ratio,
                                            "机构数量": institute_count,
                                            "数据": df_quarter,
                                            "季度代码": quarter,
                                        }
                                    )

                            # 根据可获取的数据处理结果
                            if len(available_data) > 1:
                                current_data = available_data[0]  # 最新季度
                                previous_data = available_data[1]  # 前一季度

                                # 计算变化
                                ratio_change = (
                                    current_data["持股比例"] - previous_data["持股比例"]
                                )
                                count_change = (
                                    current_data["机构数量"] - previous_data["机构数量"]
                                )

                                # 统计增减持情况 (如果有增减幅数据)
                                current_df = current_data["数据"]
                                increased_count = (
                                    sum(current_df["持股比例增幅"] > 0)
                                    if "持股比例增幅" in current_df.columns
                                    else 0
                                )
                                decreased_count = (
                                    sum(current_df["持股比例增幅"] < 0)
                                    if "持股比例增幅" in current_df.columns
                                    else 0
                                )
                                unchanged_count = (
                                    sum(current_df["持股比例增幅"] == 0)
                                    if "持股比例增幅" in current_df.columns
                                    else 0
                                )

                                # 获取机构类型分布
                                institute_types = {}
                                if "持股机构类型" in current_df.columns:
                                    institute_types = (
                                        current_df["持股机构类型"]
                                        .value_counts()
                                        .to_dict()
                                    )

                                # 构建结果
                                stock_holding["机构持股"] = {
                                    "当前持股比例": f"{current_data['持股比例']:.2f}%",
                                    "上期持股比例": f"{previous_data['持股比例']:.2f}%",
                                    "变化": f"{ratio_change:+.2f}%",
                                    "当前报告期": current_data["报告期"],
                                    "上期报告期": previous_data["报告期"],
                                    "机构数量": current_data["机构数量"],
                                    "机构数量变化": f"{count_change:+d}家",
                                    "持股趋势": "增持"
                                    if ratio_change > 0
                                    else "减持"
                                    if ratio_change < 0
                                    else "持平",
                                }

                                # 添加增减持机构数量信息
                                if increased_count > 0 or decreased_count > 0:
                                    stock_holding["机构持股"]["增持机构数"] = (
                                        increased_count
                                    )
                                    stock_holding["机构持股"]["减持机构数"] = (
                                        decreased_count
                                    )
                                    stock_holding["机构持股"]["持股不变机构数"] = (
                                        unchanged_count
                                    )

                                # 添加主要机构类型信息
                                if institute_types:
                                    main_types = []
                                    for inst_type, count in institute_types.items():
                                        if count > 0:
                                            main_types.append(f"{inst_type}({count}家)")
                                    if main_types:
                                        stock_holding["机构持股"]["主要机构类型"] = (
                                            "、".join(main_types[:3])
                                        )

                            elif len(available_data) == 1:
                                current_data = available_data[0]
                                current_df = current_data["数据"]

                                institute_types = {}
                                if "持股机构类型" in current_df.columns:
                                    institute_types = (
                                        current_df["持股机构类型"]
                                        .value_counts()
                                        .to_dict()
                                    )

                                stock_holding["机构持股"] = {
                                    "持股比例": f"{current_data['持股比例']:.2f}%",
                                    "报告期": current_data["报告期"],
                                    "机构数量": current_data["机构数量"],
                                    "状态": f"只有单季度数据，无法比较变化，报告期：{current_data['报告期']}",
                                }

                                if institute_types:
                                    main_types = []
                                    for inst_type, count in institute_types.items():
                                        if count > 0:
                                            main_types.append(f"{inst_type}({count}家)")
                                    if main_types:
                                        stock_holding["机构持股"]["主要机构类型"] = (
                                            "、".join(main_types[:3])
                                        )
                            else:
                                stock_holding["机构持股"]["状态"] = "无机构持股数据"

                        except Exception as e:
                            stock_holding["机构持股"]["错误"] = str(e)

                        # 11.2 获取股东持股变化
                        try:
                            # 获取股东持股数据
                            _throttle_request()
                            df_holders = ak.stock_main_stock_holder(stock=clean_code)
                            if not df_holders.empty:
                                # 按截至日期排序，获取最新两期数据
                                df_holders["截至日期"] = pd.to_datetime(
                                    df_holders["截至日期"]
                                )
                                latest_dates = (
                                    df_holders["截至日期"]
                                    .sort_values(ascending=False)
                                    .unique()[:2]
                                )

                                if len(latest_dates) >= 2:
                                    # 获取最新一期和上一期的数据
                                    latest_holders = df_holders[
                                        df_holders["截至日期"] == latest_dates[0]
                                    ]
                                    previous_holders = df_holders[
                                        df_holders["截至日期"] == latest_dates[1]
                                    ]

                                    # 比较同名股东的持股变化
                                    common_holders = set(
                                        latest_holders["股东名称"]
                                    ) & set(previous_holders["股东名称"])

                                    # 计算持股变化
                                    increased_count = 0
                                    decreased_count = 0
                                    unchanged_count = 0

                                    for holder in common_holders:
                                        latest = latest_holders[
                                            latest_holders["股东名称"] == holder
                                        ]["持股比例"].values[0]
                                        previous = previous_holders[
                                            previous_holders["股东名称"] == holder
                                        ]["持股比例"].values[0]

                                        if latest > previous:
                                            increased_count += 1
                                        elif latest < previous:
                                            decreased_count += 1
                                        else:
                                            unchanged_count += 1

                                    # 新增和退出的股东
                                    new_holders = len(
                                        set(latest_holders["股东名称"])
                                        - set(previous_holders["股东名称"])
                                    )
                                    exited_holders = len(
                                        set(previous_holders["股东名称"])
                                        - set(latest_holders["股东名称"])
                                    )

                                    stock_holding["股东持股"] = {
                                        "最新截至日期": latest_dates[0].strftime(
                                            "%Y-%m-%d"
                                        ),
                                        "上期截至日期": latest_dates[1].strftime(
                                            "%Y-%m-%d"
                                        ),
                                        "增持股东数": increased_count,
                                        "减持股东数": decreased_count,
                                        "持股不变股东数": unchanged_count,
                                        "新增股东数": new_holders,
                                        "退出股东数": exited_holders,
                                        "总股东数": int(
                                            latest_holders["股东总数"].iloc[0]
                                        )
                                        if "股东总数" in latest_holders.columns
                                        and not latest_holders["股东总数"].isna().all()
                                        else "未知",
                                        "总体趋势": "增持"
                                        if increased_count > decreased_count
                                        else "减持"
                                        if decreased_count > increased_count
                                        else "持平",
                                    }
                                elif len(latest_dates) == 1:
                                    latest_holders = df_holders[
                                        df_holders["截至日期"] == latest_dates[0]
                                    ]
                                    stock_holding["股东持股"] = {
                                        "最新截至日期": latest_dates[0].strftime(
                                            "%Y-%m-%d"
                                        ),
                                        "总股东数": latest_holders["股东总数"].iloc[0]
                                        if "股东总数" in latest_holders.columns
                                        and not latest_holders["股东总数"].isna().all()
                                        else "未知",
                                        "状态": "仅有一期数据，无法比较变化",
                                    }
                                else:
                                    stock_holding["股东持股"]["状态"] = "无股东持股数据"
                            else:
                                stock_holding["股东持股"]["状态"] = "无股东持股数据"
                        except Exception as e:
                            stock_holding["股东持股"]["错误"] = str(e)

                        _holding_cache[holding_cache_key] = (
                            stock_holding,
                            current_time,
                        )
                        holding_info[stock_code] = stock_holding

                    except Exception as e:
                        holding_info[stock_code] = {"错误": str(e)}

            # 12. 构建最终返回结果
            result_list = []
            for _, row in result_df.iterrows():
                stock_code = row["代码"]
                stock_data = {
                    "代码": stock_code,
                    "名称": row["名称"],
                    "最新价": row["最新价"],
                    "涨跌幅": f"{row['涨跌幅']}%",
                    "主力资金": f"{row['主力净流入-万元']}万元",
                    "资金流向": row["资金流向"],
                    "主力资金占比": f"{row['主力资金占比']}%",
                    "成交额": f"{row['成交额-万元']}万元",
                    "总市值": f"{row['总市值'] / 10000:.2f}亿元",
                    "交易量占比": f"{row['交易量占比']}%",
                }

                # 添加持股信息
                if analyze_holding and stock_code in holding_info:
                    stock_holding = holding_info[stock_code]

                    # 添加机构持股信息
                    if "机构持股" in stock_holding and stock_holding["机构持股"]:
                        inst_info = stock_holding["机构持股"]
                        if "错误" in inst_info:
                            stock_data["机构持股"] = "查询失败"
                        elif "状态" in inst_info:
                            stock_data["机构持股"] = inst_info["状态"]
                        else:
                            if "变化" in inst_info:
                                stock_data["机构持股变化"] = inst_info["变化"]
                                stock_data["机构持股趋势"] = (
                                    inst_info["持股趋势"]
                                    if "持股趋势" in inst_info
                                    else (
                                        "增持" if "+" in inst_info["变化"] else "减持"
                                    )
                                )
                            if "当前持股比例" in inst_info:
                                stock_data["机构持股比例"] = inst_info["当前持股比例"]
                            elif "持股比例" in inst_info:
                                stock_data["机构持股比例"] = inst_info["持股比例"]
                            if "机构数量" in inst_info:
                                stock_data["机构数量"] = inst_info["机构数量"]
                            if "主要机构类型" in inst_info:
                                stock_data["主要机构类型"] = inst_info["主要机构类型"]
                    else:
                        stock_data["机构持股"] = "未查询"

                    # 添加股东持股信息
                    if "股东持股" in stock_holding and stock_holding["股东持股"]:
                        holder_info = stock_holding["股东持股"]
                        if "错误" in holder_info:
                            stock_data["十大股东"] = "查询失败"
                        elif "状态" in holder_info:
                            stock_data["十大股东"] = "无数据"
                        elif "总体趋势" in holder_info:
                            stock_data["十大股东动向"] = holder_info["总体趋势"]
                            if all(
                                k in holder_info for k in ["增持股东数", "减持股东数"]
                            ):
                                stock_data["股东变动详情"] = (
                                    f"增持{holder_info['增持股东数']}家，减持{holder_info['减持股东数']}家"
                                )
                                if (
                                    "新增股东数" in holder_info
                                    and holder_info["新增股东数"] > 0
                                ):
                                    stock_data["股东变动详情"] += (
                                        f"，新进{holder_info['新增股东数']}家"
                                    )
                                if (
                                    "退出股东数" in holder_info
                                    and holder_info["退出股东数"] > 0
                                ):
                                    stock_data["股东变动详情"] += (
                                        f"，退出{holder_info['退出股东数']}家"
                                    )
                        else:
                            stock_data["十大股东"] = holder_info.get(
                                "状态", "无变化数据"
                            )
                    else:
                        stock_data["十大股东"] = "未查询"

                result_list.append(stock_data)

            # 13. 构建完整结果
            result = {
                "message": "分析完成",
                "timestamp": current_time,
                "filter_criteria": {
                    "主力资金阈值": f"{main_fund_inflow_threshold}万元",
                    "交易量占比阈值": f"{turnover_ratio_threshold}%",
                    "涨跌幅阈值": f"{price_change_threshold}%",
                    "主力资金占比阈值": f"{main_fund_ratio_threshold}%",
                },
                "total_matched": len(result_list),
                "data": result_list,
            }

            # 添加持股数据统计信息
            if analyze_holding:
                holding_stats = {
                    "机构持股数据可用率": f"{sum(1 for code, info in holding_info.items() if '机构持股' in info and info['机构持股'] and '状态' not in info['机构持股'])}/{len(holding_info)}",
                    "股东数据可用率": f"{sum(1 for code, info in holding_info.items() if '股东持股' in info and info['股东持股'] and '状态' not in info['股东持股'])}/{len(holding_info)}",
                }

                # 按趋势统计
                if holding_info:
                    inst_trends = {"增持": 0, "减持": 0, "持平": 0, "无数据": 0}
                    holder_trends = {"增持": 0, "减持": 0, "持平": 0, "无数据": 0}

                    for _, info in holding_info.items():
                        # 统计机构持股趋势
                        if "机构持股" in info and info["机构持股"]:
                            if "持股趋势" in info["机构持股"]:
                                inst_trends[info["机构持股"]["持股趋势"]] += 1
                            elif "状态" in info["机构持股"]:
                                inst_trends["无数据"] += 1
                            else:
                                inst_trends["无数据"] += 1
                        else:
                            inst_trends["无数据"] += 1

                        # 统计股东持股趋势
                        if "股东持股" in info and info["股东持股"]:
                            if "总体趋势" in info["股东持股"]:
                                holder_trends[info["股东持股"]["总体趋势"]] += 1
                            elif "状态" in info["股东持股"]:
                                holder_trends["无数据"] += 1
                            else:
                                holder_trends["无数据"] += 1
                        else:
                            holder_trends["无数据"] += 1

                    holding_stats["机构持股趋势统计"] = inst_trends
                    holding_stats["股东持股趋势统计"] = holder_trends

                result["holding_statistics"] = holding_stats

            _request_cache[cache_key] = (result, current_time)
            return result

        except Exception as e:
            raise ValueError(f"大额资金流分析失败: {str(e)}")

    @mcp.tool()
    async def analyze_stock_fund_flow_detail(
        stock_code: str = Field(..., description="股票代码，如：000001 或 600000"),
        days: int = Field(5, description="分析的天数，默认5天"),
    ) -> dict:
        """
        分析单个股票的资金流详情，包括主力资金流向、交易活跃度、价格影响及资金来源背景等

        Args:
            stock_code: 股票代码，例如：000001 或 600000
            days: 分析的天数，默认5天

        Returns:
            包含股票资金流分析详情的字典
        """
        pass

from fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:  
    """向FastMCP服务器注册大额资金流分析资源"""  

    @mcp.resource("resources://funds/analysis_guide")
    async def large_fund_flow_analysis_guide() -> str:
        """
        大额资金流分析指南

        Returns:
            str: 大额资金流分析指南文本
        """
        return """
        # 大额资金流分析指南
        
        大额资金流分析是识别市场主力资金动向和潜在投资机会的重要工具。通过以下量化标准筛选股票：
        
        ## 量化标准
        
        1. **主力资金净流入/流出 ≥ 5000万元**
           - 核心指标，直接反映资金规模
           - 可判断主力资金的明确方向和力度
        
        2. **交易量占比（成交额/总市值）≥ 6%（宽松）或 10%（严格）**
           - 标准化资金规模，消除市值差异影响
           - 反映资金相对于股票体量的重要性
        
        3. **涨跌幅绝对值 ≥ 3%**
           - 验证资金对价格的实际影响力
           - 确认资金流动与价格变动的一致性
        
        4. **主力资金占成交额 ≥ 10%**
           - 确认主力资金在总交易中的主导地位
           - 辅助确认资金意图的明确性
        
        ## 分析框架
        
        1. 获取交易量、收盘价、主力资金流、市值和持股数据
        2. 计算交易量占比和价格波动率
        3. 筛选符合条件的股票
        4. 验证持股情况（如机构增持），增强可信度
        5. 按交易量占比或主力资金金额排序，输出结果
        
        ## 实用分析策略
        
        - **资金流入+股价上涨**：可能是主力建仓或增持信号
        - **资金流入+股价下跌**：可能是筹码换手或洗盘行为
        - **资金流出+股价上涨**：可能是高位派发或减持信号
        - **资金流出+股价下跌**：可能是主力撤离或止损信号
        
        资金流向与股价变动的背离往往蕴含更重要的市场信息。
        """

    @mcp.resource("resources://funds/analysis_examples")
    async def large_fund_flow_analysis_examples() -> str:
        """
        大额资金流分析示例

        Returns:
            str: 大额资金流分析示例文本
        """
        return """
        # 大额资金流分析示例场景
        
        以下是几种典型的大额资金流动场景及其可能的市场含义：
        
        ## 示例1：主力大额资金流入
        
        某股票出现以下指标：
        - 主力净流入：8500万元
        - 交易量占比：7.5%
        - 涨幅：4.2%
        - 主力资金占成交额：18%
        
        **可能的解读**：主力资金显著流入并推动股价上涨，这可能是主力建仓阶段的信号，尤其是当这种情况持续数天时。
        
        ## 示例2：主力大额资金流出但股价上涨
        
        某股票出现以下指标：
        - 主力净流出：6200万元
        - 交易量占比：12%
        - 涨幅：3.5%
        - 主力资金占成交额：15%
        
        **可能的解读**：主力在股价上涨过程中减持，这可能是高位派发的警示信号，建议谨慎对待。
        
        ## 示例3：超大额资金流入但股价仅微涨
        
        某股票出现以下指标：
        - 主力净流入：12000万元
        - 交易量占比：8.2%
        - 涨幅：1.8%（低于标准阈值）
        - 主力资金占成交额：25%
        
        **可能的解读**：大资金流入但股价反应不强，可能是主力在刻意控制股价，积累筹码的过程，这种情况需要持续观察。
        
        通过对比不同场景的指标组合，可以更准确地解读大额资金流动的真实意图。
        """

    @mcp.resource("resources://funds/indicators_explanation")
    async def large_fund_flow_indicators_explanation() -> str:
        """
        大额资金流指标说明

        Returns:
            str: 大额资金流指标说明文本
        """
        return """
        # 大额资金流核心指标说明
        
        ## 主力资金净流入/流出
        
        **定义**：特定时间段内主力资金的净买入或净卖出金额。
        **计算方法**：主力净买入成交额 - 主力净卖出成交额
        **数据来源**：通常根据成交量和委托单大小推算
        **重要性**：直接反映机构和大资金的行为倾向
        
        ## 交易量占比
        
        **定义**：成交额占总市值的百分比
        **计算方法**：日成交额 ÷ 总市值 × 100%
        **意义**：标准化不同市值股票的资金活跃度
        **标准**：
        - <3%：交易不活跃
        - 3-6%：正常交易活跃度
        - 6-10%：交易较为活跃
        - >10%：交易非常活跃，可能有重要事件发生
        
        ## 价格波动率
        
        **定义**：股价相对于前一交易日的变动百分比
        **计算方法**：(当日收盘价 - 前日收盘价) ÷ 前日收盘价 × 100%
        **重要性**：验证资金流向是否对价格产生实质影响
        
        ## 主力资金占比
        
        **定义**：主力资金成交额占总成交额的比例
        **计算方法**：主力资金成交额 ÷ 总成交额 × 100%
        **意义**：反映主力资金在当日交易中的影响力
        **参考标准**：
        - <5%：主力参与度低
        - 5-10%：主力一般参与度
        - 10-20%：主力明显参与
        - >20%：主力高度活跃
        """
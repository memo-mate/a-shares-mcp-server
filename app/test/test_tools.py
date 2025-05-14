# import pytest
# from fastmcp import FastMCP
# from app.tools.large_fund_flow_analysis_tool import register_tools

# @pytest.fixture
# def mcp_with_tools():
#     mcp = FastMCP()
#     register_tools(mcp)
#     return mcp

# async def test_analyze_large_fund_flow_basic(mcp_with_tools):
#     # 基本功能测试
#     result = await mcp_with_tools._mcp_call_tool("analyze_large_fund_flow", {})
#     # 添加断言
#     assert result is not None


import pytest
from fastmcp import FastMCP
from app.tools.large_fund_flow_analysis_tool import register_tools

# 标记整个模块为异步测试
pytestmark = pytest.mark.asyncio


async def test_analyze_large_fund_flow():
    # 创建 FastMCP 实例
    mcp = FastMCP()

    # 注册您的工具
    register_tools(mcp)

    # 准备测试数据
    test_data = {
        "main_fund_inflow_threshold": 5000,
        "turnover_ratio_threshold": 6,
        "price_change_threshold": 3,
        "main_fund_ratio_threshold": 10,
        "stock_type": "沪深A股",
        "max_results": 10,
        "sort_by": "main_fund",
        "analyze_holding": True,
        "use_cache": False,
    }

    # 调用工具并测试结果
    result = await mcp._mcp_call_tool("analyze_large_fund_flow", test_data)
    assert result is not None
    assert "data" in result


# 新增的测试方法 - 测试低阈值场景
async def test_analyze_large_fund_flow_low_threshold():
    # 创建 FastMCP 实例
    mcp = FastMCP()
    
    # 注册工具
    register_tools(mcp)
    
    # 准备测试数据 - 使用较低的阈值，查找更多的股票
    test_data = {
        "main_fund_inflow_threshold": 2000,  # 降低主力资金阈值
        "turnover_ratio_threshold": 3,       # 降低交易量占比阈值
        "price_change_threshold": 2,         # 降低涨跌幅阈值
        "main_fund_ratio_threshold": 5,      # 降低主力资金占比阈值
        "stock_type": "全部股票",
        "max_results": 15,                   # 增加结果数量
        "sort_by": "turnover_ratio",         # 按交易量占比排序
        "analyze_holding": False,            # 不分析持股情况以提高速度
        "use_cache": False
    }
    
    # 调用工具并验证结果
    result = await mcp._mcp_call_tool("analyze_large_fund_flow", test_data)
    assert result is not None
    assert "data" in result
    
    # 验证返回的数据符合预期
    if "data" in result and result["data"]:
        # 确保结果不超过max_results
        assert len(result["data"]) <= test_data["max_results"]
        
        # 验证第一条数据的交易量占比应该是最高的
        if len(result["data"]) > 1:
            first_stock = result["data"][0]
            assert "交易量占比" in first_stock
            # 移除百分号并转为浮点数进行比较
            first_ratio = float(first_stock["交易量占比"].replace("%", ""))
            assert first_ratio >= 3.0  # 应该至少达到阈值


async def test_analyze_stock_fund_flow_detail():  
    # 创建 FastMCP 实例  
    mcp = FastMCP()  
      
    # 注册您的工具  
    register_tools(mcp)  
      
    # 准备测试数据  
    test_data = {  
        "stock_code": "000001",  # 平安银行
        "market": "sz",
        "check_big_deals": True
    }  
      
    # 调用工具并测试结果  
    await mcp._mcp_call_tool("analyze_stock_fund_flow_detail", test_data)

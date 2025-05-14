from fastmcp import FastMCP
from tools import large_fund_flow_analysis_tool
from resources import large_fund_flow_resources, static_resource
# from prompts import fund_flow_prompt

def create_mcp_server():
    """
    创建并配置FastMCP服务器实例。
    
    Returns:
        FastMCP: 配置好的FastMCP实例。
    """
    # 创建FastMCP实例
    mcp = FastMCP("A-stock Mcp Server")
    
    # 注册工具
    large_fund_flow_analysis_tool.register_tools(mcp)
    
    # 注册资源
    large_fund_flow_resources.register_resources(mcp)
    static_resource.register_resources(mcp)
    
    # 注册提示
    # fund_flow_prompt.register_prompts(mcp)
    
    return mcp

mcp = create_mcp_server()

if __name__ == "__main__":
    mcp.run()
from fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:  
    """向FastMCP服务器注册大额资金流分析资源"""  

    @mcp.resource("config://version")
    def get_version(): 
        return "2.0.1"
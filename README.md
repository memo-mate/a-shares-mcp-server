# A-Stock MCP Server

## 项目简介

A-Stock MCP Server 是一个基于 FastMCP 框架开发的 Model Context Protocol 服务器，专注于 A 股市场的数据分析和工具提供。该服务器为大语言模型（LLM）提供了一系列工具和资源，使其能够进行 A 股市场数据的实时查询、历史数据分析和大额资金流向分析等功能。

## 功能特性

### 大额资金流分析
- 基于量化标准筛选主力资金流入/流出的股票
- 分析主力资金净流入、交易量占比、价格波动与主力资金占比等核心指标
- 提供不同场景下的资金流向解读和分析建议

### 股票实时行情
- 支持查询沪深京所有 A 股的实时行情数据
- 提供按市场分类（上海、深圳、北京、科创板、创业板等）的行情查询
- 支持单只股票的详细行情查询和市场整体概览

### 历史行情数据
- 提供日线、周线、月线级别的历史行情数据查询
- 支持分钟级（1、5、15、30、60分钟）历史行情数据
- 提供多只股票历史行情的对比分析

## 技术架构

- **后端框架**：基于 FastMCP 2.3.3+ 开发的 MCP 服务器
- **数据源**：使用 AKShare 1.16.89+ 获取 A 股市场数据
- **依赖管理**：使用 uv 进行 Python 依赖管理
- **Python 版本**：要求 Python 3.12 或更高版本

## 项目结构
a-stock-mcp-server/
├── app/ # 应用程序主目录
│ ├── prompts/ # 提示模板
│ ├── resources/ # 资源文件
│ ├── tools/ # 工具函数
│ ├── utils/ # 工具类
│ ├── mcp_server.py # 服务器入口文件
├── .venv/ # 虚拟环境(由 uv 管理)
├── mcp_config.json.sample # MCP配置示例文件
├── pyproject.toml # 项目配置文件
└── README.md # 项目说明文档

## 安装与配置

### 环境要求
- Python 3.12 或更高版本
- uv 包管理器

### 安装步骤

1. 克隆仓库
   ```
   git clone <仓库地址>
   cd a-stock-mcp-server
   ```

2. 使用 uv 创建虚拟环境并安装依赖
   ```
   uv venv -p 3.12
   uv sync
   ```

3. 配置 MCP 服务器
   - 根据实际路径修改配置`mcp_config.json.sample`文件中的目录路径

## 使用方法

### 启动服务器
```bash
fastmcp run .\app\mcp_server.py:mcp
```
或
```bash
uv run .\app\mcp_server.py
```
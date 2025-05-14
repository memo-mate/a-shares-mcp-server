def format_stock_code(symbol: str) -> str:
    """
    格式化股票代码
    :param symbol: 6位股票代码（如 '600519', '300750', '830799'）
    :type symbol: str
    """
    if len(symbol) > 6:
        symbol = symbol[-6:]  # 取最后6位

    # 处理包含.SH或.SZ后缀的情况
    if "." in symbol:
        symbol = symbol.split(".")[0]

    return symbol


def get_stock_market(symbol: str) -> str:
    """
    根据6位股票代码判断所属市场（上交所、深交所、北交所）。

    :param symbol: 6位股票代码（如 '600519', '300750', '830799'）
    :type symbol: str
    :return: 市场名称 ('上海证券交易所', '深圳证券交易所', '北京证券交易所', 或 '未知市场')
    :rtype: str
    :raises ValueError: 如果股票代码不是6位数字
    """
    # 验证股票代码格式
    if not (isinstance(symbol, str) and len(symbol) == 6 and symbol.isdigit()):
        raise ValueError("股票代码必须为6位数字字符串")

    # 获取代码前缀
    prefix = symbol[:2]

    # 根据前缀判断市场
    if prefix in ["60", "68"]:  # 上交所：主板(60)、科创板(68)
        return "sh"
    elif prefix in ["00", "30", "002"]:  # 深交所：主板(00)、创业板(30)、中小板(002)
        return "sz"
    elif prefix in ["43", "83", "87", "88"]:  # 北交所：创新型中小企业
        return "bj"

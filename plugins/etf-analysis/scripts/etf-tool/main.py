#!/usr/bin/env python3
"""
ETF 分析工具

数据源：AkShare (免费，无需认证)
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional

import akshare as ak
import numpy as np
import pandas as pd


# ============================================================================
# 常用 ETF 代码映射
# ============================================================================
ETF_CODE_MAP = {
    # 宽基指数
    "上证50": "510050",
    "50etf": "510050",
    "沪深300": "510300",
    "300etf": "510300",
    "中证500": "510500",
    "500etf": "510500",
    "中证1000": "512100",
    "1000etf": "512100",
    "创业板": "159915",
    "创业板etf": "159915",
    "科创50": "588000",
    "科创50etf": "588000",
    # 行业主题
    "证券etf": "512880",
    "银行etf": "512800",
    "医药etf": "512010",
    "消费etf": "159928",
    "新能源车": "515030",
    "芯片etf": "159995",
    "军工etf": "512660",
    # 跨境
    "纳指etf": "513100",
    "纳斯达克": "513100",
    "标普500": "513500",
    "恒生科技": "513180",
    "恒生etf": "159920",
    "日经etf": "513880",
}


def resolve_etf_code(code_or_name: str) -> str:
    """解析 ETF 代码，支持名称别名"""
    code_lower = code_or_name.lower().strip()
    if code_lower in ETF_CODE_MAP:
        return ETF_CODE_MAP[code_lower]
    # 处理 BaoStock 风格的代码前缀 (sh.510050, sz.159915)
    if "." in code_or_name:
        return code_or_name.split(".")[-1]
    return code_or_name


def get_last_quarter() -> tuple[int, int]:
    """获取上一季度的年份和季度"""
    now = datetime.now()
    current_quarter = (now.month - 1) // 3 + 1  # 1-4
    if current_quarter == 1:
        return now.year - 1, 4
    return now.year, current_quarter - 1


# ============================================================================
# AkShare 数据源 (默认)
# ============================================================================
class AkShareSource:
    """AkShare 数据源 - 免费，无需认证"""

    @staticmethod
    def get_etf_spot() -> pd.DataFrame:
        """获取所有 ETF 实时行情 (使用新浪财经数据源)"""
        df = ak.fund_etf_category_sina(symbol="ETF基金")

        # 统一列名
        df = df.rename(
            columns={
                "最新价": "最新价",
                "涨跌额": "涨跌额",
                "涨跌幅": "涨跌幅",
                "买入": "买入价",
                "卖出": "卖出价",
                "昨收": "昨收",
                "今开": "开盘价",
                "最高": "最高价",
                "最低": "最低价",
            }
        )

        # 清理代码格式 (移除 sz/sh 前缀)
        if "代码" in df.columns:
            df["代码"] = df["代码"].str.replace(r"^(sz|sh)", "", regex=True)

        return df

    @staticmethod
    def get_etf_quote(codes: list[str]) -> pd.DataFrame:
        """获取指定 ETF 实时行情"""
        all_df = AkShareSource.get_etf_spot()

        # 筛选指定代码
        result = all_df[all_df["代码"].isin(codes)].copy()

        if result.empty:
            return pd.DataFrame()

        # 选择关键列
        columns = [
            "代码",
            "名称",
            "最新价",
            "涨跌额",
            "涨跌幅",
            "成交量",
            "成交额",
            "开盘价",
            "最高价",
            "最低价",
            "昨收",
        ]
        available = [c for c in columns if c in result.columns]
        return result[available].reset_index(drop=True)

    @staticmethod
    def get_etf_hist(
        code: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取 ETF 历史行情

        Args:
            code: ETF 代码
            period: 周期 daily/weekly/monthly
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            adjust: 复权类型 qfq-前复权 hfq-后复权 空-不复权
        """
        try:
            # 优先使用东方财富接口
            df = ak.fund_etf_hist_em(
                symbol=code,
                period=period,
                start_date=start_date or "19900101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust,
            )
            return df
        except Exception:
            # 备用：使用新浪财经历史数据接口
            try:
                # 确定市场前缀
                if code.startswith("15") or code.startswith("16"):
                    symbol = f"sz{code}"
                else:
                    symbol = f"sh{code}"

                df = ak.fund_etf_hist_sina(symbol=symbol)

                # 筛选日期范围
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    if start_date:
                        start = pd.to_datetime(start_date)
                        df = df[df["date"] >= start]
                    if end_date:
                        end = pd.to_datetime(end_date)
                        df = df[df["date"] <= end]

                return df
            except Exception:
                # 最后尝试股票历史数据接口 (ETF 也可用)
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period=period,
                    start_date=start_date or "19900101",
                    end_date=end_date or datetime.now().strftime("%Y%m%d"),
                    adjust=adjust if adjust else "",
                )
                return df

    @staticmethod
    def get_etf_list() -> pd.DataFrame:
        """获取 ETF 列表"""
        df = AkShareSource.get_etf_spot()
        columns = ["代码", "名称", "最新价", "涨跌幅", "成交额"]
        available = [c for c in columns if c in df.columns]
        return df[available]

    @staticmethod
    def search_etf(keyword: str) -> pd.DataFrame:
        """搜索 ETF"""
        df = AkShareSource.get_etf_spot()
        mask = df["名称"].str.contains(keyword, case=False, na=False) | df[
            "代码"
        ].str.contains(keyword, na=False)
        result = df[mask].copy()
        columns = ["代码", "名称", "最新价", "涨跌幅", "成交额"]
        available = [c for c in columns if c in result.columns]
        return result[available].reset_index(drop=True)

    @staticmethod
    def get_etf_premium(codes: Optional[list[str]] = None) -> pd.DataFrame:
        """
        获取 ETF 溢价率数据

        溢价率 = (市价 - 净值) / 净值 * 100%
        正数表示溢价，负数表示折价
        """
        df = ak.fund_etf_fund_daily_em()

        # 筛选指定代码
        if codes:
            df = df[df["基金代码"].isin(codes)].copy()

        if df.empty:
            return pd.DataFrame()

        # 获取净值列名 (动态日期格式)
        nav_cols = [c for c in df.columns if "单位净值" in c]
        latest_nav_col = nav_cols[0] if nav_cols else None
        prev_nav_col = nav_cols[1] if len(nav_cols) > 1 else None

        # 构建结果
        result = pd.DataFrame()
        result["代码"] = df["基金代码"]
        result["名称"] = df["基金简称"]
        result["类型"] = df["类型"]
        result["市价"] = df["市价"]

        if latest_nav_col:
            result["净值"] = df[latest_nav_col]

        result["折价率"] = df["折价率"]
        result["增长率"] = df["增长率"]

        return result.reset_index(drop=True)

    @staticmethod
    def get_etf_holding(code: str, year: str = "2024") -> pd.DataFrame:
        """
        获取 ETF 持仓明细 (前十大持仓)

        Args:
            code: ETF 代码 (如 510050)
            year: 年份 (如 2024)
        """
        df = ak.fund_portfolio_hold_em(symbol=code, date=year)
        if df.empty:
            return df

        # 过滤只保留最新季度的数据 (API 返回按时间顺序，最新在最后)
        if "季度" in df.columns:
            latest_quarter = df["季度"].iloc[-1]
            df = df[df["季度"] == latest_quarter].copy()

        result = df[["序号", "股票代码", "股票名称", "占净值比例", "持股数", "持仓市值"]].copy()
        if "季度" in df.columns:
            result["季度"] = df["季度"].iloc[0] if not df.empty else ""
        return result

    @staticmethod
    def get_etf_industry(code: str, year: str = "2024") -> pd.DataFrame:
        """
        获取 ETF 行业配置

        Args:
            code: ETF 代码
            year: 年份
        """
        df = ak.fund_portfolio_industry_allocation_em(symbol=code, date=year)
        if df.empty:
            return df

        result = df[["序号", "行业类别", "占净值比例", "市值", "截止时间"]].copy()
        # 格式化市值
        result["市值"] = result["市值"].apply(
            lambda x: f"{x/1e4:.2f}万" if x < 1e8 else f"{x/1e8:.2f}亿"
        )
        # 格式化占净值比例
        result["占净值比例"] = result["占净值比例"].apply(lambda x: f"{x:.2f}%")
        return result

    @staticmethod
    def get_etf_holding_change(code: str, year: str = "2024") -> pd.DataFrame:
        """
        获取 ETF 持仓变动 (季度买入/卖出)

        Args:
            code: ETF 代码
            year: 年份
        """
        result = pd.DataFrame()

        # 分别获取买入和卖出数据 (API 需要分别调用不同 indicator)
        try:
            buy_df = ak.fund_portfolio_change_em(symbol=code, date=year, indicator="累计买入")
            if not buy_df.empty:
                # 只取最新季度的前10条
                latest_quarter = buy_df["季度"].iloc[0] if "季度" in buy_df.columns else None
                if latest_quarter:
                    buy_df = buy_df[buy_df["季度"] == latest_quarter].head(10).copy()
                else:
                    buy_df = buy_df.head(10).copy()
                buy_df["操作"] = "买入"
                buy_df = buy_df.rename(columns={"本期累计买入金额": "金额(万)", "占期初基金资产净值比例": "占比(%)"})
                result = pd.concat([result, buy_df[["操作", "股票代码", "股票名称", "金额(万)", "占比(%)"]]])
        except Exception:
            pass

        try:
            sell_df = ak.fund_portfolio_change_em(symbol=code, date=year, indicator="累计卖出")
            if not sell_df.empty:
                # 只取最新季度的前10条
                latest_quarter = sell_df["季度"].iloc[0] if "季度" in sell_df.columns else None
                if latest_quarter:
                    sell_df = sell_df[sell_df["季度"] == latest_quarter].head(10).copy()
                else:
                    sell_df = sell_df.head(10).copy()
                sell_df["操作"] = "卖出"
                # API 返回的列名不一致，卖出数据的金额列仍然叫 "本期累计买入金额"
                sell_df = sell_df.rename(columns={"本期累计买入金额": "金额(万)", "占期初基金资产净值比例": "占比(%)"})
                result = pd.concat([result, sell_df[["操作", "股票代码", "股票名称", "金额(万)", "占比(%)"]]])
        except Exception:
            pass

        return result.reset_index(drop=True)

    @staticmethod
    def get_fund_flow(code: str, market: str = "sh", days: int = 10) -> pd.DataFrame:
        """
        获取资金流向数据

        Args:
            code: 代码
            market: 市场 (sh/sz)
            days: 天数
        """
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        if df.empty:
            return df

        result = df.head(days).copy()
        # 格式化金额
        for col in ["主力净流入-净额", "超大单净流入-净额", "大单净流入-净额", "中单净流入-净额", "小单净流入-净额"]:
            if col in result.columns:
                result[col] = result[col].apply(lambda x: f"{x/1e8:.2f}亿" if abs(x) >= 1e8 else f"{x/1e4:.2f}万")

        # 重命名
        result = result.rename(columns={
            "日期": "日期",
            "收盘价": "收盘",
            "涨跌幅": "涨跌%",
            "主力净流入-净额": "主力净流入",
            "主力净流入-净占比": "主力占比%",
            "超大单净流入-净额": "超大单",
            "大单净流入-净额": "大单",
            "中单净流入-净额": "中单",
            "小单净流入-净额": "小单",
        })

        return result[["日期", "收盘", "涨跌%", "主力净流入", "主力占比%"]].reset_index(drop=True)

    @staticmethod
    def get_etf_scale(exchange: str = "all") -> pd.DataFrame:
        """
        获取 ETF 规模数据

        Args:
            exchange: 交易所 (sse-上交所, szse-深交所, all-全部)
        """
        result = pd.DataFrame()

        if exchange in ["sse", "all"]:
            try:
                sse_df = ak.fund_etf_scale_sse()
                sse_df["交易所"] = "上交所"
                result = pd.concat([result, sse_df])
            except Exception:
                pass

        if exchange in ["szse", "all"]:
            try:
                szse_df = ak.fund_etf_scale_szse()
                szse_df["交易所"] = "深交所"
                result = pd.concat([result, szse_df])
            except Exception:
                pass

        if result.empty:
            return result

        # 格式化份额
        if "基金份额" in result.columns:
            result["份额(亿份)"] = result["基金份额"].apply(lambda x: f"{x/1e8:.2f}" if pd.notna(x) else "-")

        columns = ["交易所", "基金代码", "基金简称", "份额(亿份)", "ETF类型"]
        available = [c for c in columns if c in result.columns]
        return result[available].reset_index(drop=True)

    @staticmethod
    def get_etf_dividend() -> pd.DataFrame:
        """获取 ETF 分红历史"""
        df = ak.fund_etf_dividend_sina()
        if df.empty:
            return df

        df = df.rename(columns={"日期": "分红日期", "累计分红": "累计分红(元)"})
        return df

    @staticmethod
    def get_fund_rating(code: Optional[str] = None) -> pd.DataFrame:
        """
        获取基金评级

        Args:
            code: 基金代码 (可选，不指定则返回所有 ETF)
        """
        df = ak.fund_rating_all()
        if df.empty:
            return df

        # 筛选 ETF (代码以 51/15/56/58/16 开头)
        etf_prefixes = ("51", "15", "56", "58", "16")
        df = df[df["代码"].astype(str).str.startswith(etf_prefixes)].copy()

        if code:
            df = df[df["代码"].astype(str) == str(code)]

        # 选择关键列
        result = df[["代码", "简称", "基金公司", "上海证券", "招商证券", "济安金信", "晨星评级", "5星评级家数"]].copy()
        result = result.rename(columns={
            "上海证券": "上证评级",
            "招商证券": "招商评级",
            "济安金信": "济安评级",
            "晨星评级": "晨星评级",
            "5星评级家数": "5星数",
        })

        return result.reset_index(drop=True)

    @staticmethod
    def get_stock_news(code: str, limit: int = 20) -> pd.DataFrame:
        """
        获取个股/ETF 相关新闻

        Args:
            code: 股票/ETF 代码
            limit: 返回数量
        """
        df = ak.stock_news_em(symbol=code)
        if df.empty:
            return df

        # 选择关键列并重命名
        result = df[["发布时间", "新闻标题", "文章来源", "新闻链接"]].copy()
        result = result.rename(columns={
            "发布时间": "时间",
            "新闻标题": "标题",
            "文章来源": "来源",
            "新闻链接": "链接",
        })

        # 截断标题长度便于显示
        result["标题"] = result["标题"].apply(lambda x: x[:50] + "..." if len(str(x)) > 50 else x)

        return result.head(limit).reset_index(drop=True)

    @staticmethod
    def get_market_news(limit: int = 30) -> pd.DataFrame:
        """
        获取市场快讯 (财联社)

        Args:
            limit: 返回数量
        """
        df = ak.stock_info_global_cls()
        if df.empty:
            return df

        # 合并日期和时间
        result = df.copy()
        result["时间"] = result["发布日期"].astype(str) + " " + result["发布时间"].astype(str)

        # 截断内容长度
        result["内容"] = result["内容"].apply(lambda x: x[:80] + "..." if len(str(x)) > 80 else x)

        # 选择列
        result = result[["时间", "标题", "内容"]].copy()

        return result.head(limit).reset_index(drop=True)

    @staticmethod
    def get_zt_pool(date: Optional[str] = None) -> pd.DataFrame:
        """
        获取涨停板池

        Args:
            date: 日期 YYYYMMDD (默认最新交易日)
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")

        df = ak.stock_zt_pool_em(date=date)
        if df.empty:
            return df

        # 选择关键列
        result = df[["序号", "代码", "名称", "涨跌幅", "最新价", "成交额", "封板资金", "首次封板时间", "连板数", "所属行业"]].copy()

        # 格式化
        result["涨跌幅"] = result["涨跌幅"].apply(lambda x: f"{x:.2f}%")
        result["成交额"] = result["成交额"].apply(lambda x: f"{x/1e8:.2f}亿" if x >= 1e8 else f"{x/1e4:.0f}万")
        result["封板资金"] = result["封板资金"].apply(lambda x: f"{x/1e8:.2f}亿" if x >= 1e8 else f"{x/1e4:.0f}万")

        return result.reset_index(drop=True)

    @staticmethod
    def get_hot_rank(limit: int = 50) -> pd.DataFrame:
        """
        获取人气排行榜 (东方财富)

        Args:
            limit: 返回数量
        """
        df = ak.stock_hot_rank_em()
        if df.empty:
            return df

        result = df[["当前排名", "代码", "股票名称", "最新价", "涨跌幅"]].copy()
        result = result.rename(columns={"股票名称": "名称"})
        result["涨跌幅"] = result["涨跌幅"].apply(lambda x: f"{x:.2f}%")

        # 清理代码格式
        result["代码"] = result["代码"].str.replace(r"^(SZ|SH)", "", regex=True)

        return result.head(limit).reset_index(drop=True)

    @staticmethod
    def get_lhb_detail(start_date: str, end_date: str, limit: int = 30) -> pd.DataFrame:
        """
        获取龙虎榜详情

        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            limit: 返回数量
        """
        df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        if df.empty:
            return df

        # 选择关键列
        result = df[["代码", "名称", "上榜日", "收盘价", "涨跌幅", "龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额", "上榜原因"]].copy()

        # 格式化
        result["涨跌幅"] = result["涨跌幅"].apply(lambda x: f"{x:.2f}%")
        for col in ["龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额"]:
            result[col] = result[col].apply(lambda x: f"{x/1e8:.2f}亿" if abs(x) >= 1e8 else f"{x/1e4:.0f}万")

        # 重命名
        result = result.rename(columns={
            "龙虎榜净买额": "净买额",
            "龙虎榜买入额": "买入额",
            "龙虎榜卖出额": "卖出额",
        })

        return result.head(limit).reset_index(drop=True)

    @staticmethod
    def get_market_fund_flow(days: int = 10) -> pd.DataFrame:
        """
        获取大盘资金流向

        Args:
            days: 天数
        """
        df = ak.stock_market_fund_flow()
        if df.empty:
            return df

        result = df.tail(days).copy()

        # 选择列并重命名
        result = result[["日期", "上证-收盘价", "上证-涨跌幅", "主力净流入-净额", "主力净流入-净占比",
                        "超大单净流入-净额", "大单净流入-净额", "中单净流入-净额", "小单净流入-净额"]].copy()

        # 格式化金额
        for col in ["主力净流入-净额", "超大单净流入-净额", "大单净流入-净额", "中单净流入-净额", "小单净流入-净额"]:
            result[col] = result[col].apply(lambda x: f"{x/1e8:.1f}亿")

        result = result.rename(columns={
            "上证-收盘价": "上证",
            "上证-涨跌幅": "涨跌%",
            "主力净流入-净额": "主力净流入",
            "主力净流入-净占比": "主力占比%",
            "超大单净流入-净额": "超大单",
            "大单净流入-净额": "大单",
            "中单净流入-净额": "中单",
            "小单净流入-净额": "小单",
        })

        return result.reset_index(drop=True)

    @staticmethod
    def get_market_pe(symbol: str = "上证", days: int = 30) -> pd.DataFrame:
        """
        获取市场市盈率

        Args:
            symbol: 市场类型 (上证, 深证, 创业板, 科创板)
            days: 天数
        """
        df = ak.stock_market_pe_lg(symbol=symbol)
        if df.empty:
            return df

        result = df.tail(days).copy()
        # 统一列名 (不同参数返回的列名可能不同)
        rename_map = {
            "总市值": "总市值(亿)",
            "市盈率": "PE",
            "平均市盈率": "PE",
        }
        result = result.rename(columns=rename_map)
        return result.reset_index(drop=True)

    @staticmethod
    def get_market_pb(symbol: str = "上证", days: int = 30) -> pd.DataFrame:
        """
        获取市场市净率

        Args:
            symbol: 市场类型 (上证, 深证, 创业板, 科创板)
            days: 天数
        """
        # PB API 只支持 "科创版"，不支持 "科创板"
        pb_symbol = symbol.replace("科创板", "科创版")
        df = ak.stock_market_pb_lg(symbol=pb_symbol)
        if df.empty:
            return df

        result = df.tail(days).copy()
        # 统一列名
        rename_map = {
            "总市值": "总市值(亿)",
            "市净率": "PB",
        }
        result = result.rename(columns=rename_map)
        return result.reset_index(drop=True)

    @staticmethod
    def get_stock_comment(limit: int = 50) -> pd.DataFrame:
        """
        获取股票综合评分

        Args:
            limit: 返回数量
        """
        df = ak.stock_comment_em()
        if df.empty:
            return df

        result = df[["序号", "代码", "名称", "最新价", "涨跌幅", "换手率", "机构参与度", "综合得分", "目前排名", "关注指数"]].copy()
        result["涨跌幅"] = result["涨跌幅"].apply(lambda x: f"{x:.2f}%")
        result["换手率"] = result["换手率"].apply(lambda x: f"{x:.2f}%")
        result["机构参与度"] = result["机构参与度"].apply(lambda x: f"{x*100:.1f}%")
        result["综合得分"] = result["综合得分"].apply(lambda x: f"{x:.1f}")

        return result.head(limit).reset_index(drop=True)

    @staticmethod
    def get_research_report(code: str, limit: int = 20) -> pd.DataFrame:
        """
        获取个股研报

        Args:
            code: 股票/ETF 代码
            limit: 返回数量
        """
        df = ak.stock_research_report_em(symbol=code)
        if df.empty:
            return df

        # 选择关键列
        cols = ["日期", "报告名称", "东财评级", "机构"]
        available = [c for c in cols if c in df.columns]
        result = df[available].copy()

        # 截断报告名称
        if "报告名称" in result.columns:
            result["报告名称"] = result["报告名称"].apply(lambda x: x[:40] + "..." if len(str(x)) > 40 else x)

        return result.head(limit).reset_index(drop=True)


# ============================================================================
# 市场情绪分析
# ============================================================================
class MarketSentiment:
    """市场情绪分析"""

    @staticmethod
    def get_market_activity() -> dict:
        """获取市场涨跌统计"""
        try:
            df = ak.stock_market_activity_legu()
            result = {}
            for _, row in df.iterrows():
                result[row["item"]] = row["value"]
            return result
        except Exception:
            return {}

    @staticmethod
    def get_north_flow() -> pd.DataFrame:
        """获取北向资金流向"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            # 只取北向数据
            north = df[df["资金方向"] == "北向"].copy()
            return north
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def get_margin_data(days: int = 5) -> pd.DataFrame:
        """获取融资融券数据"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days + 10)).strftime("%Y%m%d")
            df = ak.stock_margin_sse(start_date=start_date, end_date=end_date)
            df = df.head(days)
            return df
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def calculate_sentiment_score(activity: dict, margin_df: pd.DataFrame) -> dict:
        """
        计算综合情绪分数

        评分规则:
        - 涨跌比: 上涨/(上涨+下跌) * 40 分
        - 涨停数: >50 得 15 分, >30 得 10 分, >10 得 5 分
        - 跌停数: <10 得 15 分, <20 得 10 分, <30 得 5 分
        - 融资变化: 增加得 15 分, 减少得 0 分
        - 活跃度: >50% 得 15 分, >30% 得 10 分, 其他 5 分
        """
        score = 0
        details = []

        # 涨跌比 (40分)
        up = float(activity.get("上涨", 0))
        down = float(activity.get("下跌", 0))
        if up + down > 0:
            ratio = up / (up + down)
            ratio_score = ratio * 40
            score += ratio_score
            details.append(f"涨跌比 {ratio:.1%} (+{ratio_score:.0f}分)")

        # 涨停数 (15分)
        zt = float(activity.get("涨停", 0))
        if zt > 50:
            score += 15
            details.append(f"涨停 {zt:.0f} 家 (+15分)")
        elif zt > 30:
            score += 10
            details.append(f"涨停 {zt:.0f} 家 (+10分)")
        elif zt > 10:
            score += 5
            details.append(f"涨停 {zt:.0f} 家 (+5分)")
        else:
            details.append(f"涨停 {zt:.0f} 家 (+0分)")

        # 跌停数 (15分)
        dt = float(activity.get("跌停", 0))
        if dt < 10:
            score += 15
            details.append(f"跌停 {dt:.0f} 家 (+15分)")
        elif dt < 20:
            score += 10
            details.append(f"跌停 {dt:.0f} 家 (+10分)")
        elif dt < 30:
            score += 5
            details.append(f"跌停 {dt:.0f} 家 (+5分)")
        else:
            details.append(f"跌停 {dt:.0f} 家 (+0分)")

        # 融资变化 (15分)
        if not margin_df.empty and len(margin_df) >= 2:
            latest = float(margin_df.iloc[0]["融资余额"])
            prev = float(margin_df.iloc[1]["融资余额"])
            change = latest - prev
            if change > 0:
                score += 15
                details.append(f"融资余额 +{change/1e8:.1f}亿 (+15分)")
            else:
                details.append(f"融资余额 {change/1e8:.1f}亿 (+0分)")

        # 活跃度 (15分)
        activity_rate = activity.get("活跃度", "0%")
        if isinstance(activity_rate, str):
            activity_rate = float(activity_rate.rstrip("%"))
        if activity_rate > 50:
            score += 15
            details.append(f"活跃度 {activity_rate:.1f}% (+15分)")
        elif activity_rate > 30:
            score += 10
            details.append(f"活跃度 {activity_rate:.1f}% (+10分)")
        else:
            score += 5
            details.append(f"活跃度 {activity_rate:.1f}% (+5分)")

        # 情绪等级
        if score >= 80:
            level = "极度贪婪 🔴"
        elif score >= 60:
            level = "贪婪 🟠"
        elif score >= 40:
            level = "中性 🟡"
        elif score >= 20:
            level = "恐惧 🟢"
        else:
            level = "极度恐惧 🔵"

        return {
            "score": round(score, 1),
            "level": level,
            "details": details,
        }

    @staticmethod
    def generate_report() -> str:
        """生成市场情绪报告"""
        lines = []
        lines.append("=" * 50)
        lines.append("📊 市场情绪分析报告")
        lines.append("=" * 50)

        # 1. 涨跌统计
        activity = MarketSentiment.get_market_activity()
        if activity:
            stat_date = activity.get("统计日期", "未知")
            lines.append(f"\n📅 统计时间: {stat_date}")
            lines.append("\n### 涨跌统计")
            up = activity.get("上涨", 0)
            down = activity.get("下跌", 0)
            flat = activity.get("平盘", 0)
            zt = activity.get("涨停", 0)
            dt = activity.get("跌停", 0)
            lines.append(f"  上涨: {up:.0f} 家 | 下跌: {down:.0f} 家 | 平盘: {flat:.0f} 家")
            lines.append(f"  涨停: {zt:.0f} 家 | 跌停: {dt:.0f} 家")
            lines.append(f"  市场活跃度: {activity.get('活跃度', '-')}")

        # 2. 北向资金
        north_df = MarketSentiment.get_north_flow()
        if not north_df.empty:
            lines.append("\n### 北向资金 (沪深港通)")
            for _, row in north_df.iterrows():
                board = row.get("板块", "")
                net_flow = row.get("资金净流入", 0)
                lines.append(f"  {board}: 净流入 {net_flow:.2f} 亿")

        # 3. 融资融券
        margin_df = MarketSentiment.get_margin_data(5)
        if not margin_df.empty:
            lines.append("\n### 融资融券 (沪市)")
            latest = margin_df.iloc[0]
            balance = float(latest["融资余额"]) / 1e8
            buy = float(latest["融资买入额"]) / 1e8
            lines.append(f"  融资余额: {balance:.0f} 亿")
            lines.append(f"  融资买入: {buy:.0f} 亿")

            if len(margin_df) >= 2:
                prev = float(margin_df.iloc[1]["融资余额"]) / 1e8
                change = balance - prev
                trend = "📈" if change > 0 else "📉"
                lines.append(f"  较前日: {trend} {change:+.1f} 亿")

        # 4. 情绪评分
        sentiment = MarketSentiment.calculate_sentiment_score(activity, margin_df)
        lines.append("\n### 情绪评分")
        lines.append(f"  综合得分: {sentiment['score']:.0f} / 100")
        lines.append(f"  情绪等级: {sentiment['level']}")
        lines.append("\n  评分明细:")
        for detail in sentiment["details"]:
            lines.append(f"    - {detail}")

        # 5. 情绪解读
        lines.append("\n### 情绪解读")
        score = sentiment["score"]
        if score >= 60:
            lines.append("  ⚠️ 市场情绪偏热，注意追高风险")
        elif score >= 40:
            lines.append("  📊 市场情绪中性，多空分歧明显")
        else:
            lines.append("  💡 市场情绪偏冷，可关注超跌机会")

        lines.append("\n" + "=" * 50)
        lines.append("⚠️ 以上数据仅供参考，不构成投资建议")
        lines.append("=" * 50)

        return "\n".join(lines)


# ============================================================================
# BaoStock 数据源 (无需注册)
# ============================================================================
class BaoStockSource:
    """BaoStock 数据源 - 擅长财务指标和指数成分股"""

    @staticmethod
    def _query_to_df(rs) -> pd.DataFrame:
        """将 BaoStock 查询结果转换为 DataFrame"""
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data, columns=rs.fields)

    @staticmethod
    def _convert_code(code: str) -> str:
        """转换代码格式：510050 -> sh.510050"""
        code = code.strip()
        if "." in code:
            return code
        # 根据代码前缀判断市场
        if code.startswith(("5", "6", "9")):
            return f"sh.{code}"
        elif code.startswith(("0", "1", "2", "3")):
            return f"sz.{code}"
        return f"sh.{code}"

    @staticmethod
    def get_index_constituents(index: str = "hs300") -> pd.DataFrame:
        """
        获取指数成分股

        Args:
            index: 指数类型 - hs300(沪深300), sz50(上证50), zz500(中证500)
        """
        import baostock as bs

        lg = bs.login()
        try:
            if index.lower() in ["hs300", "沪深300", "300"]:
                rs = bs.query_hs300_stocks()
                index_name = "沪深300"
            elif index.lower() in ["sz50", "上证50", "50"]:
                rs = bs.query_sz50_stocks()
                index_name = "上证50"
            elif index.lower() in ["zz500", "中证500", "500"]:
                rs = bs.query_zz500_stocks()
                index_name = "中证500"
            else:
                raise ValueError(f"不支持的指数: {index}，支持: hs300, sz50, zz500")

            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            # 重命名列
            df = df.rename(columns={
                "updateDate": "更新日期",
                "code": "代码",
                "code_name": "名称",
            })
            df["指数"] = index_name
            return df[["指数", "代码", "名称", "更新日期"]]
        finally:
            bs.logout()

    @staticmethod
    def get_profit_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取盈利能力指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_profit_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            # 重命名列
            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "roeAvg": "ROE(平均)",
                "npMargin": "净利率",
                "gpMargin": "毛利率",
                "netProfit": "净利润",
                "epsTTM": "EPS(TTM)",
                "MBRevenue": "主营收入",
                "totalShare": "总股本",
                "liqaShare": "流通股本",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_growth_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取成长能力指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_growth_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "YOYEquity": "净资产同比(%)",
                "YOYAsset": "总资产同比(%)",
                "YOYNI": "净利润同比(%)",
                "YOYEPSBasic": "基本EPS同比(%)",
                "YOYPNI": "归母净利润同比(%)",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_dupont_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取杜邦分析指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_dupont_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "dupontROE": "ROE",
                "dupontAssetStoEquity": "权益乘数",
                "dupontAssetTurn": "资产周转率",
                "dupontPnitoni": "净利润/利润总额",
                "dupontNitogr": "利润总额/营业总收入",
                "dupontTaxBurden": "税负",
                "dupontIntburden": "利息负担",
                "dupontEbittogr": "息税前利润/营收",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_operation_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取营运能力指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_operation_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "NRTurnRatio": "应收账款周转率",
                "NRTurnDays": "应收账款周转天数",
                "INVTurnRatio": "存货周转率",
                "INVTurnDays": "存货周转天数",
                "CATurnRatio": "流动资产周转率",
                "AssetTurnRatio": "总资产周转率",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_balance_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取资产负债表指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_balance_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "currentRatio": "流动比率",
                "quickRatio": "速动比率",
                "cashRatio": "现金比率",
                "YOYLiability": "负债同比(%)",
                "liabilityToAsset": "资产负债率",
                "assetToEquity": "权益乘数",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_cash_flow_data(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取现金流量指标"""
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_cash_flow_data(code=bs_code, year=year, quarter=quarter)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "pubDate": "公布日期",
                "statDate": "统计日期",
                "CAToAsset": "现金资产比",
                "NCAToAsset": "非现金资产比",
                "tangibleAssetToAsset": "有形资产比",
                "eaborToInterestBearDebt": "息税前利润/带息债务",
                "capitalizedToDbt": "资本化比",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_financial_summary(code: str, year: int, quarter: int) -> str:
        """获取综合财务分析报告"""
        lines = []
        lines.append(f"\n{'=' * 60}")
        lines.append(f"📊 财务分析报告 - {code} ({year}Q{quarter})")
        lines.append("=" * 60)

        # 盈利能力
        try:
            profit_df = BaoStockSource.get_profit_data(code, year, quarter)
            if not profit_df.empty:
                row = profit_df.iloc[0]
                lines.append("\n📈 盈利能力")
                lines.append("-" * 40)
                if "ROE(平均)" in row and row["ROE(平均)"]:
                    lines.append(f"  ROE: {float(row['ROE(平均)'])*100:.2f}%")
                if "毛利率" in row and row["毛利率"]:
                    lines.append(f"  毛利率: {float(row['毛利率'])*100:.2f}%")
                if "净利率" in row and row["净利率"]:
                    lines.append(f"  净利率: {float(row['净利率'])*100:.2f}%")
                if "EPS(TTM)" in row and row["EPS(TTM)"]:
                    lines.append(f"  EPS(TTM): {float(row['EPS(TTM)']):.2f}")
        except Exception:
            pass

        # 成长能力
        try:
            growth_df = BaoStockSource.get_growth_data(code, year, quarter)
            if not growth_df.empty:
                row = growth_df.iloc[0]
                lines.append("\n📊 成长能力")
                lines.append("-" * 40)
                if "净利润同比(%)" in row and row["净利润同比(%)"]:
                    lines.append(f"  净利润同比: {float(row['净利润同比(%)'])*100:.2f}%")
                if "总资产同比(%)" in row and row["总资产同比(%)"]:
                    lines.append(f"  总资产同比: {float(row['总资产同比(%)'])*100:.2f}%")
                if "净资产同比(%)" in row and row["净资产同比(%)"]:
                    lines.append(f"  净资产同比: {float(row['净资产同比(%)'])*100:.2f}%")
        except Exception:
            pass

        # 杜邦分析
        try:
            dupont_df = BaoStockSource.get_dupont_data(code, year, quarter)
            if not dupont_df.empty:
                row = dupont_df.iloc[0]
                lines.append("\n🔍 杜邦分析")
                lines.append("-" * 40)
                if "ROE" in row and row["ROE"]:
                    lines.append(f"  ROE: {float(row['ROE'])*100:.2f}%")
                if "权益乘数" in row and row["权益乘数"]:
                    lines.append(f"  权益乘数: {float(row['权益乘数']):.2f}")
                if "资产周转率" in row and row["资产周转率"]:
                    lines.append(f"  资产周转率: {float(row['资产周转率']):.2f}")
        except Exception:
            pass

        # 偿债能力
        try:
            balance_df = BaoStockSource.get_balance_data(code, year, quarter)
            if not balance_df.empty:
                row = balance_df.iloc[0]
                lines.append("\n💰 偿债能力")
                lines.append("-" * 40)
                if "流动比率" in row and row["流动比率"]:
                    lines.append(f"  流动比率: {float(row['流动比率']):.2f}")
                if "速动比率" in row and row["速动比率"]:
                    lines.append(f"  速动比率: {float(row['速动比率']):.2f}")
                if "资产负债率" in row and row["资产负债率"]:
                    lines.append(f"  资产负债率: {float(row['资产负债率'])*100:.2f}%")
        except Exception:
            pass

        lines.append("\n" + "=" * 60)
        lines.append("数据来源: BaoStock")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def get_dividend_data(code: str, year: str = "", year_type: str = "report") -> pd.DataFrame:
        """
        获取股票分红数据

        Args:
            code: 股票代码
            year: 年份 (如 2024)
            year_type: 年份类型 report-预案公告日 operate-除权除息日
        """
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_dividend_data(code=bs_code, year=year, yearType=year_type)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "dividPreNoticeDate": "预案公告日",
                "dividAgmPum498Date": "股东大会日",
                "dividPlanAnnounceDate": "分红计划公告日",
                "dividPlanDate": "分红实施公告日",
                "dividRegistDate": "股权登记日",
                "dividOperateDate": "除权除息日",
                "dividPayDate": "派息日",
                "dividStockMarketDate": "红股上市日",
                "dividCashPsBeforeTax": "税前每股派息",
                "dividCashPsAfterTax": "税后每股派息",
                "dividStocksPs": "每股送股",
                "dividCashStock": "每股转增",
                "dividReserveToStockPs": "每股公积金转增",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_forecast_report(code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取业绩预告

        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
        """
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_forecast_report(code=bs_code, start_date=start_date, end_date=end_date)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "code": "代码",
                "publishDate": "发布日期",
                "profitForcastExpPubDate": "预计公告日",
                "profitForcastType": "业绩类型",
                "profitForcastAbstract": "业绩摘要",
                "profitForcastChgPctUp": "预计增幅上限(%)",
                "profitForcastChgPctDwn": "预计增幅下限(%)",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()

    @staticmethod
    def get_stock_industry(code: str) -> pd.DataFrame:
        """
        获取股票行业分类

        Args:
            code: 股票代码
        """
        import baostock as bs

        bs_code = BaoStockSource._convert_code(code)
        lg = bs.login()
        try:
            rs = bs.query_stock_industry(code=bs_code)
            df = BaoStockSource._query_to_df(rs)
            if df.empty:
                return df

            column_map = {
                "updateDate": "更新日期",
                "code": "代码",
                "code_name": "名称",
                "industry": "行业",
                "industryClassification": "行业分类",
            }
            return df.rename(columns=column_map)
        finally:
            bs.logout()


# ============================================================================
# 技术指标计算
# ============================================================================
class TechnicalIndicators:
    """技术指标计算器"""

    @staticmethod
    def ma(close: pd.Series, period: int) -> pd.Series:
        """简单移动平均线 (SMA)"""
        return close.rolling(window=period).mean()

    @staticmethod
    def ema(close: pd.Series, period: int) -> pd.Series:
        """指数移动平均线 (EMA)"""
        return close.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(
        close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD 指标
        返回: (DIF, DEA, MACD柱)
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_hist = (dif - dea) * 2
        return dif, dea, macd_hist

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI 相对强弱指标
        RSI = 100 - 100 / (1 + RS)
        RS = 平均涨幅 / 平均跌幅
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def kdj(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        KDJ 随机指标
        返回: (K, D, J)
        """
        lowest_low = low.rolling(window=n).min()
        highest_high = high.rolling(window=n).max()

        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)

        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        return k, d, j

    @staticmethod
    def boll(
        close: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        布林带 (Bollinger Bands)
        返回: (上轨, 中轨, 下轨)
        """
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 包含 OHLCV 数据的 DataFrame
                需要列: 日期, 开盘, 最高, 最低, 收盘, 成交量

        Returns:
            添加了技术指标的 DataFrame
        """
        result = df.copy()

        # 标准化列名
        col_map = {
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "日期": "date",
        }
        for cn, en in col_map.items():
            if cn in result.columns:
                result = result.rename(columns={cn: en})

        close = result["close"].astype(float)
        high = result["high"].astype(float) if "high" in result.columns else close
        low = result["low"].astype(float) if "low" in result.columns else close

        # MA 移动平均线
        for p in [5, 10, 20, 60]:
            result[f"MA{p}"] = TechnicalIndicators.ma(close, p).round(4)

        # MACD
        dif, dea, macd_hist = TechnicalIndicators.macd(close)
        result["DIF"] = dif.round(4)
        result["DEA"] = dea.round(4)
        result["MACD"] = macd_hist.round(4)

        # RSI
        result["RSI6"] = TechnicalIndicators.rsi(close, 6).round(2)
        result["RSI12"] = TechnicalIndicators.rsi(close, 12).round(2)
        result["RSI14"] = TechnicalIndicators.rsi(close, 14).round(2)

        # KDJ
        k, d, j = TechnicalIndicators.kdj(high, low, close)
        result["K"] = k.round(2)
        result["D"] = d.round(2)
        result["J"] = j.round(2)

        # BOLL
        upper, middle, lower = TechnicalIndicators.boll(close)
        result["BOLL_UP"] = upper.round(4)
        result["BOLL_MID"] = middle.round(4)
        result["BOLL_LOW"] = lower.round(4)

        return result

    @staticmethod
    def get_latest_summary(df: pd.DataFrame, code: str, name: str = "") -> dict:
        """获取最新技术指标摘要"""
        if df.empty:
            return {}

        latest = df.iloc[-1]

        summary = {
            "代码": code,
            "名称": name,
            "收盘价": latest.get("close", "-"),
            "MA5": latest.get("MA5", "-"),
            "MA10": latest.get("MA10", "-"),
            "MA20": latest.get("MA20", "-"),
            "MA60": latest.get("MA60", "-"),
            "DIF": latest.get("DIF", "-"),
            "DEA": latest.get("DEA", "-"),
            "MACD": latest.get("MACD", "-"),
            "RSI14": latest.get("RSI14", "-"),
            "K": latest.get("K", "-"),
            "D": latest.get("D", "-"),
            "J": latest.get("J", "-"),
            "BOLL_UP": latest.get("BOLL_UP", "-"),
            "BOLL_MID": latest.get("BOLL_MID", "-"),
            "BOLL_LOW": latest.get("BOLL_LOW", "-"),
        }

        return summary

    @staticmethod
    def interpret_signals(df: pd.DataFrame) -> list[str]:
        """解读技术指标信号"""
        if df.empty or len(df) < 2:
            return []

        signals = []
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = latest.get("close", 0)

        # MA 趋势
        ma5 = latest.get("MA5")
        ma10 = latest.get("MA10")
        ma20 = latest.get("MA20")
        if ma5 and ma10 and ma20:
            if close > ma5 > ma10 > ma20:
                signals.append("📈 均线多头排列 (MA5>MA10>MA20)")
            elif close < ma5 < ma10 < ma20:
                signals.append("📉 均线空头排列 (MA5<MA10<MA20)")

        # MACD 金叉/死叉
        dif = latest.get("DIF", 0)
        dea = latest.get("DEA", 0)
        prev_dif = prev.get("DIF", 0)
        prev_dea = prev.get("DEA", 0)
        if dif and dea and prev_dif and prev_dea:
            if prev_dif <= prev_dea and dif > dea:
                signals.append("🔵 MACD 金叉 (DIF 上穿 DEA)")
            elif prev_dif >= prev_dea and dif < dea:
                signals.append("🔴 MACD 死叉 (DIF 下穿 DEA)")

        # RSI 超买超卖
        rsi = latest.get("RSI14", 50)
        if rsi:
            if rsi > 80:
                signals.append(f"⚠️ RSI 超买区 ({rsi:.1f})")
            elif rsi < 20:
                signals.append(f"⚠️ RSI 超卖区 ({rsi:.1f})")

        # KDJ 超买超卖
        k = latest.get("K", 50)
        d = latest.get("D", 50)
        j = latest.get("J", 50)
        if k and d and j:
            if j > 100:
                signals.append(f"⚠️ KDJ 超买 (J={j:.1f})")
            elif j < 0:
                signals.append(f"⚠️ KDJ 超卖 (J={j:.1f})")

        # BOLL 突破
        boll_up = latest.get("BOLL_UP")
        boll_low = latest.get("BOLL_LOW")
        if boll_up and boll_low:
            if close > boll_up:
                signals.append("⬆️ 突破布林带上轨")
            elif close < boll_low:
                signals.append("⬇️ 跌破布林带下轨")

        return signals


# ============================================================================
# 输出格式化
# ============================================================================
def format_output(df: pd.DataFrame, output_format: str = "table") -> str:
    """格式化输出"""
    if df.empty:
        return "未找到符合条件的数据"

    if output_format == "json":
        return df.to_json(orient="records", force_ascii=False, indent=2)
    elif output_format == "csv":
        return df.to_csv(index=False)
    else:
        return df.to_markdown(index=False)


def format_number(val, decimals: int = 2) -> str:
    """格式化数字，大数字用亿/万"""
    if pd.isna(val):
        return "-"
    val = float(val)
    if abs(val) >= 1e8:
        return f"{val/1e8:.{decimals}f}亿"
    elif abs(val) >= 1e4:
        return f"{val/1e4:.{decimals}f}万"
    else:
        return f"{val:.{decimals}f}"


# ============================================================================
# CLI 主程序
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ETF 分析工具 - 默认使用 AkShare 数据源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询 ETF 实时行情 (AkShare, 免费)
  python main.py quote 510050
  python main.py quote 上证50
  python main.py quote 510050,510300,159915

  # 搜索 ETF
  python main.py search 沪深300
  python main.py search 医药

  # 获取历史行情
  python main.py hist 510050 --days 30
  python main.py hist 510300 --start 20250101 --end 20250127

  # 获取 ETF 列表 (按成交额排序)
  python main.py list --limit 20

常用 ETF 别名:
  宽基: 上证50, 沪深300, 中证500, 中证1000, 创业板, 科创50
  行业: 证券etf, 银行etf, 医药etf, 消费etf, 新能源车, 芯片etf, 军工etf
  跨境: 纳指etf, 标普500, 恒生科技, 恒生etf, 日经etf
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # quote 命令 - 实时行情
    quote_parser = subparsers.add_parser("quote", help="获取 ETF 实时行情")
    quote_parser.add_argument(
        "codes", type=str, help="ETF 代码或名称，多个用逗号分隔"
    )
    quote_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # search 命令 - 搜索
    search_parser = subparsers.add_parser("search", help="搜索 ETF")
    search_parser.add_argument("keyword", type=str, help="搜索关键词")
    search_parser.add_argument("--limit", type=int, default=20, help="返回数量限制")
    search_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # hist 命令 - 历史行情
    hist_parser = subparsers.add_parser("hist", help="获取 ETF 历史行情")
    hist_parser.add_argument("code", type=str, help="ETF 代码或名称")
    hist_parser.add_argument("--days", type=int, default=30, help="最近 N 天 (默认 30)")
    hist_parser.add_argument("--start", type=str, help="开始日期 YYYYMMDD")
    hist_parser.add_argument("--end", type=str, help="结束日期 YYYYMMDD")
    hist_parser.add_argument(
        "--period",
        type=str,
        default="daily",
        choices=["daily", "weekly", "monthly"],
        help="周期",
    )
    hist_parser.add_argument(
        "--adjust",
        type=str,
        default="qfq",
        choices=["qfq", "hfq", ""],
        help="复权类型: qfq-前复权, hfq-后复权, 空-不复权",
    )
    hist_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # list 命令 - ETF 列表
    list_parser = subparsers.add_parser("list", help="获取 ETF 列表")
    list_parser.add_argument("--limit", type=int, default=20, help="返回数量限制")
    list_parser.add_argument(
        "--sort",
        type=str,
        default="成交额",
        help="排序字段 (默认: 成交额)",
    )
    list_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # premium 命令 - 溢价率
    premium_parser = subparsers.add_parser("premium", help="获取 ETF 溢价率")
    premium_parser.add_argument(
        "codes",
        type=str,
        nargs="?",
        help="ETF 代码或名称，多个用逗号分隔 (不指定则显示全部)",
    )
    premium_parser.add_argument("--limit", type=int, default=20, help="返回数量限制")
    premium_parser.add_argument(
        "--sort",
        type=str,
        default="折价率",
        help="排序字段 (默认: 折价率)",
    )
    premium_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # indicator 命令 - 技术指标
    ind_parser = subparsers.add_parser("indicator", help="获取 ETF 技术指标")
    ind_parser.add_argument("code", type=str, help="ETF 代码或名称")
    ind_parser.add_argument("--days", type=int, default=120, help="计算用历史天数 (默认 120)")
    ind_parser.add_argument(
        "--indicators",
        type=str,
        default="all",
        help="指标类型: all, ma, macd, rsi, kdj, boll (多个用逗号分隔)",
    )
    ind_parser.add_argument(
        "--show-history",
        action="store_true",
        help="显示历史数据而非仅最新值",
    )
    ind_parser.add_argument("--limit", type=int, default=10, help="历史数据显示行数")
    ind_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # sentiment 命令 - 市场情绪
    subparsers.add_parser("sentiment", help="市场情绪分析面板")

    # constituent 命令 - 指数成分股 (BaoStock)
    const_parser = subparsers.add_parser("constituent", help="查询指数成分股 (BaoStock)")
    const_parser.add_argument(
        "index",
        type=str,
        nargs="?",
        default="hs300",
        help="指数: hs300/沪深300, sz50/上证50, zz500/中证500 (默认: hs300)",
    )
    const_parser.add_argument("--limit", type=int, help="返回数量限制")
    const_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # finance 命令 - 财务分析 (BaoStock)
    _default_year, _default_quarter = get_last_quarter()
    fin_parser = subparsers.add_parser("finance", help="财务指标分析 (BaoStock)")
    fin_parser.add_argument("code", type=str, help="股票代码 (如: 600519, sh.600519)")
    fin_parser.add_argument(
        "--year",
        type=int,
        default=_default_year,
        help=f"年份 (默认: {_default_year})",
    )
    fin_parser.add_argument(
        "--quarter",
        type=int,
        default=_default_quarter,
        help=f"季度 1-4 (默认: {_default_quarter}, 上一季度)",
    )
    fin_parser.add_argument(
        "--type",
        type=str,
        default="summary",
        choices=["summary", "profit", "growth", "dupont", "balance", "cashflow", "operation"],
        help="指标类型: summary-综合, profit-盈利, growth-成长, dupont-杜邦, balance-负债, cashflow-现金流, operation-营运",
    )
    fin_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # holding 命令 - ETF 持仓
    hold_parser = subparsers.add_parser("holding", help="ETF 持仓明细 (前十大)")
    hold_parser.add_argument("code", type=str, help="ETF 代码 (如 510050)")
    hold_parser.add_argument("--year", type=str, default="2024", help="年份 (默认: 2024)")
    hold_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # industry 命令 - 行业配置
    ind_alloc_parser = subparsers.add_parser("industry", help="ETF 行业配置")
    ind_alloc_parser.add_argument("code", type=str, help="ETF 代码")
    ind_alloc_parser.add_argument("--year", type=str, default="2024", help="年份 (默认: 2024)")
    ind_alloc_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # change 命令 - 持仓变动
    change_parser = subparsers.add_parser("change", help="ETF 持仓变动 (买入/卖出)")
    change_parser.add_argument("code", type=str, help="ETF 代码")
    change_parser.add_argument("--year", type=str, default="2024", help="年份 (默认: 2024)")
    change_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # flow 命令 - 资金流向
    flow_parser = subparsers.add_parser("flow", help="资金流向 (主力/散户)")
    flow_parser.add_argument("code", type=str, help="ETF 代码或名称")
    flow_parser.add_argument("--days", type=int, default=10, help="天数 (默认 10)")
    flow_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # scale 命令 - ETF 规模
    scale_parser = subparsers.add_parser("scale", help="ETF 规模数据")
    scale_parser.add_argument(
        "--exchange",
        type=str,
        default="all",
        choices=["sse", "szse", "all"],
        help="交易所: sse-上交所, szse-深交所, all-全部",
    )
    scale_parser.add_argument("--limit", type=int, default=20, help="返回数量")
    scale_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # dividend 命令 - 分红历史
    div_parser = subparsers.add_parser("dividend", help="ETF 分红历史")
    div_parser.add_argument("--limit", type=int, default=20, help="返回数量")
    div_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # rating 命令 - 基金评级
    rating_parser = subparsers.add_parser("rating", help="ETF 基金评级")
    rating_parser.add_argument("code", type=str, nargs="?", help="ETF 代码 (可选)")
    rating_parser.add_argument("--limit", type=int, default=20, help="返回数量")
    rating_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # news 命令 - 新闻快讯
    news_parser = subparsers.add_parser("news", help="获取新闻/快讯")
    news_parser.add_argument("code", type=str, nargs="?", help="ETF/股票代码 (不指定则获取市场快讯)")
    news_parser.add_argument("--market", action="store_true", help="获取市场快讯 (财联社)")
    news_parser.add_argument("--limit", type=int, default=15, help="返回数量 (默认 15)")
    news_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # zt 命令 - 涨停板池
    zt_parser = subparsers.add_parser("zt", help="涨停板池")
    zt_parser.add_argument("--date", type=str, help="日期 YYYYMMDD (默认最新)")
    zt_parser.add_argument("--limit", type=int, default=30, help="返回数量")
    zt_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # hot 命令 - 人气排行
    hot_parser = subparsers.add_parser("hot", help="人气排行榜 (东方财富)")
    hot_parser.add_argument("--limit", type=int, default=30, help="返回数量")
    hot_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # lhb 命令 - 龙虎榜
    lhb_parser = subparsers.add_parser("lhb", help="龙虎榜详情")
    lhb_parser.add_argument("--days", type=int, default=5, help="最近 N 天 (默认 5)")
    lhb_parser.add_argument("--limit", type=int, default=30, help="返回数量")
    lhb_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # marketflow 命令 - 大盘资金流
    mf_parser = subparsers.add_parser("marketflow", help="大盘资金流向")
    mf_parser.add_argument("--days", type=int, default=10, help="天数 (默认 10)")
    mf_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # valuation 命令 - 市场估值
    val_parser = subparsers.add_parser("valuation", help="市场估值 (PE/PB)")
    val_parser.add_argument(
        "--market",
        type=str,
        default="上证",
        help="市场: 上证, 深证, 创业板, 科创板",
    )
    val_parser.add_argument("--days", type=int, default=30, help="天数 (默认 30)")
    val_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # comment 命令 - 综合评分
    comment_parser = subparsers.add_parser("comment", help="股票综合评分")
    comment_parser.add_argument("--limit", type=int, default=30, help="返回数量")
    comment_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # report 命令 - 研报
    report_parser = subparsers.add_parser("report", help="个股研报")
    report_parser.add_argument("code", type=str, help="股票/ETF 代码")
    report_parser.add_argument("--limit", type=int, default=15, help="返回数量")
    report_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # forecast 命令 - 业绩预告 (BaoStock)
    forecast_parser = subparsers.add_parser("forecast", help="业绩预告 (BaoStock)")
    forecast_parser.add_argument("code", type=str, help="股票代码")
    forecast_parser.add_argument("--days", type=int, default=365, help="查询天数范围 (默认 365)")
    forecast_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # stockindustry 命令 - 行业分类 (BaoStock)
    si_parser = subparsers.add_parser("stockindustry", help="股票行业分类 (BaoStock)")
    si_parser.add_argument("code", type=str, help="股票代码")
    si_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    # stockdividend 命令 - 股票分红 (BaoStock)
    sd_parser = subparsers.add_parser("stockdividend", help="股票分红历史 (BaoStock)")
    sd_parser.add_argument("code", type=str, help="股票代码")
    sd_parser.add_argument("--year", type=str, default="", help="年份 (如 2024)")
    sd_parser.add_argument(
        "--format",
        type=str,
        default="table",
        choices=["table", "json", "csv"],
        help="输出格式",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "quote":
            codes = [resolve_etf_code(c.strip()) for c in args.codes.split(",")]
            df = AkShareSource.get_etf_quote(codes)
            print(format_output(df, args.format))

        elif args.command == "search":
            df = AkShareSource.search_etf(args.keyword)
            if args.limit:
                df = df.head(args.limit)
            print(format_output(df, args.format))

        elif args.command == "hist":
            code = resolve_etf_code(args.code)

            # 处理日期范围：尊重单独提供的 --start 或 --end
            if args.start and args.end:
                # 两者都提供
                start_date = args.start
                end_date = args.end
            elif args.start:
                # 只提供 --start，结束日期为今天
                start_date = args.start
                end_date = datetime.now().strftime("%Y%m%d")
            elif args.end:
                # 只提供 --end，开始日期为 end 往前推 days 天
                end_dt = datetime.strptime(args.end, "%Y%m%d")
                start_date = (end_dt - timedelta(days=args.days)).strftime("%Y%m%d")
                end_date = args.end
            else:
                # 都没提供，使用默认的 days
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=args.days)).strftime(
                    "%Y%m%d"
                )

            df = AkShareSource.get_etf_hist(
                code=code,
                period=args.period,
                start_date=start_date,
                end_date=end_date,
                adjust=args.adjust,
            )
            print(format_output(df, args.format))

        elif args.command == "list":
            df = AkShareSource.get_etf_list()
            if args.sort in df.columns:
                df = df.sort_values(args.sort, ascending=False)
            if args.limit:
                df = df.head(args.limit)
            print(format_output(df, args.format))

        elif args.command == "premium":
            codes = None
            if args.codes:
                codes = [resolve_etf_code(c.strip()) for c in args.codes.split(",")]

            df = AkShareSource.get_etf_premium(codes)

            # 转换折价率为数值便于排序 (处理 "---" 等无效值)
            if "折价率" in df.columns:
                # 处理字符串或数值类型的折价率
                if df["折价率"].dtype == object:
                    # 字符串类型，去掉百分号
                    df["折价率_num"] = pd.to_numeric(
                        df["折价率"].astype(str).str.rstrip("%"), errors="coerce"
                    )
                else:
                    # 数值类型，直接使用
                    df["折价率_num"] = pd.to_numeric(df["折价率"], errors="coerce")
                # 过滤掉无效数据
                df = df.dropna(subset=["折价率_num"])
                if args.sort == "折价率":
                    df = df.sort_values("折价率_num", ascending=False)
                df = df.drop(columns=["折价率_num"])

            if args.limit and not args.codes:
                df = df.head(args.limit)

            print(format_output(df, args.format))

        elif args.command == "indicator":
            code = resolve_etf_code(args.code)

            # 获取历史数据用于计算指标
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")

            hist_df = AkShareSource.get_etf_hist(
                code=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if hist_df.empty:
                print(f"未找到 {code} 的历史数据")
                sys.exit(1)

            # 获取名称
            try:
                spot_df = AkShareSource.get_etf_spot()
                name_row = spot_df[spot_df["代码"] == code]
                name = name_row["名称"].iloc[0] if not name_row.empty else code
            except Exception:
                name = code

            # 计算所有技术指标
            df_full = TechnicalIndicators.calculate_all(hist_df)

            # 选择要显示的指标列 (仅用于历史数据显示)
            indicators = args.indicators.lower().split(",")
            base_cols = ["date", "close"] if "date" in df_full.columns else ["收盘"]

            if "all" in indicators:
                df_display = df_full
            else:
                ind_cols = []
                if "ma" in indicators:
                    ind_cols.extend(["MA5", "MA10", "MA20", "MA60"])
                if "macd" in indicators:
                    ind_cols.extend(["DIF", "DEA", "MACD"])
                if "rsi" in indicators:
                    ind_cols.extend(["RSI6", "RSI12", "RSI14"])
                if "kdj" in indicators:
                    ind_cols.extend(["K", "D", "J"])
                if "boll" in indicators:
                    ind_cols.extend(["BOLL_UP", "BOLL_MID", "BOLL_LOW"])

                available = base_cols + [c for c in ind_cols if c in df_full.columns]
                df_display = df_full[available]

            if args.show_history:
                # 显示历史数据
                output_df = df_display.tail(args.limit)
                print(f"\n{name} ({code}) 技术指标 (最近 {len(output_df)} 天)")
                print(format_output(output_df, args.format))
            else:
                # 只显示最新指标摘要 (始终使用完整指标)
                summary = TechnicalIndicators.get_latest_summary(df_full, code, name)
                summary_df = pd.DataFrame([summary])
                print(f"\n{name} ({code}) 最新技术指标")
                print(format_output(summary_df.T.reset_index(), args.format))

                # 显示信号解读 (始终使用完整指标)
                signals = TechnicalIndicators.interpret_signals(df_full)
                if signals:
                    print("\n📊 信号解读:")
                    for sig in signals:
                        print(f"  {sig}")
                else:
                    print("\n📊 当前无明显技术信号")

        elif args.command == "sentiment":
            report = MarketSentiment.generate_report()
            print(report)

        elif args.command == "constituent":
            df = BaoStockSource.get_index_constituents(args.index)
            if args.limit:
                df = df.head(args.limit)
            print(format_output(df, args.format))

        elif args.command == "finance":
            code = args.code
            year = args.year
            quarter = args.quarter

            if args.type == "summary":
                report = BaoStockSource.get_financial_summary(code, year, quarter)
                print(report)
            else:
                type_map = {
                    "profit": BaoStockSource.get_profit_data,
                    "growth": BaoStockSource.get_growth_data,
                    "dupont": BaoStockSource.get_dupont_data,
                    "balance": BaoStockSource.get_balance_data,
                    "cashflow": BaoStockSource.get_cash_flow_data,
                    "operation": BaoStockSource.get_operation_data,
                }
                df = type_map[args.type](code, year, quarter)
                if df.empty:
                    print(f"未找到 {code} 在 {year}Q{quarter} 的财务数据", file=sys.stderr)
                    sys.exit(1)
                print(f"\n{code} {year}Q{quarter} 财务指标 ({args.type})")
                print(format_output(df.T.reset_index(), args.format))

        elif args.command == "holding":
            code = resolve_etf_code(args.code)
            df = AkShareSource.get_etf_holding(code, args.year)
            if df.empty:
                print(f"未找到 {code} 的持仓数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n{code} 持仓明细 ({args.year})")
            print(format_output(df, args.format))

        elif args.command == "industry":
            code = resolve_etf_code(args.code)
            df = AkShareSource.get_etf_industry(code, args.year)
            if df.empty:
                print(f"未找到 {code} 的行业配置数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n{code} 行业配置 ({args.year})")
            print(format_output(df, args.format))

        elif args.command == "change":
            code = resolve_etf_code(args.code)
            df = AkShareSource.get_etf_holding_change(code, args.year)
            if df.empty:
                print(f"未找到 {code} 的持仓变动数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n{code} 持仓变动 ({args.year})")
            print(format_output(df, args.format))

        elif args.command == "flow":
            code = resolve_etf_code(args.code)
            # 判断市场
            market = "sz" if code.startswith(("15", "16")) else "sh"
            df = AkShareSource.get_fund_flow(code, market, args.days)
            if df.empty:
                print(f"未找到 {code} 的资金流向数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n{code} 资金流向 (最近 {args.days} 天)")
            print(format_output(df, args.format))

        elif args.command == "scale":
            df = AkShareSource.get_etf_scale(args.exchange)
            if df.empty:
                print("未找到 ETF 规模数据", file=sys.stderr)
                sys.exit(1)
            if args.limit:
                df = df.head(args.limit)
            print(f"\nETF 规模数据")
            print(format_output(df, args.format))

        elif args.command == "dividend":
            df = AkShareSource.get_etf_dividend()
            if df.empty:
                print("未找到分红数据", file=sys.stderr)
                sys.exit(1)
            if args.limit:
                df = df.tail(args.limit)
            print(f"\nETF 分红历史")
            print(format_output(df, args.format))

        elif args.command == "rating":
            df = AkShareSource.get_fund_rating(args.code)
            if df.empty:
                print("未找到评级数据", file=sys.stderr)
                sys.exit(1)
            if args.limit and not args.code:
                df = df.head(args.limit)
            print(f"\nETF 基金评级")
            print(format_output(df, args.format))

        elif args.command == "news":
            if args.market or not args.code:
                # 市场快讯
                df = AkShareSource.get_market_news(args.limit)
                if df.empty:
                    print("未找到市场快讯", file=sys.stderr)
                    sys.exit(1)
                print(f"\n📰 市场快讯 (财联社)")
                print(format_output(df, args.format))
            else:
                # 个股/ETF 新闻
                code = resolve_etf_code(args.code)
                df = AkShareSource.get_stock_news(code, args.limit)
                if df.empty:
                    print(f"未找到 {code} 相关新闻", file=sys.stderr)
                    sys.exit(1)
                print(f"\n📰 {code} 相关新闻")
                print(format_output(df, args.format))

        elif args.command == "zt":
            df = AkShareSource.get_zt_pool(args.date)
            if df.empty:
                print("未找到涨停板数据", file=sys.stderr)
                sys.exit(1)
            if args.limit:
                df = df.head(args.limit)
            date_str = args.date if args.date else "今日"
            print(f"\n🔴 涨停板池 ({date_str})")
            print(format_output(df, args.format))

        elif args.command == "hot":
            df = AkShareSource.get_hot_rank(args.limit)
            if df.empty:
                print("未找到人气排行数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n🔥 人气排行榜 (东方财富)")
            print(format_output(df, args.format))

        elif args.command == "lhb":
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")
            df = AkShareSource.get_lhb_detail(start_date, end_date, args.limit)
            if df.empty:
                print("未找到龙虎榜数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n🐉 龙虎榜详情 (最近 {args.days} 天)")
            print(format_output(df, args.format))

        elif args.command == "marketflow":
            df = AkShareSource.get_market_fund_flow(args.days)
            if df.empty:
                print("未找到大盘资金流数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n💰 大盘资金流向 (最近 {args.days} 天)")
            print(format_output(df, args.format))

        elif args.command == "valuation":
            market = args.market
            pe_df = AkShareSource.get_market_pe(market, args.days)
            pb_df = AkShareSource.get_market_pb(market, args.days)

            print(f"\n📊 市场估值 - {market} (最近 {args.days} 天)")

            if not pe_df.empty:
                print("\n### 市盈率 (PE)")
                print(format_output(pe_df, args.format))

                # 显示最新值和历史分位
                latest_pe = pe_df.iloc[-1]["PE"]
                print(f"\n当前 PE: {latest_pe:.2f}")

            if not pb_df.empty:
                print("\n### 市净率 (PB)")
                print(format_output(pb_df, args.format))

                latest_pb = pb_df.iloc[-1]["PB"]
                print(f"\n当前 PB: {latest_pb:.2f}")

        elif args.command == "comment":
            df = AkShareSource.get_stock_comment(args.limit)
            if df.empty:
                print("未找到综合评分数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n⭐ 股票综合评分")
            print(format_output(df, args.format))

        elif args.command == "report":
            code = resolve_etf_code(args.code)
            df = AkShareSource.get_research_report(code, args.limit)
            if df.empty:
                print(f"未找到 {code} 的研报", file=sys.stderr)
                sys.exit(1)
            print(f"\n📋 {code} 研报")
            print(format_output(df, args.format))

        elif args.command == "forecast":
            code = args.code
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
            df = BaoStockSource.get_forecast_report(code, start_date, end_date)
            if df.empty:
                print(f"未找到 {code} 的业绩预告", file=sys.stderr)
                sys.exit(1)
            print(f"\n📈 {code} 业绩预告")
            print(format_output(df, args.format))

        elif args.command == "stockindustry":
            code = args.code
            df = BaoStockSource.get_stock_industry(code)
            if df.empty:
                print(f"未找到 {code} 的行业分类", file=sys.stderr)
                sys.exit(1)
            print(f"\n🏭 {code} 行业分类")
            print(format_output(df, args.format))

        elif args.command == "stockdividend":
            code = args.code
            df = BaoStockSource.get_dividend_data(code, args.year)
            if df.empty:
                print(f"未找到 {code} 的分红数据", file=sys.stderr)
                sys.exit(1)
            print(f"\n💵 {code} 分红历史")
            print(format_output(df, args.format))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

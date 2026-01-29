---
name: etf-basic
version: 0.0.1
author: Finance Skill Marketplace
description: |
  ETF/股票全方位分析工具。
  数据源：AkShare (行情/溢价率/技术指标/持仓/资金流向/新闻/涨停/龙虎榜/筹码分布), BaoStock (指数成分股/财务指标/业绩预告)
  触发词：ETF、基金、指数基金、上证50、沪深300、中证500、创业板、科创50、ETF行情、ETF历史、溢价率、技术指标、MA、MACD、RSI、KDJ、布林带、市场情绪、情绪分析、北向资金、融资融券、成分股、财报、财务指标、ROE、毛利率、净利率、杜邦分析、持仓、重仓股、行业配置、资金流向、主力资金、规模、份额、分红、评级、新闻、快讯、涨停、涨停板、人气榜、龙虎榜、游资、市场估值、PE、PB、研报、业绩预告、筹码分布、筹码、获利盘、套牢盘、成本分布、集中度
---

# ETF/股票分析工具

国内 ETF 和股票的全方位分析：实时行情、历史数据、溢价率、技术指标、市场情绪、资金流向、涨停板、龙虎榜、研报、业绩预告、筹码分布等。

## 数据源

| 数据源 | 功能 | 认证 |
|--------|------|------|
| **AkShare** | 行情、溢价率、技术指标、情绪、资金流向、涨停、龙虎榜、新闻、研报、筹码分布 | 无需认证 |
| **BaoStock** | 指数成分股、财务指标、业绩预告、行业分类 | 无需注册 |

## 命令总览 (28个)

| 类别 | 命令 | 功能 |
|------|------|------|
| **行情** | quote, search, hist, list | 实时/历史行情、搜索、排行 |
| **估值** | premium, indicator, valuation | 溢价率、技术指标、市场PE/PB |
| **情绪** | sentiment, comment | 市场情绪、综合评分 |
| **筹码** | cyq | 筹码分布、获利盘、成本集中度 |
| **持仓** | holding, industry, change | 持仓明细、行业配置、变动 |
| **资金** | flow, marketflow | 个股/大盘资金流向 |
| **热点** | zt, hot, lhb | 涨停板、人气榜、龙虎榜 |
| **基本面** | scale, dividend, rating, finance, constituent | 规模、分红、评级、财务、成分股 |
| **资讯** | news, report | 新闻快讯、研报 |
| **BaoStock** | forecast, stockindustry, stockdividend | 业绩预告、行业分类、股票分红 |

## 命令详解

### 1. quote - 实时行情

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py quote <代码或名称>
```

示例：
```bash
uv run python main.py quote 510050
uv run python main.py quote 上证50
uv run python main.py quote "上证50,沪深300,创业板"
```

### 2. search - 搜索 ETF

```bash
uv run python main.py search <关键词> [--limit N]
```

示例：
```bash
uv run python main.py search 医药 --limit 10
uv run python main.py search 黄金
```

### 3. hist - 历史行情

```bash
uv run python main.py hist <代码> [--days N] [--start YYYYMMDD] [--end YYYYMMDD] [--period daily|weekly|monthly]
```

示例：
```bash
uv run python main.py hist 510050 --days 30
uv run python main.py hist 510300 --start 20250101 --end 20250127
uv run python main.py hist 159915 --period weekly --days 90
```

### 4. list - ETF 列表

```bash
uv run python main.py list [--limit N] [--sort 字段]
```

示例：
```bash
uv run python main.py list --limit 20
uv run python main.py list --sort 涨跌幅 --limit 10
```

### 5. premium - 溢价率

```bash
uv run python main.py premium [代码] [--limit N]
```

溢价率 = (市价 - 净值) / 净值 × 100%

示例：
```bash
uv run python main.py premium 上证50
uv run python main.py premium --limit 10  # 高溢价排行
```

### 6. indicator - 技术指标

```bash
uv run python main.py indicator <代码> [--days N] [--indicators 类型] [--show-history]
```

支持指标：MA (5/10/20/60)、MACD、RSI (6/12/14)、KDJ、BOLL

示例：
```bash
uv run python main.py indicator 上证50
uv run python main.py indicator 510050 --indicators macd,rsi
uv run python main.py indicator 510300 --show-history --limit 10
```

### 7. sentiment - 市场情绪

```bash
uv run python main.py sentiment
```

提供：涨跌统计、北向资金、融资融券、情绪评分 (0-100)

情绪等级：
- 80-100: 极度贪婪 🔴
- 60-80: 贪婪 🟠
- 40-60: 中性 🟡
- 20-40: 恐惧 🟢
- 0-20: 极度恐惧 🔵

### 8. constituent - 指数成分股 (BaoStock)

```bash
uv run python main.py constituent <指数> [--limit N]
```

支持：hs300/沪深300, sz50/上证50, zz500/中证500

示例：
```bash
uv run python main.py constituent hs300
uv run python main.py constituent sz50 --limit 20
```

### 9. finance - 财务分析 (BaoStock)

```bash
uv run python main.py finance <股票代码> [--year 年份] [--quarter 季度] [--type 类型]
```

类型：summary (综合)、profit (盈利)、growth (成长)、dupont (杜邦)、balance (偿债)、cashflow (现金流)、operation (营运)

示例：
```bash
uv run python main.py finance 600519
uv run python main.py finance 600519 --year 2024 --quarter 3 --type profit
```

### 10. holding - ETF 持仓

```bash
uv run python main.py holding <代码> [--year 年份]
```

示例：
```bash
uv run python main.py holding 510050
uv run python main.py holding 510300 --year 2024
```

### 11. industry - 行业配置

```bash
uv run python main.py industry <代码> [--year 年份]
```

### 12. change - 持仓变动

```bash
uv run python main.py change <代码> [--year 年份]
```

### 13. flow - 资金流向

```bash
uv run python main.py flow <代码> [--days N]
```

示例：
```bash
uv run python main.py flow 510050 --days 5
```

### 14. scale - ETF 规模

```bash
uv run python main.py scale [--exchange sse|szse|all] [--limit N]
```

### 15. dividend - ETF 分红

```bash
uv run python main.py dividend [--limit N]
```

### 16. rating - 基金评级

```bash
uv run python main.py rating [代码] [--limit N]
```

### 17. news - 新闻快讯 ⭐ NEW

```bash
uv run python main.py news [代码] [--market] [--limit N]
```

示例：
```bash
uv run python main.py news 518880        # 特定 ETF 新闻
uv run python main.py news --market      # 财联社市场快讯
uv run python main.py news               # 默认市场快讯
```

### 18. zt - 涨停板池 ⭐ NEW

```bash
uv run python main.py zt [--date YYYYMMDD] [--limit N]
```

显示：代码、名称、涨幅、封板资金、连板数、所属行业

示例：
```bash
uv run python main.py zt --limit 20
uv run python main.py zt --date 20260127
```

### 19. hot - 人气排行 ⭐ NEW

```bash
uv run python main.py hot [--limit N]
```

东方财富人气榜排名

### 20. lhb - 龙虎榜 ⭐ NEW

```bash
uv run python main.py lhb [--days N] [--limit N]
```

显示：代码、名称、上榜日、净买额、上榜原因

示例：
```bash
uv run python main.py lhb --days 5 --limit 20
```

### 21. marketflow - 大盘资金流 ⭐ NEW

```bash
uv run python main.py marketflow [--days N]
```

显示：主力/超大单/大单/中单/小单净流入

示例：
```bash
uv run python main.py marketflow --days 10
```

### 22. valuation - 市场估值 ⭐ NEW

```bash
uv run python main.py valuation [--market 上证|深证|创业板|科创板] [--days N]
```

显示：PE、PB 历史数据

示例：
```bash
uv run python main.py valuation --market 上证 --days 30
uv run python main.py valuation --market 创业板
```

### 23. comment - 综合评分 ⭐ NEW

```bash
uv run python main.py comment [--limit N]
```

显示：机构参与度、综合得分、关注指数

### 24. report - 研报 ⭐ NEW

```bash
uv run python main.py report <代码> [--limit N]
```

示例：
```bash
uv run python main.py report 600519 --limit 10
```

### 25. forecast - 业绩预告 (BaoStock) ⭐ NEW

```bash
uv run python main.py forecast <代码> [--days N]
```

示例：
```bash
uv run python main.py forecast 600519
```

### 26. stockindustry - 行业分类 (BaoStock) ⭐ NEW

```bash
uv run python main.py stockindustry <代码>
```

示例：
```bash
uv run python main.py stockindustry 600519
```

### 27. stockdividend - 股票分红 (BaoStock) ⭐ NEW

```bash
uv run python main.py stockdividend <代码> [--year 年份]
```

示例：
```bash
uv run python main.py stockdividend 600519 --year 2024
```

### 28. cyq - 筹码分布 ⭐ NEW

```bash
uv run python main.py cyq <代码> [--adjust 复权类型] [--limit N] [--plot] [--top N]
```

**双模式支持**：
- **股票模式**：输入股票代码，显示详细筹码分布数据和图表
- **ETF 模式**：输入 ETF 代码，自动展示前 N 大重仓股筹码汇总

参数：
- `--adjust`: 复权类型，空-不复权，qfq-前复权，hfq-后复权 (股票模式)
- `--limit`: 返回最近 N 天数据，默认 30 (股票模式)
- `--plot`: 显示 ASCII 图表 (股票模式)
- `--top`: ETF 模式显示前 N 大重仓股，默认 5

解读说明：
- **获利比例**: 当前价格下盈利的筹码占比，>90% 追高风险，<10% 可能接近底部
- **90集中度**: 90% 筹码的价格集中程度，越小说明主力控盘越强
- **70集中度**: 70% 筹码的价格集中程度

示例：
```bash
# 股票模式
uv run python main.py cyq 000001                # 平安银行筹码分布
uv run python main.py cyq 600519 --limit 60     # 茅台最近60天
uv run python main.py cyq 600519 --plot         # 显示 ASCII 图表

# ETF 模式 (自动检测)
uv run python main.py cyq 510050                # 上证50ETF 前5大重仓股筹码
uv run python main.py cyq 沪深300 --top 10      # 沪深300ETF 前10大重仓股
uv run python main.py cyq 159915 --top 3        # 创业板ETF 前3大重仓股
```

## 常用 ETF 别名

| 类别 | 别名 → 代码 |
|------|-------------|
| **宽基** | 上证50→510050, 沪深300→510300, 中证500→510500, 中证1000→512100, 创业板→159915, 科创50→588000 |
| **行业** | 证券etf→512880, 银行etf→512800, 医药etf→512010, 消费etf→159928, 新能源车→515030, 芯片etf→159995, 军工etf→512660 |
| **跨境** | 纳指etf→513100, 标普500→513500, 恒生科技→513180, 恒生etf→159920, 日经etf→513880 |

## 工作流程

### 步骤 1: 解析用户需求

| 用户描述 | 命令 |
|----------|------|
| "XX 今天怎么样" | `quote` |
| "最近走势" | `hist` |
| "有哪些 XX ETF" | `search` |
| "成交最活跃的" | `list` |
| "溢价率/折价" | `premium` |
| "技术指标/MA/MACD/RSI" | `indicator` |
| "市场情绪/北向资金" | `sentiment` |
| "成分股" | `constituent` |
| "财报/ROE/毛利率" | `finance` |
| "持仓/重仓股" | `holding` |
| "行业配置" | `industry` |
| "持仓变动" | `change` |
| "资金流向/主力资金" | `flow` |
| "大盘资金" | `marketflow` |
| "规模/份额" | `scale` |
| "分红" | `dividend` |
| "评级" | `rating` |
| "新闻/快讯" | `news` |
| "涨停/涨停板" | `zt` |
| "人气榜/热门股" | `hot` |
| "龙虎榜/游资" | `lhb` |
| "市场估值/PE/PB" | `valuation` |
| "综合评分" | `comment` |
| "研报" | `report` |
| "业绩预告" | `forecast` |
| "行业分类" | `stockindustry` |
| "股票分红历史" | `stockdividend` |
| "筹码分布/获利盘/套牢盘" | `cyq` |

### 步骤 2: 执行查询

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py <command> [args]
```

### 步骤 3: 解读结果

向用户解释数据含义，提供分析见解。

## 示例

<example>
user: 今天有哪些涨停的股票
assistant: 我来查询今日涨停板。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py zt --limit 20
```

结果：今日共有 XX 只股票涨停，其中黄金、有色板块涨停家数较多...
</example>

<example>
user: 最近龙虎榜有哪些股票
assistant: 我来查询最近龙虎榜详情。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py lhb --days 5 --limit 20
```

结果：[展示龙虎榜数据，分析机构和游资动向]
</example>

<example>
user: 市场估值现在怎么样
assistant: 我来查询当前市场估值水平。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py valuation --market 上证 --days 30
```

结果：上证当前 PE 16.94，PB 1.48，处于历史中位水平...
</example>

<example>
user: 黄金ETF最近有什么新闻
assistant: 我来查询黄金ETF相关新闻。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py news 518880 --limit 10
```

结果：[展示相关新闻并总结要点]
</example>

<example>
user: 分析一下茅台的财务和研报
assistant: 我来查询茅台的财务指标和研报。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py finance 600519
uv run python main.py report 600519 --limit 5
```

结果：茅台 ROE 26.83%，毛利率 91.53%，最新研报多数给予买入评级...
</example>

<example>
user: 看看平安银行的筹码分布
assistant: 我来查询平安银行的筹码分布情况。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py cyq 000001 --limit 30
```

结果：平安银行当前获利比例 45.2%，90集中度 12.5%，筹码较为集中，显示主力有一定控盘...
</example>

<example>
user: 上证50ETF 的重仓股筹码情况怎么样
assistant: 我来查询上证50ETF前5大重仓股的筹码分布。

```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/etf-tool
uv run python main.py cyq 510050 --top 5
```

结果：
- 贵州茅台 (9.06%): 获利盘 0.49%，🟢 低位
- 中国平安 (7.67%): 获利盘 0.83%，🟢 低位
- 紫金矿业 (5.97%): 获利盘 0.98%，🟢 低位
整体重仓股获利盘都很低，套牢盘较重...
</example>

## 技术指标解读

| 指标 | 买入信号 | 卖出信号 |
|------|----------|----------|
| **MA** | 金叉，多头排列 | 死叉，空头排列 |
| **MACD** | DIF 上穿 DEA | DIF 下穿 DEA |
| **RSI** | < 20 (超卖) | > 80 (超买) |
| **KDJ** | K 上穿 D，J < 0 | K 下穿 D，J > 100 |
| **BOLL** | 触及下轨反弹 | 触及上轨回落 |

## 免责声明

本工具提供的数据仅供参考，不构成任何投资建议。
数据来源：AkShare (新浪财经/东方财富)、BaoStock (开源财经数据)。
投资有风险，决策需谨慎。

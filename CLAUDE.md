# Finance Skill Marketplace 开发规范

## 项目概述

这是一个金融领域的 Claude Code Skills 市场，用于管理和分发金融相关的自动化工具。

## 目录结构

```
finance-skill-marketplace/
├── .claude/                    # Claude Code 配置
├── .claude-plugin/             # 插件市场配置
│   └── marketplace.json        # 核心：插件注册清单
├── plugins/                    # 所有插件
└── scripts/                    # 项目级脚本
```

## 开发规范

### 插件开发

#### 必需文件

每个插件必须包含：
- `plugins/<plugin-name>/.claude-plugin/plugin.json` - 插件元数据

#### 可选组件

- `skills/` - 自动触发的能力
- `commands/` - 用户显式调用的命令
- `agents/` - 子任务执行器
- `scripts/` - Python 辅助工具
- `tools/` - 编译工具 (Go/Rust 等)

### 命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| 插件目录 | kebab-case | `stock-analysis` |
| Skill 文件 | `SKILL.md` | `skills/price-alert/SKILL.md` |
| Command 文件 | `<name>.md` | `commands/portfolio.md` |
| Agent 文件 | `<name>.md` | `agents/data-fetcher.md` |

### Frontmatter 规范

#### plugin.json

```json
{
  "name": "plugin-name",
  "description": "功能描述",
  "version": "1.0.0",
  "author": {
    "name": "Author Name"
  }
}
```

**注意**：`author` 必须是对象格式，不能是字符串。

#### SKILL.md

```yaml
---
name: skill-name
version: 1.0.0
author: Author Name
description: |
  Skill 描述。
  触发词：关键词1、关键词2、关键词3
---
```

#### Command/Agent

```yaml
---
name: Component Name
description: 组件描述
category: 分类 (可选)
tags: [tag1, tag2] (可选)
tools: Tool1, Tool2 (Agent 必需)
---
```

### 工具集成

#### Python 工具 (推荐)

使用 `uv` 管理依赖：

```
scripts/<tool-name>/
├── pyproject.toml
├── main.py
├── internal/
└── uv.lock
```

在 Skill 中调用：
```bash
cd ${CLAUDE_PLUGIN_ROOT}/scripts/<tool-name>
uv run python main.py [args]
```

#### Bash 脚本

适用于轻量级自动化：
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/<script-name>.sh
```

### 注册插件

编辑 `.claude-plugin/marketplace.json`：

```json
{
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "插件描述",
      "version": "1.0.0"
    }
  ]
}
```

## 质量要求

### 提交前检查

- [ ] plugin.json 格式正确
- [ ] SKILL.md 包含完整 frontmatter
- [ ] 已注册到 marketplace.json
- [ ] README.md 已更新（如有必要）

### Skill 内容要求

- 清晰的使用场景描述
- 完整的工作流程步骤
- 至少一个使用示例
- 包含触发词便于自动识别

## 常用命令

```bash
# 更新 marketplace
/plugin marketplace update finance-skill-marketplace

# 安装插件
/plugin install <plugin-name>@finance-skill-marketplace

# 卸载插件
/plugin uninstall <plugin-name>@finance-skill-marketplace
```

## 金融领域特定规范

### 数据安全

- 不在 Skill 中硬编码 API 密钥
- 使用环境变量管理敏感信息
- 日志中不输出敏感财务数据

### 免责声明

所有金融相关 Skill 应包含适当的免责声明，说明：
- 不构成投资建议
- 数据仅供参考
- 用户需自行承担风险

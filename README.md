# Finance Skill Marketplace

金融领域 Claude Code Skills 市场，提供金融相关的自动化工具和能力扩展。

## 快速开始

### 1. 添加 Marketplace

```bash
/plugin marketplace add git@github.com:zhengzexiang/finance-skill-marketplace.git
```

### 2. 安装插件

```bash
/plugin install <plugin-name>@finance-skill-marketplace
```

### 3. 使用插件

- **自动触发**：根据对话上下文自动识别并使用相关 skill
- **显式调用**：使用 `/<skill-name>` 手动触发
- **命令调用**：使用 `/<plugin-name>:<command-name>` 调用特定命令

## 项目结构

```
finance-skill-marketplace/
├── .claude/                    # Claude Code 配置
│   └── settings.json
├── .claude-plugin/             # 插件市场配置
│   └── marketplace.json        # 插件注册清单
├── plugins/                    # 插件目录
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json     # 插件元数据
│       ├── skills/             # Skills (自动触发能力)
│       ├── commands/           # Commands (显式命令)
│       └── agents/             # Agents (子任务执行器)
├── scripts/                    # 项目级脚本
├── README.md
├── CLAUDE.md                   # 开发规范
└── .gitignore
```

## 开发新插件

### 1. 创建插件目录

```bash
mkdir -p plugins/your-plugin/.claude-plugin
mkdir -p plugins/your-plugin/skills/your-skill
```

### 2. 创建 plugin.json

```json
{
  "name": "your-plugin",
  "description": "插件描述",
  "version": "1.0.0",
  "author": {
    "name": "Your Name"
  }
}
```

### 3. 创建 SKILL.md

```markdown
---
name: your-skill
version: 1.0.0
author: Your Name
description: |
  Skill 描述。
  触发词：关键词1、关键词2
---

# Skill 标题

## 何时使用

说明使用场景...

## 工作流程

### 步骤 1
...

## 示例

<example>
user: 示例输入
assistant: 示例输出
</example>
```

### 4. 注册到 marketplace

编辑 `.claude-plugin/marketplace.json`，添加插件信息：

```json
{
  "plugins": [
    {
      "name": "your-plugin",
      "source": "./plugins/your-plugin",
      "description": "插件描述",
      "version": "1.0.0"
    }
  ]
}
```

### 5. 提交更新

```bash
git add plugins/your-plugin/ .claude-plugin/marketplace.json
git commit -m "feat: add your-plugin"
git push
```

## 插件规范

### plugin.json 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 插件名称，需与目录名一致 |
| description | string | 插件功能描述 |
| version | string | 版本号 (semver) |
| author | object | 作者信息 `{ "name": "..." }` |

### SKILL.md frontmatter 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | Skill 名称 |
| version | string | 版本号 |
| author | string | 作者名称 |
| description | string | 描述，建议包含触发词 |

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-plugin`)
3. 按照上述规范开发插件
4. 提交 PR

## License

MIT

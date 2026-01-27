---
name: greeting
version: 1.0.0
author: Finance Skill Marketplace
description: |
  示例 Skill，用于展示 Skill 的基本结构。
  触发词：示例、greeting、hello、你好
---

# Greeting Skill

这是一个示例 Skill，用于展示 Finance Skill Marketplace 插件的基本开发规范。

## 何时使用

当用户需要了解如何开发新的 Skill 时，可以参考此示例。

## 工作流程

### 步骤 1：理解需求

分析用户的需求，确定 Skill 的功能边界。

### 步骤 2：设计结构

1. 创建插件目录结构
2. 编写 plugin.json
3. 编写 SKILL.md

### 步骤 3：测试验证

确保 Skill 可以正常触发和执行。

## 示例

<example>
user: 你好，我想了解如何开发一个金融相关的 Skill
assistant: 你好！开发金融相关的 Skill 需要以下步骤：
1. 在 plugins/ 目录下创建插件文件夹
2. 添加 .claude-plugin/plugin.json 元数据
3. 在 skills/ 目录下创建 Skill 文件
4. 将插件注册到 marketplace.json
</example>

## 注意事项

- Skill 文件必须命名为 `SKILL.md`
- frontmatter 中的 author 在 plugin.json 中必须是对象格式
- description 中建议包含触发词，便于自动识别

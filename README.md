# 林月半子 · AI 配图技能库

公众号「林月半子的 AI 笔记」的 Claude Code 配图技能集合。自动为技术长文生成概念图、流程图、对比图、架构图，让长文不再单调。

## Preview Gallery

`linyuebanzi-inline-diagram` 支持 4 种视觉风格：

| | |
|:---:|:---:|
| ![](./previews/notebook.png) | ![](./previews/infographic.png) |
| notebook · 手绘网格笔记本风 | infographic · 专业扁平信息图 |
| ![](./previews/executive-tech.png) | ![](./previews/cozy-handdrawn.png) |
| executive-tech · 现代科技商务风 | cozy-handdrawn · 温暖手绘卡片风 |

## 包含 Skills

### `linyuebanzi-inline-diagram` · 技术长文插图生成

为 3000~8000 字技术长文自动识别插图位置，生成 4-5 张概念图、流程图、对比图、架构图。支持 notebook / infographic / executive-tech / cozy-handdrawn 四种视觉风格。

- **输入**: 技术长文 Markdown
- **输出**: 多张 16:9 插图 PNG + 插入位置清单

### `linyuebanzi-image-gen` · 通用图像生成

MuleRun Nano Banana 2 API 执行层，支持纯文本生图（generation）和带参考图修图（edit）两种模式，单张和批量执行。被其他 skill 调用的基础设施，不直接面向终端用户。

## 安装

```bash
# 安装全部 skills（推荐）
npx skills add lqshow/linyuebanzi-skills

# 全局安装（所有项目可用）
npx skills add lqshow/linyuebanzi-skills -g

# 只安装某一个 skill
npx skills add lqshow/linyuebanzi-skills -s linyuebanzi-inline-diagram

# 先看看有哪些可安装的
npx skills add lqshow/linyuebanzi-skills --list
```

## 使用

安装后在 Claude Code 中直接对话触发：

```bash
# 插图生成（会先让你选风格）
"帮这篇文章加几张插图，用笔记本手绘风"
"这篇太单调了，配几张图"

# 指定风格
"用温暖手绘卡片风配图"
"来张专业信息图风格的"
```

需要设置环境变量 `MULERUN_API_KEY`（MuleRun API 的 Bearer token）。

## 项目结构

```
linyuebanzi-skills/
├── README.md
├── previews/                                # 预览图
├── skills/
│   ├── linyuebanzi-inline-diagram/          # 插图生成 skill
│   │   ├── SKILL.md                         # 入口定义
│   │   ├── scripts/
│   │   │   └── inject_style.py              # 风格注入脚本
│   │   └── references/                      # 提示词模板、风格定义、案例
│   │       ├── styles/                      # 4 种风格定义
│   │       ├── examples.md                  # 完整案例
│   │       └── prompt_template.md           # 骨架模板
│   └── linyuebanzi-image-gen/               # 通用图像生成 skill
│       ├── SKILL.md                         # 入口定义
│       └── scripts/
│           └── generate.py                  # API 调用脚本
```

## 关于作者

林月半子（LQ），AI 自动化实践者。公众号「林月半子的 AI 笔记」专注于 n8n 和 AI Agent 实战教程。

---

Star & Fork 随意，有问题欢迎提 Issue。

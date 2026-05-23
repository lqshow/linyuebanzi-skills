---
name: linyuebanzi-image-gen
description: |
  通用图像生成执行层,支持 MuleRun Nano Banana 2 和 APImart GPT Image 2 两种生图 API。通过 --provider 切换。支持 generation(纯文本生图)和 edit(带参考图修图)两种模式,单张和批量执行。这是被其他 skill 调用的基础设施 skill,不直接面向终端用户。当其他 skill(如 cover-hero、inline-diagram)需要调 API 生图时,调用本 skill 的 scripts/generate.py。不要用于:提示词撰写、风格注入、业务校验——这些由调用方 skill 负责。
---

# 林月半子通用图像生成器

支持两种生图 API 的执行层,通过 `--provider` 参数切换。调用方 skill 负责 prompt 撰写、样式注入、业务校验;本 skill 只管"接收 prompt → 调 API → 返回结果"。

## 什么时候触发这个 skill

本 skill 是被其他 skill 调用的基础设施,不直接由用户触发。当 Claude 正在执行某个生图相关的 skill(如 `linyuebanzi-cover-hero`、`linyuebanzi-inline-diagram`)时,通过 bash 调用本 skill 的脚本。

## 生图 API 切换

通过 `--provider` 参数或环境变量自动检测选择生图平台:

```bash
# 方式 1: 自动检测 —— 只设一个环境变量就行
export APIMART_API_KEY=sk-xxx
python linyuebanzi-image-gen/scripts/generate.py \
  --mode generation --prompt "..." --output-dir ./out
# 自动检测到 APIMART_API_KEY，使用 apimart

# 方式 2: 显式指定 —— 两个都设了时用这个覆盖
python linyuebanzi-image-gen/scripts/generate.py \
  --provider apimart --mode generation --prompt "..." --output-dir ./out
```

| Provider | `--provider` | 环境变量 | 模型 |
|---|---|---|---|
| MuleRun | `mulerun`（默认） | `MULERUN_API_KEY` | Nano Banana 2 |
| APImart | `apimart` | `APIMART_API_KEY` | GPT Image 2 |

**自动检测逻辑**（不传 `--provider` 时）:
1. 只设了 `APIMART_API_KEY` → 自动用 apimart
2. 只设了 `MULERUN_API_KEY` → 用 mulerun
3. 两个都设了 → 默认 mulerun（向后兼容），想用 apimart 需显式传 `--provider apimart`

## 两种模式

### generation — 纯文本生图

从纯文字 prompt 生成图片,不依赖参考图。适合:概念图、流程图、信息图等。

```bash
# 单张
python linyuebanzi-image-gen/scripts/generate.py \
  --mode generation \
  --prompt "A notebook-style diagram showing..." \
  --name-tag diagram-001 \
  --output-dir ./out

# 单张(从文件读 prompt)
python linyuebanzi-image-gen/scripts/generate.py \
  --mode generation \
  --prompt-file ./prompt.txt \
  --name-tag diagram-001 \
  --output-dir ./out
```

### edit — 带参考图修图

在参考图基础上生成新图,适合需要人物一致性的场景。

```bash
# 单张
python linyuebanzi-image-gen/scripts/generate.py \
  --mode edit \
  --prompt "A portrait of..." \
  --images "https://r2.cloudnative101.net/portrait.png" \
  --name-tag cover-hero \
  --output-dir ./out
```

## 批量模式

通过 manifest JSON 批量提交,支持串行和并行。

```bash
# 串行
python linyuebanzi-image-gen/scripts/generate.py \
  --manifest ./batch.json \
  --output-dir ./out

# 并行
python linyuebanzi-image-gen/scripts/generate.py \
  --manifest ./batch.json \
  --output-dir ./out \
  --parallel
```

### Manifest JSON 格式

```json
{
  "mode": "generation",
  "aspect_ratio": "16:9",
  "resolution": "2K",
  "items": [
    {
      "id": "diagram-001",
      "prompt": "完整提示词(调用方已注入风格前缀)"
    },
    {
      "id": "cover-001",
      "prompt": "完整提示词",
      "images": ["https://example.com/ref.png"]
    }
  ]
}
```

- `mode`: `generation` 或 `edit`(默认 `generation`)
- `aspect_ratio` / `resolution`: 全局默认,可省略
- `items[].id`: 必填,用于输出文件命名
- `items[].prompt`: 必填,完整提示词(调用方已完成所有拼接)
- `items[].images`: 可选,edit 模式需要传参考图 URL

## CLI 参数

| 参数 | 单张 | 批量 | 必填 | 说明 |
|---|---|---|---|---|
| `--provider` | Y | Y | 否 | `mulerun`(默认) 或 `apimart` |
| `--mode` | Y | N(在 manifest) | 单张必填 | `generation` 或 `edit` |
| `--prompt` | Y(或 --prompt-file) | N | 否 | 内联提示词 |
| `--prompt-file` | Y(或 --prompt) | N | 否 | 提示词文件路径 |
| `--manifest` | N | Y | 否 | manifest JSON 路径 |
| `--images` | Y(edit 模式) | N(在 items) | edit 模式必填 | 逗号分隔的参考图 URL |
| `--name-tag` | Y | N | 否 | 输出文件名前缀(默认 `image`) |
| `--output-dir` | Y | Y | 否 | 输出目录(默认 `./output`) |
| `--aspect-ratio` | Y | Y(可被 manifest 覆盖) | 否 | 默认 `16:9` |
| `--resolution` | Y | Y(可被 manifest 覆盖) | 否 | 默认 `2K` |
| `--parallel` | N | Y | 否 | 启用并行执行 |
| `--blocklist` | Y | Y | 否 | 禁用词表文件路径(每行一个词,命中即停止) |

## 输出结构

单张:
```
{output-dir}/
├── {name-tag}-{timestamp}.png   # 生成图片
├── {name-tag}-{timestamp}.txt   # 使用的 prompt
└── {name-tag}-{timestamp}.json  # 元数据
```

批量:
```
{output-dir}/
├── {id}.png            # 每项图片
├── {id}.txt            # 每项 prompt
├── {id}.json           # 每项元数据
└── _run_metadata.json  # 整体运行信息
```

## 环境变量

根据 `--provider` 设置对应的 API Key:

- `MULERUN_API_KEY`: `--provider mulerun` 时必填,MuleRun API 的 Bearer token
- `APIMART_API_KEY`: `--provider apimart` 时必填,APImart API 的 Bearer token

## 调用方 skill 集成指南

### 新 skill 如何使用

1. 在你的 SKILL.md 中定义 prompt 生成工作流
2. 生成 prompt 后,通过 bash 调用本 skill:

```bash
# 单张（默认 mulerun）
python /path/to/linyuebanzi-image-gen/scripts/generate.py \
  --mode generation \
  --prompt-file ./my-prompt.txt \
  --name-tag my-image \
  --output-dir ./my-output

# 单张（指定 apimart）
python /path/to/linyuebanzi-image-gen/scripts/generate.py \
  --provider apimart \
  --mode generation \
  --prompt-file ./my-prompt.txt \
  --name-tag my-image \
  --output-dir ./my-output

# 批量:先写 manifest JSON,再调用
python /path/to/linyuebanzi-image-gen/scripts/generate.py \
  --manifest ./my-manifest.json \
  --output-dir ./my-output \
  --parallel
```

3. 脚本退出码:0 成功,1 失败
4. 读取输出目录中的 .txt 文件可获取保存的 prompt,方便重跑

### 调用方负责的事情

- 提示词撰写和拼接(包括风格前缀注入)
- 业务校验(如禁用特定词汇)
- 参考图 URL 管理
- 后处理(如生成 manifest.md 插图位置清单)

## 故障排除

| 问题 | 原因 | 对策 |
|---|---|---|
| API KEY 未找到 | 环境变量未设置 | mulerun: `export MULERUN_API_KEY=sk-xxx`，apimart: `export APIMART_API_KEY=sk-xxx` |
| HTTP 403 | Cloudflare WAF 拦截 | 脚本已内置浏览器 UA,检查网络 |
| 轮询超时 | API 服务繁忙 | 等待后重试,或检查 API 状态 |
| edit 模式未传 --images | 缺少参考图 | edit 模式必须通过 --images 传参考图 URL |

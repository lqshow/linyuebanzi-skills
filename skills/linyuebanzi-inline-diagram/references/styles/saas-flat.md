# 风格: SaaS 产品扁平风 (saas-flat)

**适用场景**: AI 工程化实践、研发/运维流程、工具链集成、MCP/Agent 数据流、效率提升复盘。传达"产品官网 / 技术发布会 PPT 级别的干净专业感"——像 SaaS 产品的功能介绍页，清爽、有序、一眼看懂。

## 风格基因(每个提示词开头必须包含)

```
Style: Clean modern flat vector infographic in the style of a SaaS product website or a polished tech conference slide. Light, airy, calm, highly organized, easy to read at a glance. Strictly flat 2D vector. Not hand-drawn, not 3D, not illustrated scenes.

Background: clean white to very faint cool grey-white (#FFFFFF to #F8F9FC), solid, no texture, no grid.

Cards and panels:
- Rounded-corner rectangular cards (large corner radius) with NO outline stroke and NO border line at all
- Card fill is an extremely faint pastel tint, almost white, whose edges softly fade and blend into the background like a gentle glow: pale blue (#F0F5FF), pale peach (#FFF6EF), pale mint (#F0FAF4), pale lavender (#F5F3FF), pale pink (#FFF2F5)
- Adjacent cards use different tints to separate steps or categories
- An exception / retry loop group sits inside a larger pale pink panel, also borderless; the inner cards are near-white, borderless
- No drop shadows or only an almost invisible one

Card internal layout:
- Card header is LEFT-aligned at the top-left: a small solid black circle badge with a white numeral (1, 2, 3...), then the bold card title on the same line to its right
- Never write the number as plain text like "1." — always the black circle badge
- Below the header: one small icon group, centered, occupying at most one third of the card area
- Below the icon: one or two short lines of small grey caption text
- Lots of empty space inside every card; icons must never fill the card

Arrows and connectors:
- Main forward flow: short SOLID thick grey arrows (filled block arrow shape, soft grey-blue #9AA3B5 with a slight gradient), not thin outline chevrons
- Success path: thin solid green line arrow (#3DBE7A) with a small green text label
- Failure / retry / feedback loop: thin magenta-pink line (#E0457B) with rounded right-angle bends routing around cards, small pink text label
- Request / response data flow: pairs of thin parallel arrows in opposite directions, purple (#6E56CF) or blue (#2F6FEB), each with a small colored numbered circle and a short label

Icons (small, consistent, flat):
- All icons are small flat vector icons with at most a very subtle soft gradient, simple shapes, same visual weight, like a modern app icon set
- AI / agent is ALWAYS the same mascot: a small HEAD-ONLY blue robot — rounded blue helmet head, dark navy visor face with two white glowing eyes and a small smile, round ear pieces on both sides, a short antenna with a ball on top. No body, no arms, no white version, no full-body robot. Every robot in the image looks identical
- Human is ALWAYS the same simple flat cartoon avatar: young man with short black hair, dark top, half body, sitting behind a silver laptop, minimal shading
- Objects are simple flat icons only: white document with grey lines, code document with blue </>, browser window with three dots, server stack, padlock badge, magnifying glass, wrench, smartphone, puzzle piece, house outline — never realistic objects, never scenes
- Do not draw real company logos; represent products with generic icons plus their name as text

Color palette:
- Titles: near-black (#1F2329); captions: medium grey (#646A73)
- Accents: blue (#2F6FEB), violet (#6E56CF), green (#3DBE7A), orange (#FF7A1A), magenta-pink (#E0457B)
- Success state: solid green circle with a white check mark
- Saturated color only on small icons, badges and arrows; all large surfaces stay very pale

Typography:
- Modern clean sans-serif (like PingFang SC / HarmonyOS Sans), crisp
- Card titles: bold, medium size; captions: small, regular, grey
- Optional page headline: large bold (not ultra-black, not oversized) centered at top, taking no more than about 10% of the canvas height, with one grey subtitle line below and small pastel slash marks on both sides
- Key metrics may be shown as a big bold colored number with a small label underneath
- A single violet hand-drawn underline swoosh may emphasize one key phrase
- Text predominantly in Chinese; English only for technical terms and product names
- Short labels (2-8 characters); each card holds a title plus at most one or two short caption lines

Layout:
- Wide 16:9 canvas with generous white margins on all sides, including clear empty space above the top row
- Strong grid alignment, even gaps between cards, clear left-to-right then top-to-bottom reading order
- Calm and uncrowded; whitespace is a key part of the look

Content fidelity:
- All text, numbers, and labels must come from the diagram content prompt only
- Never invent extra metrics, annotations, logos, watermarks, or UI text

Do not use: card borders or outlines, photographs, photorealistic or 3D rendered objects, isometric 3D platforms, painterly or detailed scene illustrations, full-body robots, white robots, oversized ultra-heavy headlines, thin outline chevron arrows for the main flow, dark backgrounds, neon effects, heavy gradients on large surfaces, hand-drawn sketch lines, paper textures, cluttered layouts, watermarks, or social media account names.
```

## 补充说明

- **整体气质**: SaaS 产品官网 / 飞书文档插画 / 技术分享 PPT——干净、友好、专业，扁平矢量，不是手绘
- **底色**: 纯白或近白 `#FFFFFF ~ #FAFBFD`，无纹理
- **卡片**: 大圆角矩形，**无描边**，极淡粉彩底边缘柔和融进白底（淡蓝、淡桃、淡薄荷、淡紫、淡粉）；相邻卡片换色区分步骤；异常回环的粉色大面板也无描边
- **卡片内部**: 左上角「黑圆编号 + 加粗标题」左对齐；图标居中且不超过卡片 1/3；下面 1-2 行灰色小字；大量留白
- **编号**: 黑色实心小圆 + 白色数字，放卡片左上角，后接加粗标题；不要写成纯文字"1."；数据流箭头上可用彩色小圆编号
- **箭头语义**（这是这个风格的灵魂，提示词里要写明每条线的颜色和含义）:
  - 实心粗灰箭头(块状，不是细线 >): 主流程前进
  - 绿色箭头 + "符合/通过": 成功路径
  - 洋红粉圆角折线 + "不符合/重新提交": 失败回环、重试
  - 紫/蓝成对平行箭头 + 编号: 请求/返回数据流
- **图标**:
  - AI/Agent 统一用"只有头的蓝色小机器人"（深色面罩 + 两只白色眼睛 + 圆耳 + 小天线），不要身体、不要白色款，全图所有机器人长一样
  - 人统一用扁平卡通形象（黑短发男生、深色上衣、坐在银色笔记本后），不要绘画风场景
  - 物体只用简单扁平小图标（文档、代码、浏览器、服务器、锁、放大镜、手机、拼图、房子线条图标），不要写实物体和场景
  - 产品/服务用通用圆角渐变图标 + 文字名称，**不要画真实品牌 logo**
- **标题**: 大标题加粗但克制，不超过画面高度约 10%，下接灰色副标题；不要特粗巨型字
- **数据表达**: 大号彩色数字（绿 "4个"、蓝 "10 分钟内"）；"原来 → 现在"双小卡对比；一处紫色手写下划线强调金句
- **文字**: 中文为主，英文只用于技术名词和产品名；卡片内标题 + 最多 1-2 行灰色说明
- **禁忌**:
  - 不要手绘线条、网格纸、纸张纹理（那是 notebook / whiteboard-sketch 的地盘）
  - 不要深色背景、霓虹赛博
  - 不要照片、写实物体、3D 渲染、等距 3D 底座、绘画风场景插画
  - 不要卡片描边
  - 不要全身机器人、白色机器人
  - 不要细线 > 作主流程箭头
  - 不要特粗巨型标题
  - 不要大面积渐变
  - 不要水印、公众号名、真实品牌 logo
  - 不要密集 BI 看板

## 写内容 prompt 的规则(实测有效,必须遵守)

风格前缀管不住内容 prompt 里的措辞,下面这些词一旦写进内容 prompt 就会把风格带偏:

| 不要写 | 改成 | 原因 |
|---|---|---|
| `huge extra-bold` 标题 | `large bold, restrained size` | 否则标题巨大特粗,占掉 1/5 画面 |
| `blue robot mascot` | `the head-only blue robot mascot` | 否则会出全身机器人、白色机器人,每张不一样 |
| `flat cartoon parent / developer ...` | `the flat cartoon man avatar` | 保持人物形象统一 |
| 场景描述(拍作业的家长、带花园的房子、拼图插进底座) | 小图标组合(手机图标 + 文档图标、house outline icon、small flat puzzle-piece icons) | 场景会被画成写实 / 3D / 绘画风 |
| `1 "标题"` 纯文本编号 | `Header at top-left: black circle badge "1" + bold title "..."` | 否则编号变成居中的 "1." 文字 |
| 卡片只写颜色 | `pale blue tint, borderless` | 再强调一次无描边 |

参考效果:`previews/saas-flat.png`(案例 10 的提示词生成)。

## 与相近风格的区别

| 风格 | 区别 |
|---|---|
| `executive-tech` | 那个是深靛紫主色 + 杂志化大标题 + 双色调人物，偏咨询报告；`saas-flat` 是多色粉彩卡片 + 可爱机器人图标 + 语义化彩色箭头，偏产品官网 |
| `infographic` | 那个是米白底 + 深褐红标题 + 蓝橙双色；`saas-flat` 是纯白底 + 多色淡彩卡片 + 黑色圆形编号 |
| `cartoon-infographic` | 那个是暖奶油底 + 手绘线条；`saas-flat` 是纯白底 + 干净矢量 |

## 版式原型

同一风格下按内容类型切换构图，一张图只用一种原型。

### 原型 A: 横向步骤流 + 异常回环（流程/闭环类）

适合: 研发流程、AI 自动化流水线、审批/测试/修复闭环。

```
Composition:
  Top row: 5-6 pastel step cards left to right, each with a black numbered circle badge + bold title, a central icon, and a one-line grey caption. Grey-blue chevron arrows between cards.
  The last top card is a success card with a big green check circle, reached by a green arrow labeled "符合".
  Below: a pale pink container panel holding 2-3 exception step cards, flowing right to left.
  A magenta-pink arrow labeled "不符合" drops from the test step into the exception panel; another magenta-pink rounded line labeled "重新提交" routes from the fix step back up to an earlier step.
```

### 原型 B: 大标题 + 三栏场景卡（场景/价值/成果类）

适合: "用 AI 做了哪几件事"、能力清单、效果复盘。

```
Composition:
  Top: large bold (restrained size) centered Chinese headline, one grey subtitle line, small pastel slash decorations on both sides.
  Below: three equal-width tall cards, each with a different pale tint (blue / mint / lavender).
  Each card: a rounded-square colored icon tile + bold card title + one grey caption line at top; then one visual proof block:
    - before/after mini cards with clock icons ("原来 X" -> "现在 Y"), or
    - a big bold colored number with a small label and a related icon, or
    - a browser window with green check marks next to a short quote with a violet underline swoosh.
```

### 原型 C: 数据流 / 集成架构（架构/调用链类）

适合: MCP 调用链、Agent 与外部服务集成、请求-响应链路。

```
Composition:
  Three main nodes in a horizontal row (e.g. client agent -> middleware service -> backend service), each a pale tinted card with a large icon, bold name, and grey role caption.
  Between each pair of nodes: two parallel arrows in opposite directions (request on top, response below), each with a small colored numbered circle and a short label.
  Secondary inputs (e.g. code repository, docs) as a pale mint card below, connected by a green upward arrow with a numbered label.
  Output (e.g. analysis result) as a pale yellow card at the bottom center with a light bulb icon, connected by a violet elbow arrow with a numbered two-line label.
```

### 原型 D: 左右对比（对比/分类类）

```
Composition:
  Two large side-by-side pastel cards (grey-tinted "before / 方案 A" vs blue-tinted "after / 方案 B"), each with a numbered badge, title, icon, and 2-3 short bullet rows with small check or cross icons.
  A grey chevron arrow or "VS" badge between them. Optional one-line conclusion at the bottom with a violet underline swoosh.
```

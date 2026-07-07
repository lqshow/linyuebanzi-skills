# 学科知识信息图 · 提示词骨架

以下是生图提示词的标准模板。使用时将 `{变量}` 替换为实际内容。

```
Create a vertical educational infographic poster (9:16 ratio) about "{topic}".

HEADER SECTION:
- Large bold Chinese title: "{topic}" in {theme_color}, prominent and eye-catching
- Subtitle tag: "— {grade}{subject} {chapter} —" in a colored pill-shaped badge below the title
- Decorative elements matching the topic theme (e.g., sound waves for acoustics, light rays for optics, molecule shapes for chemistry)

MAIN CONTENT:
{num_sections} numbered sections arranged vertically, each in a rounded card/panel with light fill:

{sections_content}

BOTTOM SECTION (pick the most appropriate one):
- Option A: Summary strip with 3-4 key terms in small rounded badges with mini icons
- Option B: "学习提示" box with a lightbulb icon and 1-2 sentence takeaway
- Option C: "生活中的例子" strip with 4-5 real-world application mini icons and labels

VISUAL STYLE:
- Clean educational infographic style — NOT hand-drawn, NOT sketch, NOT notebook grid
- {theme_color} as primary accent color for: section headers, numbered badges, decorative elements, key terms
- White or very light tinted background for card interiors
- Overall poster background: light colored, matching theme but very subtle (not pure white, not dark)
- Numbered section badges: solid {theme_color} circles with white numbers
- Illustrations: simple, clear diagrams with labeled parts — NOT photographs, NOT 3D renders
- Typography: clean sans-serif, Chinese text throughout, large readable headings
- Generous whitespace between sections — do NOT cram content
- Each card visually distinct but stylistically consistent
- Publication-ready quality for WeChat articles, Xiaohongshu, or print
- Do NOT use: dark backgrounds, neon colors, glossy effects, heavy shadows, complex 3D visuals, photographic elements

ACCURACY (critical — this is educational material for students):
- Render ALL Chinese text, formulas, numbers, subscripts and superscripts EXACTLY as written in this prompt — do not paraphrase, translate, drop characters, or invent text
- Formulas must keep exact structure: e.g. "a² + b² = c²", "I = U/R", "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂" — superscripts/subscripts in the correct position
- No garbled, malformed, or half-formed Chinese characters
- Arrow directions, labels and diagram relationships must match the described logic exactly
```

## 单个 Section 的模板

```
Section {n}: "{concept_title}"
- Heading: "{concept_title}" in {theme_color}, bold
- Illustration: {illustration_description}
- Text: {explanation_text} (1-2 sentences, Chinese)
- Highlight: {formula_or_key_relationship} (if applicable, displayed prominently)
```

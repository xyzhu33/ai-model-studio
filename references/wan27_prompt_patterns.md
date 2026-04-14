# Wan2.7 Prompt Patterns

## 基础原则
- 始终保留角色 `seed core`，这是所有景别和变体的统一锚点。
- 白底设定图必须明确写出用途，例如：`white background`、`character reference sheet`、`front view`、`studio lighting`。
- 三视图与表情组优先走 sequential / group generation，保证角色一致性。
- 有参考图时，要明确指出参考图的作用：服装依据、配饰依据、产品依据、场景依据。
- 文字要求优先于图片分析，prompt 中不得让图片推断覆盖用户的明确文字要求。
- prompt 要强调：**同一角色、同一身份、同一核心特征**，避免多图输出时角色漂移。

---

## Prompt 结构总公式

推荐将 Wan2.7 prompt 组织成 6 段：

1. **角色锚点**
2. **当前用途 / 景别**
3. **外形描述**
4. **造型描述**
5. **环境 / 背景要求**
6. **一致性 / 质量要求**

推荐模板：

```text
[seed core],
[shot purpose],
[identity + appearance],
[styling + outfit + makeup + accessories],
[background / setting],
[consistency + quality terms]
```

---

## Seed Core 写法

Seed core 是所有 prompt 的统一角色锚点，建议固定包含：
- 角色年龄感
- 性别表达
- 体型
- 发型发色
- 核心脸部特征
- 1-2 个必须保留的辨识点
- 角色整体气质

示例：

```text
same character, a tall slender young female model, long black wavy hair, defined cheekbones, calm confident gaze, elegant posture, black beauty mark under left eye
```

或：

```text
same character, androgynous futuristic idol, silver-white layered long hair, pale skin, sharp almond eyes, ethereal but intense presence
```

---

## 输出类型

### 1. close_up
用于面部特写。

#### 目标
- 清楚呈现脸部结构、妆容、发际线、表情基调
- 便于后续锁定脸

#### 模板
```text
[seed core], close-up portrait, front view, face centered, white background, character reference sheet, clear facial structure, visible makeup details, studio lighting, same identity, high detail
```

#### 要点
- 强调 `front view`
- 强调 `face centered`
- 不要写太多服装细节
- 应保留发型、妆容、脸部标志点

---

### 2. medium_shot
用于中景（腰部以上 / 半身）。

#### 目标
- 展现身体比例与姿态
- 适合看角色整体气质、站姿、上半身服装结构

#### 模板
```text
[seed core], medium shot, waist up, front view, framing from waist to head, upper body and face clearly visible, white background, character reference sheet, balanced body proportion, natural posture, visible outfit silhouette, studio lighting, same identity, high detail
```

#### 要点
- 必须明确指定 `waist up` 和 `framing from waist to head`，否则模型可能生成全身或特写
- 如果是偶像 / 影视角色，可以加入轻微角色姿态描述
- 如果是商业模特，姿态应更标准、更稳定

---

### 3. full_body
用于全身正面设定图。

#### 目标
- 看清完整轮廓、身材比例、全套服装、鞋履

#### 模板
```text
[seed core], full body, front view, standing pose, white background, character reference sheet, full outfit visible, shoes visible, accurate silhouette, studio lighting, same identity, high detail
```

#### 要点
- `standing pose` 尽量标准
- 强调 `full outfit visible`
- 适合用于第一轮角色确认

---

### 4. three_view
用于三视图（正 / 侧 / 背）。

#### 目标
- 建立稳定角色参考
- 便于后续 continuity 和多图生成

#### 模板（给 sequential 用）
```text
[seed core], character reference sheet, full body, white background, same identity, studio lighting.
First image: front view.
Second image: right side view.
Third image: back view.
Keep the same hairstyle, outfit, body proportion, and character identity across all three images.
```

#### 要点
- 必须明确 `same identity across all three images`
- 明确 front / side / back 的顺序
- 适合 `enable_sequential: true`

---

### 5. reference_composite
用于有参考图时的最终融合图。

#### 目标
- 让角色与用户提供的服装 / 配饰 / 产品 / 场景参考结合
- 用于最终成片感输出

#### 模板
```text
[seed core], [scene or campaign purpose], wearing the outfit from reference image 1, using the accessories from reference image 2, placed in the atmosphere of reference image 3, preserve the character identity, preserve the product or garment structure, cinematic / commercial final image, high detail
```

#### 要点
- 要明确每张参考图的作用
- 如果参考图是产品图，要强调不要改产品结构
- 如果参考图是服装图，要强调保留服装版型和材质特征

---

## 不同场景的 prompt 偏向

### 商业平面 / 虚拟模特
应更强调：
- commercial clarity
- product visibility
- elegant standard pose
- clean presentation
- brand-fit styling

可加关键词：
- commercial campaign
- editorial fashion
- luxury beauty image
- product-friendly composition
- clean premium look

---

## Fast / Pro 模式下的 prompt 策略

### Fast
- 允许自动补全更多细节
- prompt 更强调整体方向和大轮廓
- 适合快速拿结果

### Pro
- prompt 使用完整设定卡
- 写明更多局部特征、材质、结构、continuity 规则
- 适合高一致性长期角色

---

## 推荐关键词库

### 一致性
- consistent character
- same identity
- same person
- preserve character identity
- maintain facial features
- stable appearance

### 白底设定图
- white background
- character reference sheet
- front view
- full body reference
- clean studio background
- design sheet presentation

### 质量
- high detail
- studio lighting
- clean texture rendering
- accurate silhouette
- premium fashion rendering
- cinematic detail

### 商业风格
- commercial campaign
- editorial fashion
- luxury beauty ad
- product-forward styling
- premium visual

---

## 反例 / 避免写法

不要只写：
- `beautiful girl`
- `fashion outfit`
- `cool style`
- `nice face`

这类 prompt 太空，会导致：
- 角色不稳定
- 材质不准
- 服装不准
- 多图不一致

应该改成：
- 年龄感 + 性别表达 + 身材方向
- 发型发色 + 脸部识别点
- 服装结构 + 材质 + 色彩
- 当前输出用途
- 一致性要求

---

## 推荐最小生成包

无论哪种场景，最小可用输出应包含：
1. `close_up_prompt`
2. `medium_shot_prompt`
3. `full_body_prompt`
4. `three_view_prompt`

有参考图时额外：
5. `reference_composite_prompt`

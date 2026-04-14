# AI Model Studio

AI 虚拟模特工作室 Skill —— 接收服装图、场景图与文字描述，自动完成角色分析、设定卡生成与多景别图片输出。

## 功能概览

- 接受文字、服装图、人物参考图、场景图的任意组合输入
- 自动生成角色草案（外形、气质、妆造、造型方向）
- 支持**快速模式**（2-4 个确认问题，快速出图）和**专业模式**（完整维度树，适合品牌 IP）
- 两阶段角色一致性流程：锚点人脸 → 发型变体 → 多景别批量生成
- 输出：角色设定卡（JSON）、Wan2.7 可用 prompts、近景 / 中景 / 全身 / 三视图 / 参考图融合

## 适用场景

电商拍摄、时尚大片、美妆护肤广告、服饰珠宝展示、品牌 KV、长期虚拟 IP 建设

---


## 快速开始

### 第一步：获取 DashScope API Key

1. 前往 [阿里云百炼平台](https://bailian.console.aliyun.com/) 注册账号
2. 在控制台创建 API Key

### 第二步：将 skill 放入正确路径

将整个 `ai-model-studio/` 文件夹放到你的 skill 目录下：

```
.claude/skills/ai-model-studio/
```

### 第三步：上传参考图，开始使用

将参考图放到input image下，然后直接描述你的需求，例如：

> 我需要展示purple1.jpeg这件紫色裙子，帮我生成一个亚裔模特，黑色微卷发，新中式妆造。

进入角色分析 → 草案生成 → 模式选择 → 图片生成的完整流程。

---

## 文件结构

```
ai-model-studio/
├── SKILL.md                          # Skill 主文档
├── README.md                         # 本文件
├── assets/
│   └── character_card_template.json  # 角色设定卡模板
├── references/
│   ├── dimensions_commercial.md      # 商业拍摄完整维度体系
│   ├── mode_routing.md               # 快速/专业模式路由规则
│   ├── interview_flow.md             # 提问流设计
│   └── wan27_prompt_patterns.md      # Wan2.7 prompt 编写规范
├── scripts/
│   ├── wan27_client.py               # Wan2.7 API 封装客户端
│   ├── prompt_generator.py           # Prompt 生成器
│   ├── output_manager.py             # 输出目录统一管理
│   ├── project_namer.py              # 项目文件夹自动命名
│   ├── generate_portrait_images.py   # Phase E1：面部特写候选生成
│   ├── generate_hair_variants.py     # Phase E2.5：发型变体生成
│   ├── generate_hair_variants_real.py
│   ├── generate_final_bundle.py      # Phase E3：全景别批量生成
│   ├── generate_prompts.py           # Prompt 文件生成
│   ├── regenerate_portraits.py       # 重新生成面部候选
│   ├── character_card.py             # 角色设定卡数据结构
│   └── export_character_bundle.py    # 导出完整角色包
├── input image/                      # 放置输入参考图（服装图、场景图等）
└── output/                           # 生成结果输出目录（自动创建子文件夹）
```

---

## 生成流程说明

```
用户输入（文字 + 图片）
    ↓ Phase A：输入理解与深度分析
    ↓ Phase B：自动生成角色草案
    ↓ Phase C：选择快速 / 专业模式
    ↓ Phase D：按模式确认关键维度
    ↓ Phase E1：文生图 → 3 个面部候选
    ↓ Phase E2：用户选择锚点人脸
    ↓ Phase E2.5：图生图 → 3 个发型变体
    ↓ Phase E3：图生图 → 全景别（近景 / 中景 / 全身 / 三视图 / 融合图）
    ↓ Phase F：局部细化（按需）
```

---

## 注意事项

- 图片生成依赖 Wan2.7（万相2.7）模型，需要有效的 DashScope API Key 且账户有余额
- 生成图片会保存到 `output/{project_name}/` 目录，项目文件夹名称根据用户输入自动生成
- 文字要求优先于图片推断：同时提供文字和图片时，文字描述具有最高优先级
- 角色一致性依赖两阶段流程（E1 锚点 → E3 生成），不要跳过用户确认步骤

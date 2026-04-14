#!/usr/bin/env python3
"""
生成prompt变体并保存到output文件夹
"""
import os
import sys
import json
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from prompt_generator import PromptGenerator

try:
    from output_manager import OutputManager
    HAS_OUTPUT_MANAGER = True
except ImportError as e:
    print(f"导入OutputManager失败: {e}")
    print("⚠️  将使用默认输出目录")
    HAS_OUTPUT_MANAGER = False

def main():
    # 获取当前项目目录
    if HAS_OUTPUT_MANAGER:
        try:
            output_dir = OutputManager.get_current_project_dir()
            print(f"✅ 使用当前项目目录：{output_dir}")
        except FileNotFoundError:
            print("⚠️  找不到当前项目目录，使用默认目录")
            output_dir = current_dir.parent / "output" / "default_project"
            output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = current_dir.parent / "output" / "default_project"
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 项目目录：{output_dir}")

    # 加载角色设定卡（优先查找项目目录中的文件）
    card_files_to_try = [
        "character_card.json",
        "temp_character_card.json"
    ]

    card_path = None
    for card_file in card_files_to_try:
        candidate_path = output_dir / card_file
        if candidate_path.exists():
            card_path = candidate_path
            print(f"✅ 找到角色设定卡：{card_file}")
            break

    if not card_path:
        # 如果没有找到，尝试在父目录中查找temp文件
        temp_path = current_dir.parent / "temp_character_card.json"
        if temp_path.exists():
            card_path = temp_path
            print(f"✅ 找到临时角色设定卡：temp_character_card.json")
        else:
            print(f"❌ 错误：找不到角色设定卡文件")
            print(f"在目录 {output_dir} 和父目录中查找")
            sys.exit(1)

    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)

    print("✅ 已加载角色设定卡")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建prompt生成器
    generator = PromptGenerator()

    # 1. 生成个性化面部特写prompt变体
    print("\n1. 生成个性化面部特写prompt变体...")
    portrait_variants = generator.generate_portrait_prompt_variants(card, n=3)

    portrait_prompts_file = output_dir / "portrait_prompt_variants.txt"
    with open(portrait_prompts_file, "w", encoding="utf-8") as f:
        f.write("=== 面部特写prompt变体（Phase E1） ===\n\n")
        for i, prompt in enumerate(portrait_variants, 1):
            f.write(f"--- 变体 {i} ---\n")
            f.write(f"{prompt}\n\n")

    print(f"  已保存到：{portrait_prompts_file}")

    # 2. 生成单个面部特写prompt
    print("\n2. 生成单个面部特写prompt...")
    single_portrait_prompt = generator.generate_portrait_prompt(card)
    single_portrait_file = output_dir / "single_portrait_prompt.txt"
    with open(single_portrait_file, "w", encoding="utf-8") as f:
        f.write("=== 单个面部特写prompt ===\n\n")
        f.write(single_portrait_prompt)

    print(f"  已保存到：{single_portrait_file}")

    # 3. 生成发型变体prompts
    print("\n3. 生成发型变体prompts...")
    hair_variants = generator.generate_hair_variants_prompts(card, n=3)
    hair_prompts_file = output_dir / "hair_variant_prompts.txt"
    with open(hair_prompts_file, "w", encoding="utf-8") as f:
        f.write("=== 发型变体prompts（Phase E2.5） ===\n\n")
        for i, prompt in enumerate(hair_variants, 1):
            f.write(f"--- 发型变体 {i} ---\n")
            f.write(f"{prompt}\n\n")

    print(f"  已保存到：{hair_prompts_file}")

    # 4. 生成完整prompt bundle
    print("\n4. 生成完整prompt bundle...")
    bundle = generator.generate_bundle(card)
    bundle_file = output_dir / "prompt_bundle.json"
    with open(bundle_file, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    print(f"  已保存到：{bundle_file}")

    # 5. 生成角色设定卡副本
    print("\n5. 保存角色设定卡副本...")
    card_copy_file = output_dir / "character_card.json"
    with open(card_copy_file, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

    print(f"  已保存到：{card_copy_file}")

    # 6. 生成说明文件
    print("\n6. 生成说明文件...")
    readme_file = output_dir / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write("# neo_chinese_model_v3 生成文件说明\n\n")
        f.write("## 文件结构\n\n")
        f.write("1. **portrait_prompt_variants.txt** - 面部特写prompt变体（Phase E1）\n")
        f.write("   - 用于生成3个差异化面部特写候选方案\n")
        f.write("   - 每个变体对应不同的脸型、五官风格和光线氛围\n")
        f.write("   - 用户需要从中选择一个作为\"锚点人脸\"\n\n")
        f.write("2. **single_portrait_prompt.txt** - 单个面部特写prompt\n")
        f.write("   - 标准的单个面部特写描述\n\n")
        f.write("3. **hair_variant_prompts.txt** - 发型变体prompts（Phase E2.5）\n")
        f.write("   - 基于锚点人脸的3个发型微调变体\n")
        f.write("   - 即使已指定发型，也提供微调选项\n\n")
        f.write("4. **prompt_bundle.json** - 完整prompt bundle（Phase E3）\n")
        f.write("   - 包含所有景别的prompt：近景、中景、全身、三视图、参考图融合\n")
        f.write("   - 用于基于锚点人脸生成所有其他景别\n\n")
        f.write("5. **character_card.json** - 完整角色设定卡\n")
        f.write("   - 包含所有分析、草案、最终配置信息\n\n")
        f.write("## 后续步骤\n\n")
        f.write("1. 使用 **portrait_prompt_variants.txt** 中的prompt生成3个面部特写候选\n")
        f.write("2. 用户选择其中一个作为\"锚点人脸\"\n")
        f.write("3. 使用 **hair_variant_prompts.txt** 生成3个发型变体\n")
        f.write("4. 用户选择最终发型\n")
        f.write("5. 使用 **prompt_bundle.json** 生成所有其他景别（基于锚点人脸+发型的图生图）\n")

    print(f"  已保存到：{readme_file}")

    print(f"\n✅ 所有prompt文件已生成到：{output_dir}")
    print("请按照README.md中的说明进行后续图像生成步骤。")

if __name__ == "__main__":
    main()
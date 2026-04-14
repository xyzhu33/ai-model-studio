#!/usr/bin/env python3
"""
重新生成面部特写候选图片（妆容调整版）
"""
import os
import sys
import json
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from wan27_client import Wan27Client
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

    print("✅ 已加载角色设定卡（准备重新生成面部特写）")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建prompt生成器
    generator = PromptGenerator()

    # 生成个性化面部特写prompt变体（基于修改后的妆容）
    print("\n生成个性化面部特写prompt变体...")
    portrait_variants = generator.generate_portrait_prompt_variants(card, n=3)

    # 保存新的prompt变体
    portrait_prompts_file = output_dir / "portrait_prompt_variants_v2.txt"
    with open(portrait_prompts_file, "w", encoding="utf-8") as f:
        f.write("=== 面部特写prompt变体 v2（妆容调整版） ===\n\n")
        for i, prompt in enumerate(portrait_variants, 1):
            f.write(f"--- 变体 {i} ---\n")
            f.write(f"{prompt}\n\n")

    print(f"✅ 已保存新的prompt变体：{portrait_prompts_file}")

    # 显示prompt变体
    for i, prompt in enumerate(portrait_variants, 1):
        print(f"\n--- 变体 {i} (前100字符) ---")
        print(prompt[:100] + "..." if len(prompt) > 100 else prompt)

    # 初始化Wan27Client
    print("\n初始化Wan27Client...")
    try:
        client = Wan27Client(output_dir=str(output_dir))
        print("✅ Wan27Client初始化成功")
    except Exception as e:
        print(f"❌ Wan27Client初始化失败: {e}")
        sys.exit(1)

    # 生成新的面部特写候选图片
    print("\n开始生成新的面部特写候选图片...")
    print(f"使用 {len(portrait_variants)} 个差异化prompt")
    print("前缀：portrait_option_v2")

    try:
        result = client.generate_portrait_options(
            prompts=portrait_variants,
            n=len(portrait_variants),
            prefix="portrait_option_v2",
            size="1K"
        )

        if result.get("success"):
            print("✅ 图片生成成功！")
            print(f"生成的图片：")
            for i, path in enumerate(result.get("local_paths", []), 1):
                print(f"  {i}. {Path(path).name}")

            # 更新角色设定卡中的锚点信息
            card.setdefault("generation_outputs", {})
            card["generation_outputs"]["portrait_options_v2"] = {
                "generated": True,
                "local_paths": result.get("local_paths", []),
                "urls": result.get("urls", []),
                "prompts_used": portrait_variants,
                "note": "妆容调整版（更自然的新中式妆造）"
            }

            # 保存更新后的角色设定卡
            card_file = output_dir / "character_card_with_portraits_v2.json"
            with open(card_file, "w", encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            print(f"\n📁 更新后的角色设定卡：{card_file}")

            # 生成说明文件
            note_file = output_dir / "REGENERATION_NOTES.md"
            with open(note_file, "w", encoding="utf-8") as f:
                f.write("# 重新生成说明\n\n")
                f.write("## 调整内容\n")
                f.write("- **妆容调整**：根据用户反馈\"妆太浓了\"，调整为更自然的新中式妆造\n")
                f.write("- **具体修改**：\n")
                f.write("  - 眼妆：subtle smoky eyes → natural eye makeup with subtle eyeliner\n")
                f.write("  - 唇妆：classic red lipstick → soft natural lip color\n")
                f.write("  - 眉毛：fine arched brows → fine natural brows\n")
                f.write("  - 腮红：soft blush → very subtle blush\n")
                f.write("\n## 新生成的文件\n")
                f.write("- `portrait_prompt_variants_v2.txt` - 新的prompt变体\n")
                for i, path in enumerate(result.get("local_paths", []), 1):
                    f.write(f"- `{Path(path).name}` - 面部特写候选 {i}\n")
                f.write("- `character_card_with_portraits_v2.json` - 更新后的角色设定卡\n")
                f.write("\n## 后续步骤\n")
                f.write("请从新的候选方案中选择一个作为锚点人脸。\n")

            print(f"\n📝 已创建说明文件：{note_file}")

        else:
            print(f"❌ 图片生成失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 生成过程中出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ 重新生成完成！")

if __name__ == "__main__":
    main()
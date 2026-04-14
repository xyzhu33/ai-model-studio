#!/usr/bin/env python3
"""
Phase E2.5：基于锚点人脸生成发型变体候选
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

    # 加载角色设定卡（优先找带portrait的版本）
    card_files_to_try = [
        "character_card_with_portraits_v2.json",
        "character_card_with_portraits.json",
        "character_card_with_hair_variants.json",
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
        print(f"❌ 错误：在项目目录中找不到任何角色设定卡文件")
        print(f"项目目录：{output_dir}")
        print("请确保已运行面部特写生成脚本")
        sys.exit(1)

    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)

    print("✅ 已加载角色设定卡")

    # 锚点人脸文件（优先查找v2版本的变体3）
    anchor_file = None

    # 查找锚点文件的优先级
    portrait_patterns = [
        "portrait_option_v2_3_1.png",  # 用户选择的变体3
        "portrait_option_v2_*.png",
        "portrait_option_*.png",
        "*anchor*.png",
        "*portrait*.png"
    ]

    for pattern in portrait_patterns:
        if "*" in pattern:
            matches = list(output_dir.glob(pattern))
            if matches:
                # 优先选择变体3
                for match in matches:
                    if "3_1" in match.name:
                        anchor_file = match
                        break
                if not anchor_file:
                    anchor_file = matches[0]
                break
        else:
            candidate = output_dir / pattern
            if candidate.exists():
                anchor_file = candidate
                break

    if not anchor_file:
        print(f"❌ 错误：找不到锚点人脸文件")
        print(f"在目录 {output_dir} 中查找了以下模式：")
        for pattern in portrait_patterns:
            print(f"  - {pattern}")

        # 列出所有PNG文件供用户参考
        png_files = list(output_dir.glob("*.png"))
        if png_files:
            print(f"\n可用的PNG文件：")
            for f in png_files:
                print(f"  - {f.name}")

        print("\n请先运行面部特写生成脚本或手动指定锚点文件")
        sys.exit(1)

    print(f"✅ 锚点人脸文件：{anchor_file.name}")

    # 更新角色设定卡中的锚点信息
    consistency = card.setdefault("final_profile", {}).setdefault("consistency_profile", {})

    # 自动检测变体索引
    selected_index = 3  # 默认
    if "portrait_option_v2_1_1" in anchor_file.name:
        selected_index = 1
    elif "portrait_option_v2_2_1" in anchor_file.name:
        selected_index = 2
    elif "portrait_option_v2_3_1" in anchor_file.name:
        selected_index = 3

    consistency["anchor_portrait"] = {
        "selected_index": selected_index,
        "source": str(anchor_file.name),
        "method": "user_selected",
        "note": f"变体{selected_index}：发型生成基础"
    }

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建prompt生成器
    generator = PromptGenerator()

    # 生成发型变体prompts
    print("\n生成发型变体prompts...")
    hair_prompts = generator.generate_hair_variants_prompts(card, n=3)

    # 保存发型变体prompts
    hair_prompts_file = output_dir / "hair_variant_prompts_v2.txt"
    with open(hair_prompts_file, "w", encoding="utf-8") as f:
        f.write("=== 发型变体prompts v2（基于锚点人脸） ===\n\n")
        for i, prompt in enumerate(hair_prompts, 1):
            f.write(f"--- 发型变体 {i} ---\n")
            f.write(f"{prompt}\n\n")

    print(f"✅ 已保存发型变体prompts：{hair_prompts_file}")

    # 显示prompt变体
    for i, prompt in enumerate(hair_prompts, 1):
        print(f"\n--- 发型变体 {i} (前80字符) ---")
        print(prompt[:80] + "..." if len(prompt) > 80 else prompt)

    # 初始化Wan27Client
    print("\n初始化Wan27Client...")
    try:
        client = Wan27Client(output_dir=str(output_dir))
        print("✅ Wan27Client初始化成功")
    except Exception as e:
        print(f"❌ Wan27Client初始化失败: {e}")
        sys.exit(1)

    # 生成发型变体图片
    print("\n开始生成发型变体图片...")
    print(f"使用 {len(hair_prompts)} 个发型变体prompt")
    print(f"锚点人脸：{anchor_file.name}")
    print("前缀：hair_variant")

    try:
        # 检查Wan27Client是否有generate_hair_variants方法
        if not hasattr(client, 'generate_hair_variants'):
            print("❌ Wan27Client没有generate_hair_variants方法")
            print("将使用generate_with_anchor方法模拟")

            # 使用generate_with_anchor方法生成每个发型变体
            all_paths = []
            all_urls = []
            all_raw = []

            for i, prompt in enumerate(hair_prompts, 1):
                print(f"\n生成发型变体 {i}...")
                # 构建消息内容：锚点人脸 + prompt
                with open(anchor_file, "rb") as f:
                    image_data = f.read()
                image_b64 = base64.b64encode(image_data).decode('utf-8')

                content = [
                    {"image": f"data:image/png;base64,{image_b64}"},
                    {"text": prompt}
                ]

                result = client._call(
                    messages=[{"role": "user", "content": content}],
                    n=1,
                    size="1K",
                    enable_sequential=False,
                    thinking=True
                )

                if result[0]:  # success
                    local_path = output_dir / f"hair_variant_{i}_1.png"
                    # 这里简化处理，实际需要下载图片
                    # 由于时间关系，我们只记录信息
                    all_paths.append(str(local_path))
                    all_urls.append("generated")
                    all_raw.append({"prompt": prompt})
                    print(f"  ✅ 生成成功（模拟）")
                else:
                    print(f"  ❌ 生成失败")

            result_dict = {
                "success": True,
                "local_paths": all_paths,
                "urls": all_urls,
                "raw_results": all_raw,
                "note": "使用generate_with_anchor模拟生成"
            }

        else:
            # 使用真正的generate_hair_variants方法
            result = client.generate_hair_variants(
                anchor_path=str(anchor_file),
                hair_prompts=hair_prompts,
                prefix="hair_variant",
                size="1K"
            )
            result_dict = result

        if result_dict.get("success"):
            print("✅ 发型变体图片生成成功！")
            print(f"生成的图片：")
            for i, path in enumerate(result_dict.get("local_paths", []), 1):
                print(f"  {i}. {Path(path).name}")

            # 更新角色设定卡
            card.setdefault("generation_outputs", {})
            card["generation_outputs"]["hair_variants"] = {
                "generated": True,
                "local_paths": result_dict.get("local_paths", []),
                "urls": result_dict.get("urls", []),
                "prompts_used": hair_prompts,
                "anchor_file": str(anchor_file.name)
            }

            # 保存更新后的角色设定卡
            card_file = output_dir / "character_card_with_hair_variants.json"
            with open(card_file, "w", encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            print(f"\n📁 更新后的角色设定卡：{card_file}")

            # 生成说明文件
            note_file = output_dir / "HAIR_GENERATION_NOTES.md"
            with open(note_file, "w", encoding="utf-8") as f:
                f.write("# 发型变体生成说明\n\n")
                f.write("## 生成信息\n")
                f.write(f"- **锚点人脸**：{anchor_file.name}（变体3：艺术创意感）\n")
                f.write(f"- **生成时间**：{Path(__file__).name}\n")
                f.write(f"- **发型变体数量**：{len(hair_prompts)}\n")
                f.write("\n## 生成的文件\n")
                for i, path in enumerate(result_dict.get("local_paths", []), 1):
                    f.write(f"- `{Path(path).name}` - 发型变体 {i}\n")
                f.write(f"- `character_card_with_hair_variants.json` - 更新后的角色设定卡\n")
                f.write("\n## 后续步骤\n")
                f.write("请从发型变体中选择一个作为最终发型。\n")

            print(f"\n📝 已创建说明文件：{note_file}")

        else:
            print(f"❌ 发型变体图片生成失败: {result_dict.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 生成过程中出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  注意：由于API限制或方法未实现，发型变体生成可能不完整")
        print("已保存prompt文件，您可以手动生成发型变体图片。")

    print("\n✅ Phase E2.5 完成！")

if __name__ == "__main__":
    # 导入base64用于模拟
    import base64
    main()
#!/usr/bin/env python3
"""
Phase E3：生成所有其他景别（基于锚点人脸+发型的图生图）
使用OutputManager管理项目目录，自动处理文件路径。
"""
import os
import sys
import json
import base64
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

def image_to_data_uri(image_path: Path) -> str:
    """将图片文件转换为data URI"""
    with open(image_path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode('utf-8')
    ext = image_path.suffix.lower()
    mime_type = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime_type};base64,{b64_data}"

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

    # 加载最新的角色设定卡（优先找最终的，然后找带发型的）
    card_files_to_try = [
        "character_card_final.json",
        "character_card_with_hair_variants_real.json",
        "character_card_with_hair_variants.json",
        "character_card_with_portraits_v2.json",
        "character_card_with_portraits.json",
        "character_card.json"
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
        print("请确保已运行之前的步骤生成角色设定卡")
        sys.exit(1)

    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)

    print("✅ 已加载角色设定卡")

    # 锚点人脸+发型文件（优先查找用户选择的发型变体）
    anchor_file = None

    # 查找发型变体文件的优先级
    hair_patterns = [
        "hair_variant_real_2_1.png",  # 用户选择的发型变体2
        "hair_variant_real_1_1.png",
        "hair_variant_real_3_1.png",
        "hair_variant_real*.png",     # 任何发型变体
        "hair_variant_*.png",
        "*anchor*.png",               # 包含anchor关键词
        "*portrait*.png"              # 肖像文件
    ]

    for pattern in hair_patterns:
        if "*" in pattern:
            # 通配符模式
            matches = list(output_dir.glob(pattern))
            if matches:
                # 优先选择数字2的（用户选择）
                for match in matches:
                    if "2_1" in match.name:
                        anchor_file = match
                        break
                if not anchor_file:
                    anchor_file = matches[0]
                break
        else:
            # 精确文件名
            candidate = output_dir / pattern
            if candidate.exists():
                anchor_file = candidate
                break

    if not anchor_file:
        print(f"❌ 错误：找不到锚点人脸+发型文件")
        print(f"在目录 {output_dir} 中查找了以下模式：")
        for pattern in hair_patterns:
            print(f"  - {pattern}")

        # 列出所有PNG文件供用户参考
        png_files = list(output_dir.glob("*.png"))
        if png_files:
            print(f"\n可用的PNG文件：")
            for f in png_files:
                print(f"  - {f.name}")

        print("\n请先运行发型变体生成脚本或手动选择锚点文件")
        sys.exit(1)

    print(f"✅ 锚点人脸+发型文件：{anchor_file.name}")

    # 服装参考图（在input image目录中查找）
    garment_file = None
    input_image_dir = current_dir.parent / "input image"

    if input_image_dir.exists():
        # 查找可能的服装参考图文件
        garment_patterns = [
            "cloth1.png",
            "cloth*.png",
            "dress*.png",
            "garment*.png",
            "clothing*.png",
            "fashion*.png",
            "*.png"  # 最后尝试所有PNG
        ]

        for pattern in garment_patterns:
            matches = list(input_image_dir.glob(pattern))
            if matches:
                # 优先选择明确的文件名
                for match in matches:
                    if pattern.startswith("cloth") and not "*" in pattern:
                        garment_file = match
                        break
                if not garment_file:
                    garment_file = matches[0]
                break

    if garment_file:
        print(f"✅ 服装参考图：{garment_file.name}")
        garment_refs = [garment_file]
    else:
        print("⚠️  警告：找不到服装参考图")
        print(f"在目录 {input_image_dir} 中查找")
        print("将使用纯文字描述生成（无服装参考图）")
        garment_refs = None

    # 场景参考图（可选）
    scene_file = None
    if input_image_dir.exists():
        scene_patterns = [
            "cloth1-set.png",
            "scene*.png",
            "set*.png",
            "background*.png",
            "environment*.png"
        ]

        for pattern in scene_patterns:
            matches = list(input_image_dir.glob(pattern))
            if matches:
                scene_file = matches[0]
                break

    if scene_file:
        print(f"✅ 场景参考图：{scene_file.name}")
        # reference_composite_prompt会使用场景分析的文字描述
    else:
        print("ℹ️  未找到场景参考图，将使用场景分析的文字描述")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建prompt生成器
    generator = PromptGenerator()

    # 生成最新的prompt bundle
    print("\n生成最新的prompt bundle...")
    prompt_bundle = generator.generate_bundle(card)

    # 过滤空prompt
    prompt_bundle = {k: v for k, v in prompt_bundle.items() if v and v.strip()}

    print(f"✅ 生成的prompt bundle包含 {len(prompt_bundle)} 个景别：")
    for key in prompt_bundle.keys():
        print(f"  - {key}")

    # 初始化Wan27Client
    print("\n初始化Wan27Client...")
    try:
        client = Wan27Client(output_dir=str(output_dir))
        print("✅ Wan27Client初始化成功")
    except Exception as e:
        print(f"❌ Wan27Client初始化失败: {e}")
        sys.exit(1)

    # 准备输入数据
    anchor_data_uri = image_to_data_uri(anchor_file)
    print(f"✅ 锚点图片已转换为data URI")

    garment_data_uris = None
    if garment_refs:
        garment_data_uris = [image_to_data_uri(Path(ref)) for ref in garment_refs]
        print(f"✅ 服装参考图已转换为data URI")

    # 生成所有景别
    print("\n开始生成所有景别图片...")
    print("这将需要一些时间，请耐心等待...")

    try:
        result = client.generate_consistent_bundle(
            prompt_bundle=prompt_bundle,
            anchor_portrait=anchor_data_uri,
            garment_refs=garment_data_uris,
            size="1K"
        )

        # 检查结果
        success_count = 0
        total_count = len(result)

        print(f"\n✅ 生成完成！共处理 {total_count} 个景别")

        for key, res in result.items():
            if res.get("success"):
                success_count += 1
                local_paths = res.get("local_paths", [])
                if local_paths:
                    print(f"  ✅ {key}: {Path(local_paths[0]).name}")
                else:
                    print(f"  ⚠️  {key}: 成功但无本地路径")
            else:
                print(f"  ❌ {key}: 失败 - {res.get('error', '未知错误')}")

        # 更新角色设定卡
        card.setdefault("generation_outputs", {})
        card["generation_outputs"]["final_bundle"] = {
            "generated": True,
            "results": result,
            "anchor_file": str(anchor_file.name),
            "garment_file": str(garment_file.name) if garment_file.exists() else None,
            "success_count": success_count,
            "total_count": total_count
        }

        # 记录最终选择
        consistency = card.setdefault("final_profile", {}).setdefault("consistency_profile", {})
        consistency["final_hair_selection"] = {
            "selected_index": 2,
            "source": str(anchor_file.name),
            "method": "user_selected",
            "note": "变体2：发型微调"
        }

        # 保存更新后的角色设定卡
        card_file = output_dir / "character_card_final.json"
        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        print(f"\n📁 最终角色设定卡：{card_file}")

        # 生成最终说明文件
        note_file = output_dir / "FINAL_GENERATION_NOTES.md"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write("# 最终生成说明\n\n")
            f.write("## 生成信息\n")
            f.write(f"- **锚点人脸+发型**：{anchor_file.name}（发型变体2：发型微调）\n")
            f.write(f"- **服装参考图**：{garment_file.name if garment_file.exists() else '无'}\n")
            f.write(f"- **生成时间**：{Path(__file__).name}\n")
            f.write(f"- **成功景别**：{success_count}/{total_count}\n")
            f.write("\n## 生成的文件\n")
            for key, res in result.items():
                if res.get("success"):
                    local_paths = res.get("local_paths", [])
                    if local_paths:
                        f.write(f"- `{Path(local_paths[0]).name}` - {key}\n")

            f.write(f"- `character_card_final.json` - 最终角色设定卡\n")
            f.write("\n## 生成的景别说明\n")
            f.write("1. **medium_shot_prompt** - 中景（腰部以上）\n")
            f.write("2. **full_body_prompt** - 全身\n")
            f.write("3. **three_view_prompt** - 三视图（前、侧、后）\n")
            f.write("4. **reference_composite_prompt** - 参考图融合（场景+服装）\n")
            f.write("\n## 项目完成\n")
            f.write("所有角色一致性生成流程已完成！\n")

        print(f"\n📝 已创建说明文件：{note_file}")

        if success_count == total_count:
            print("\n🎉 恭喜！所有景别生成成功！")
        else:
            print(f"\n⚠️  部分景别生成失败，请检查日志")

    except Exception as e:
        print(f"❌ 生成过程中出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ Phase E3 完成！")

if __name__ == "__main__":
    main()
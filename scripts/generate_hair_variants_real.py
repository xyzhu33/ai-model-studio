#!/usr/bin/env python3
"""
真正生成发型变体图片（使用generate_with_anchor）
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
    # 根据文件扩展名确定MIME类型
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

    # 将锚点图片转换为data URI
    anchor_data_uri = image_to_data_uri(anchor_file)
    print(f"✅ 锚点图片已转换为data URI（长度：{len(anchor_data_uri)}）")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取发型变体prompts（使用之前生成的v2文件）
    hair_prompts_file = output_dir / "hair_variant_prompts_v2.txt"
    if not hair_prompts_file.exists():
        print(f"错误：找不到发型变体prompts文件 {hair_prompts_file}")
        # 重新生成
        generator = PromptGenerator()
        hair_prompts = generator.generate_hair_variants_prompts(card, n=3)
    else:
        # 从文件读取
        with open(hair_prompts_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析prompts
        prompts = []
        lines = content.split('\n')
        current_prompt = []
        in_prompt = False

        for line in lines:
            if line.startswith('--- 发型变体'):
                if current_prompt:
                    prompts.append(' '.join(current_prompt))
                    current_prompt = []
                in_prompt = True
            elif in_prompt and line.strip() and not line.startswith('==='):
                current_prompt.append(line.strip())

        if current_prompt:
            prompts.append(' '.join(current_prompt))

        hair_prompts = [p.strip() for p in prompts if p.strip()]

        if len(hair_prompts) < 3:
            print(f"警告：只找到 {len(hair_prompts)} 个prompt，需要3个")
            # 重新生成
            generator = PromptGenerator()
            hair_prompts = generator.generate_hair_variants_prompts(card, n=3)

    print(f"✅ 加载了 {len(hair_prompts)} 个发型变体prompt")

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
    print("前缀：hair_variant_real")

    all_paths = []
    all_urls = []
    all_raw = []

    for i, prompt in enumerate(hair_prompts, 1):
        print(f"\n生成发型变体 {i}...")

        try:
            result = client.generate_with_anchor(
                prompt=prompt,
                anchor_portrait=anchor_data_uri,
                garment_refs=None,  # 发型变体不需要服装参考
                size="1K",
                prefix=f"hair_variant_real_{i}",
                enable_sequential=False,
                n=1
            )

            if result.get("success"):
                local_paths = result.get("local_paths", [])
                if local_paths:
                    local_path = local_paths[0]
                    all_paths.append(local_path)
                    all_urls.append(result.get("urls", [])[0] if result.get("urls") else "")
                    all_raw.append(result.get("raw_results", [])[0] if result.get("raw_results") else {})
                    print(f"  ✅ 生成成功：{Path(local_path).name}")
                else:
                    print(f"  ⚠️  生成成功但未返回本地路径")
            else:
                print(f"  ❌ 生成失败：{result.get('error', '未知错误')}")

        except Exception as e:
            print(f"  ❌ 生成过程中出错：{e}")

    if all_paths:
        print("\n✅ 发型变体图片生成完成！")
        print(f"生成的图片：")
        for i, path in enumerate(all_paths, 1):
            print(f"  {i}. {Path(path).name}")

        # 更新角色设定卡
        consistency = card.setdefault("final_profile", {}).setdefault("consistency_profile", {})
        consistency["anchor_portrait"] = {
            "selected_index": 3,
            "source": str(anchor_file.name),
            "method": "user_selected",
            "note": "变体3：艺术创意感，妆容调整版"
        }

        card.setdefault("generation_outputs", {})
        card["generation_outputs"]["hair_variants_real"] = {
            "generated": True,
            "local_paths": all_paths,
            "urls": all_urls,
            "prompts_used": hair_prompts,
            "anchor_file": str(anchor_file.name)
        }

        # 保存更新后的角色设定卡
        card_file = output_dir / "character_card_with_hair_variants_real.json"
        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        print(f"\n📁 更新后的角色设定卡：{card_file}")

        # 生成说明文件
        note_file = output_dir / "HAIR_GENERATION_REAL_NOTES.md"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write("# 发型变体生成说明（真实API调用）\n\n")
            f.write("## 生成信息\n")
            f.write(f"- **锚点人脸**：{anchor_file.name}（变体3：艺术创意感）\n")
            f.write(f"- **生成方法**：使用generate_with_anchor API调用\n")
            f.write(f"- **发型变体数量**：{len(hair_prompts)}\n")
            f.write("\n## 生成的文件\n")
            for i, path in enumerate(all_paths, 1):
                f.write(f"- `{Path(path).name}` - 发型变体 {i}\n")
            f.write(f"- `character_card_with_hair_variants_real.json` - 更新后的角色设定卡\n")
            f.write("\n## 后续步骤\n")
            f.write("请从发型变体中选择一个作为最终发型。\n")

        print(f"\n📝 已创建说明文件：{note_file}")

    else:
        print("\n❌ 没有成功生成任何发型变体图片")

    print("\n✅ 脚本执行完成！")

if __name__ == "__main__":
    main()
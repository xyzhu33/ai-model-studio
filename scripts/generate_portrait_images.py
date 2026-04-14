#!/usr/bin/env python3
"""
尝试生成面部特写候选图片（Phase E1）
"""
import os
import sys
import json
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from wan27_client import Wan27Client
    HAS_WAN27 = True
except ImportError as e:
    print(f"导入Wan27Client失败: {e}")
    HAS_WAN27 = False
except ValueError as e:
    print(f"Wan27Client初始化失败（缺少API密钥）: {e}")
    HAS_WAN27 = False

try:
    from output_manager import OutputManager
    HAS_OUTPUT_MANAGER = True
except ImportError as e:
    print(f"导入OutputManager失败: {e}")
    print("⚠️  将使用默认输出目录")
    HAS_OUTPUT_MANAGER = False

def main():
    # 加载角色设定卡
    card_path = current_dir.parent / "temp_character_card.json"
    if not card_path.exists():
        print(f"错误：找不到角色设定卡 {card_path}")
        sys.exit(1)

    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)

    # 获取或创建输出目录
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

    print(f"📁 输出目录：{output_dir}")

    # 检查是否已生成prompt变体文件
    portrait_prompts_file = output_dir / "portrait_prompt_variants.txt"
    if not portrait_prompts_file.exists():
        print(f"错误：找不到prompt变体文件 {portrait_prompts_file}")
        print("请先运行 generate_prompts.py")
        sys.exit(1)

    # 读取prompt变体
    with open(portrait_prompts_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析prompt变体（简单解析）
    prompts = []
    lines = content.split('\n')
    current_prompt = []
    in_prompt = False

    for line in lines:
        if line.startswith('--- 变体'):
            if current_prompt:
                prompts.append(' '.join(current_prompt))
                current_prompt = []
            in_prompt = True
        elif in_prompt and line.strip() and not line.startswith('==='):
            current_prompt.append(line.strip())

    if current_prompt:
        prompts.append(' '.join(current_prompt))

    # 清理空prompt
    prompts = [p.strip() for p in prompts if p.strip()]

    if len(prompts) < 3:
        print(f"警告：只找到 {len(prompts)} 个prompt，需要3个")
        # 如果不够，使用单个prompt重复
        if prompts:
            prompts = prompts * (3 // len(prompts) + 1)
            prompts = prompts[:3]
        else:
            print("错误：没有可用的prompt")
            sys.exit(1)

    print(f"找到 {len(prompts)} 个prompt变体")
    for i, p in enumerate(prompts, 1):
        print(f"\n--- Prompt {i} (前100字符) ---")
        print(p[:100] + "..." if len(p) > 100 else p)

    # 尝试生成图片
    if not HAS_WAN27:
        print("\n❌ 无法生成图片：Wan27Client不可用")
        print("可能原因：")
        print("1. 缺少DASHSCOPE_API_KEY环境变量")
        print("2. wan27_client.py模块缺失或错误")
        print("\n已保存prompt文件，您可以：")
        print("1. 设置DASHSCOPE_API_KEY环境变量")
        print("2. 使用其他工具生成图片")

        # 创建说明文件
        note_file = output_dir / "IMAGE_GENERATION_NOTES.md"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write("# 图片生成说明\n\n")
            f.write("## 状态\n")
            f.write("❌ 图片生成失败：缺少API密钥或Wan27Client不可用\n\n")
            f.write("## 已生成的prompt文件\n")
            f.write("以下prompt文件已生成，可用于手动生成图片：\n")
            f.write("- `portrait_prompt_variants.txt` - 3个面部特写prompt变体\n")
            f.write("- `single_portrait_prompt.txt` - 单个面部特写prompt\n")
            f.write("- `hair_variant_prompts.txt` - 3个发型变体prompt\n")
            f.write("- `prompt_bundle.json` - 完整prompt bundle\n\n")
            f.write("## 后续步骤\n")
            f.write("1. 设置DASHSCOPE_API_KEY环境变量：\n")
            f.write("   ```bash\n")
            f.write("   export DASHSCOPE_API_KEY='your-api-key'\n")
            f.write("   ```\n")
            f.write("2. 重新运行图片生成脚本\n")
            f.write("3. 或使用其他AI图像生成工具导入prompt\n")

        print(f"\n📝 已创建说明文件：{note_file}")
        sys.exit(0)

    print("\n尝试初始化Wan27Client...")
    try:
        client = Wan27Client(output_dir=str(output_dir))
        print("✅ Wan27Client初始化成功")
    except Exception as e:
        print(f"❌ Wan27Client初始化失败: {e}")
        print("请检查DASHSCOPE_API_KEY环境变量")
        sys.exit(1)

    print("\n开始生成面部特写候选图片...")
    print(f"使用 {len(prompts)} 个差异化prompt")

    try:
        result = client.generate_portrait_options(
            prompts=prompts,
            n=len(prompts),
            prefix="portrait_option",
            size="1K"
        )

        if result.get("success"):
            print("✅ 图片生成成功！")
            print(f"生成的图片：")
            for i, path in enumerate(result.get("local_paths", []), 1):
                print(f"  {i}. {Path(path).name}")

            # 更新角色设定卡中的锚点信息
            card.setdefault("generation_outputs", {})
            card["generation_outputs"]["portrait_options"] = {
                "generated": True,
                "local_paths": result.get("local_paths", []),
                "urls": result.get("urls", []),
                "prompts_used": prompts
            }

            # 保存更新后的角色设定卡
            card_file = output_dir / "character_card_with_portraits.json"
            with open(card_file, "w", encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            print(f"\n📁 更新后的角色设定卡：{card_file}")

        else:
            print(f"❌ 图片生成失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 生成过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
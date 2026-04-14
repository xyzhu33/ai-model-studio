#!/usr/bin/env python3
"""
项目文件夹自动命名工具
根据用户输入自动生成项目文件夹名称，遵循SKILL.md中的文件组织约定。
"""

import re
import os
from pathlib import Path
from typing import List, Optional, Dict, Tuple

class ProjectNamer:
    """自动生成项目文件夹名称"""

    # 中英文关键词映射（常用服装和风格词汇）
    KEYWORD_MAP: Dict[str, List[str]] = {
        # 服装类型
        "裙子": ["dress", "skirt"],
        "连衣裙": ["dress", "gown"],
        "旗袍": ["qipao", "cheongsam"],
        "汉服": ["hanfu", "traditional"],
        "西装": ["suit", "blazer"],
        "外套": ["jacket", "coat"],
        "上衣": ["top", "blouse"],
        "裤子": ["pants", "trousers"],
        "婚纱": ["wedding", "bridal", "wedding_dress"],
        "礼服": ["gown", "formal", "evening_dress"],

        # 风格描述
        "新中式": ["neo_chinese", "modern_chinese"],
        "中式": ["chinese", "traditional"],
        "现代": ["modern", "contemporary"],
        "复古": ["vintage", "retro"],
        "优雅": ["elegant", "graceful"],
        "时尚": ["fashion", "trendy"],
        "休闲": ["casual", "leisure"],
        "商务": ["business", "professional"],
        "街头": ["street", "urban"],
        "文艺": ["artsy", "bohemian"],

        # 颜色特征
        "紫色": ["purple", "violet"],
        "红色": ["red", "crimson"],
        "蓝色": ["blue", "azure"],
        "绿色": ["green", "emerald"],
        "黑色": ["black", "dark"],
        "白色": ["white", "ivory"],
        "粉色": ["pink", "rose"],
        "灰色": ["gray", "grey"],
        "金色": ["gold", "golden"],
        "银色": ["silver", "metallic"],

        # 场景类型
        "庭院": ["garden", "courtyard"],
        "室内": ["indoor", "interior"],
        "室外": ["outdoor", "exterior"],
        "办公室": ["office", "workspace"],
        "街道": ["street", "alley"],
        "海边": ["beach", "seaside"],
        "森林": ["forest", "woods"],
        "摄影棚": ["studio", "photography"],
    }

    # 停用词（不用于命名的常见词汇）
    STOP_WORDS = {"模特", "展示", "妆造", "发型", "发", "的", "和", "与", "在", "有", "是", "一个", "一种"}

    @classmethod
    def extract_keywords(cls, text: str, max_keywords: int = 3) -> List[str]:
        """从用户输入文本中提取关键词"""
        keywords = []

        # 1. 检查是否有直接匹配的中文关键词
        for chinese, english_list in cls.KEYWORD_MAP.items():
            if chinese in text:
                # 使用第一个英文翻译
                keywords.append(english_list[0])
                if len(keywords) >= max_keywords:
                    break

        # 2. 如果中文关键词不够，尝试其他方法
        if len(keywords) < max_keywords:
            # 提取名词性短语（简单实现：2-4字的中文词组）
            words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
            for word in words:
                if word not in cls.STOP_WORDS and word not in text:  # 避免重复
                    # 尝试转换为拼音或简单翻译
                    simple_translation = cls._simple_translate(word)
                    if simple_translation:
                        keywords.append(simple_translation)
                        if len(keywords) >= max_keywords:
                            break

        # 3. 如果还不够，使用默认名称
        if not keywords:
            keywords = ["fashion", "model"]

        return keywords[:max_keywords]

    @classmethod
    def _simple_translate(cls, chinese_word: str) -> Optional[str]:
        """简单的中文到英文翻译（使用映射表）"""
        for chinese, english_list in cls.KEYWORD_MAP.items():
            if chinese_word in chinese or chinese in chinese_word:
                return english_list[0]
        return None

    @classmethod
    def generate_folder_name(cls, text: str, base_output_dir: Path) -> str:
        """
        生成项目文件夹名称，自动处理版本号

        Args:
            text: 用户输入文本
            base_output_dir: output目录的Path对象

        Returns:
            完整的项目文件夹名称（如：neo_chinese_purple_dress_v3）
        """
        # 提取关键词
        keywords = cls.extract_keywords(text, max_keywords=3)

        # 构建基础名称
        if len(keywords) >= 2:
            base_name = "_".join(keywords[:2])
        else:
            base_name = keywords[0] if keywords else "fashion_project"

        # 检查版本号
        version = 1
        folder_name = f"{base_name}_v{version}"

        # 查找现有版本
        while (base_output_dir / folder_name).exists():
            version += 1
            folder_name = f"{base_name}_v{version}"

        return folder_name

    @classmethod
    def get_or_create_project_dir(cls, text: str, skill_root: Path) -> Path:
        """
        获取或创建项目目录

        Args:
            text: 用户输入文本
            skill_root: skill根目录（包含output/的目录）

        Returns:
            项目目录的Path对象
        """
        output_dir = skill_root / "output"
        output_dir.mkdir(exist_ok=True)

        folder_name = cls.generate_folder_name(text, output_dir)
        project_dir = output_dir / folder_name
        project_dir.mkdir(exist_ok=True)

        return project_dir

    @classmethod
    def create_readme(cls, project_dir: Path, text: str, folder_name: str) -> None:
        """创建项目README文件"""
        readme_content = f"""# {folder_name}

## 项目信息
- **生成时间**: {Path(__file__).name}
- **用户输入**: {text}
- **项目文件夹**: {folder_name}

## 文件说明
1. `character_card.json` - 角色设定卡
2. `portrait_prompt_variants.txt` - 面部特写prompt变体
3. `prompt_bundle.json` - 完整prompt bundle
4. `*.png` - 生成图片文件
5. 其他相关文档

## 命名依据
项目名称基于用户输入自动生成：
- 原始输入: "{text}"
- 提取关键词: {cls.extract_keywords(text)}
- 命名规则: 关键词1_关键词2_vN
"""

        readme_file = project_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)


def main():
    """命令行测试"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python project_namer.py '用户输入文本'")
        print("示例: python project_namer.py '亚裔模特，黑色微卷发，新中式妆造，展示紫色裙子'")
        sys.exit(1)

    text = sys.argv[1]
    skill_root = Path(__file__).parent.parent

    print(f"用户输入: {text}")
    print(f"提取关键词: {ProjectNamer.extract_keywords(text)}")

    project_dir = ProjectNamer.get_or_create_project_dir(text, skill_root)
    print(f"项目目录: {project_dir}")

    # 创建README
    ProjectNamer.create_readme(project_dir, text, project_dir.name)
    print(f"已创建README: {project_dir}/README.md")


if __name__ == "__main__":
    main()
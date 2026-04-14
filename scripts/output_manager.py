#!/usr/bin/env python3
"""
输出目录管理模块
统一管理ai-model-studio的项目目录创建和访问，确保所有脚本使用一致的目录结构。
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from project_namer import ProjectNamer


class OutputManager:
    """管理项目输出目录，确保文件组织有序"""

    # 存储当前项目信息的文件
    CURRENT_PROJECT_FILE = ".current_project.json"

    @classmethod
    def init_project(cls, user_input: str, skill_root: Optional[Path] = None) -> Path:
        """
        初始化项目目录，基于用户输入自动创建项目文件夹

        Args:
            user_input: 用户输入的文本描述
            skill_root: skill根目录，如果为None则自动检测

        Returns:
            项目目录的Path对象
        """
        if skill_root is None:
            skill_root = Path(__file__).parent.parent

        # 使用ProjectNamer创建项目目录
        project_dir = ProjectNamer.get_or_create_project_dir(user_input, skill_root)

        # 创建项目README
        ProjectNamer.create_readme(project_dir, user_input, project_dir.name)

        # 保存当前项目信息
        project_info = {
            "project_name": project_dir.name,
            "user_input": user_input,
            "created_at": datetime.now().isoformat(),
            "project_dir": str(project_dir),
            "skill_root": str(skill_root)
        }

        # 保存到项目目录
        info_file = project_dir / cls.CURRENT_PROJECT_FILE
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)

        # 保存到scripts目录供其他脚本访问
        scripts_info_file = skill_root / "scripts" / cls.CURRENT_PROJECT_FILE
        with open(scripts_info_file, "w", encoding="utf-8") as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)

        print(f"✅ 项目初始化完成: {project_dir.name}")
        print(f"📁 项目目录: {project_dir}")
        print(f"📝 用户输入: {user_input[:100]}..." if len(user_input) > 100 else f"📝 用户输入: {user_input}")

        return project_dir

    @classmethod
    def get_current_project_dir(cls, skill_root: Optional[Path] = None) -> Path:
        """
        获取当前项目目录

        Args:
            skill_root: skill根目录，如果为None则自动检测

        Returns:
            当前项目目录的Path对象

        Raises:
            FileNotFoundError: 如果找不到当前项目信息
        """
        if skill_root is None:
            skill_root = Path(__file__).parent.parent

        # 首先检查scripts目录中的当前项目文件
        scripts_info_file = skill_root / "scripts" / cls.CURRENT_PROJECT_FILE
        if scripts_info_file.exists():
            with open(scripts_info_file, "r", encoding="utf-8") as f:
                project_info = json.load(f)

            project_dir = Path(project_info["project_dir"])
            if project_dir.exists():
                return project_dir

        # 如果scripts目录中没有，查找output目录中最新的项目
        output_dir = skill_root / "output"
        if output_dir.exists():
            # 查找所有包含.current_project.json的目录
            project_dirs = []
            for item in output_dir.iterdir():
                if item.is_dir():
                    info_file = item / cls.CURRENT_PROJECT_FILE
                    if info_file.exists():
                        project_dirs.append(item)

            # 按创建时间排序（最新的在前）
            if project_dirs:
                project_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return project_dirs[0]

        # 如果都找不到，检查是否有neo_chinese_model_v3（兼容旧版本）
        legacy_dir = output_dir / "neo_chinese_model_v3"
        if legacy_dir.exists():
            print(f"⚠️  使用旧版目录: {legacy_dir.name}")
            return legacy_dir

        raise FileNotFoundError(
            f"找不到当前项目目录。请先运行OutputManager.init_project()初始化项目。"
            f"搜索路径: {output_dir}"
        )

    @classmethod
    def get_current_project_info(cls, skill_root: Optional[Path] = None) -> Dict[str, Any]:
        """
        获取当前项目信息

        Returns:
            项目信息字典
        """
        project_dir = cls.get_current_project_dir(skill_root)
        info_file = project_dir / cls.CURRENT_PROJECT_FILE

        if info_file.exists():
            with open(info_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # 如果项目信息文件不存在，创建基本信息
        return {
            "project_name": project_dir.name,
            "project_dir": str(project_dir),
            "skill_root": str(skill_root or Path(__file__).parent.parent)
        }

    @classmethod
    def ensure_subdirectories(cls, project_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        确保项目目录中存在必要的子目录

        Args:
            project_dir: 项目目录，如果为None则使用当前项目目录

        Returns:
            子目录路径的字典
        """
        if project_dir is None:
            project_dir = cls.get_current_project_dir()

        subdirs = {
            "images": project_dir / "images",
            "temp": project_dir / "temp",
            "logs": project_dir / "logs",
            "backups": project_dir / "backups"
        }

        for name, path in subdirs.items():
            path.mkdir(exist_ok=True)

        return subdirs

    @classmethod
    def get_output_path(cls, filename: str, subdir: Optional[str] = None) -> Path:
        """
        获取输出文件的完整路径

        Args:
            filename: 文件名（可包含子目录）
            subdir: 可选子目录名称

        Returns:
            完整的文件路径
        """
        project_dir = cls.get_current_project_dir()

        if subdir:
            output_dir = project_dir / subdir
            output_dir.mkdir(exist_ok=True)
            return output_dir / filename
        else:
            return project_dir / filename

    @classmethod
    def backup_file(cls, filepath: Path, backup_name: Optional[str] = None) -> Path:
        """
        备份文件到backups目录

        Args:
            filepath: 要备份的文件路径
            backup_name: 备份文件名称，如果为None则使用原文件名+时间戳

        Returns:
            备份文件的路径
        """
        if not filepath.exists():
            raise FileNotFoundError(f"要备份的文件不存在: {filepath}")

        project_dir = cls.get_current_project_dir()
        backups_dir = project_dir / "backups"
        backups_dir.mkdir(exist_ok=True)

        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"

        backup_path = backups_dir / backup_name
        shutil.copy2(filepath, backup_path)

        return backup_path

    @classmethod
    def list_generated_files(cls, pattern: str = "*.png") -> Dict[str, list]:
        """
        列出项目目录中生成的文件

        Args:
            pattern: 文件模式，如"*.png", "*.json"等

        Returns:
            按文件类型组织的文件列表字典
        """
        project_dir = cls.get_current_project_dir()

        files_by_type = {
            "images": [],
            "json_files": [],
            "text_files": [],
            "markdown_files": [],
            "other": []
        }

        for filepath in project_dir.rglob(pattern):
            if filepath.is_file():
                rel_path = filepath.relative_to(project_dir)

                if filepath.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    files_by_type["images"].append(str(rel_path))
                elif filepath.suffix.lower() == ".json":
                    files_by_type["json_files"].append(str(rel_path))
                elif filepath.suffix.lower() in [".txt", ".csv"]:
                    files_by_type["text_files"].append(str(rel_path))
                elif filepath.suffix.lower() == ".md":
                    files_by_type["markdown_files"].append(str(rel_path))
                else:
                    files_by_type["other"].append(str(rel_path))

        return files_by_type


def main():
    """命令行接口：初始化项目或获取项目信息"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="AI Model Studio 输出目录管理")
    parser.add_argument("--init", metavar="TEXT", help="初始化新项目，提供用户输入文本")
    parser.add_argument("--current-dir", action="store_true", help="显示当前项目目录")
    parser.add_argument("--current-info", action="store_true", help="显示当前项目信息")
    parser.add_argument("--list-files", metavar="PATTERN", nargs="?", const="*",
                       help="列出项目文件（可选文件模式，如'*.png'）")
    parser.add_argument("--ensure-dirs", action="store_true", help="确保创建必要的子目录")

    args = parser.parse_args()

    if args.init:
        # 初始化新项目
        project_dir = OutputManager.init_project(args.init)
        print(f"✅ 项目已初始化: {project_dir}")

    elif args.current_dir:
        # 显示当前项目目录
        try:
            project_dir = OutputManager.get_current_project_dir()
            print(f"📁 当前项目目录: {project_dir}")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)

    elif args.current_info:
        # 显示当前项目信息
        try:
            info = OutputManager.get_current_project_info()
            print("📋 当前项目信息:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)

    elif args.list_files:
        # 列出文件
        try:
            files = OutputManager.list_generated_files(args.list_files)
            print("📁 项目文件:")
            for file_type, file_list in files.items():
                if file_list:
                    print(f"\n{file_type} ({len(file_list)}):")
                    for filepath in file_list[:20]:  # 限制显示数量
                        print(f"  - {filepath}")
                    if len(file_list) > 20:
                        print(f"  ... 和 {len(file_list) - 20} 个更多文件")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)

    elif args.ensure_dirs:
        # 确保子目录存在
        try:
            subdirs = OutputManager.ensure_subdirectories()
            print("✅ 子目录已确保创建:")
            for name, path in subdirs.items():
                print(f"  {name}: {path}")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
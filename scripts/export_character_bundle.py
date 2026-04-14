#!/usr/bin/env python3
"""
Export utility for virtual-character-builder skill.
将角色设定卡、prompt bundle、生成结果打包导出。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from character_card import CharacterCardBuilder


class CharacterBundleExporter:
    """将角色构建全流程产物打包为可交付 bundle。"""

    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)

    def export(
        self,
        card: Dict[str, Any],
        prompt_bundle: Dict[str, str],
        generation_results: Optional[Dict[str, Dict[str, Any]]] = None,
        character_name: Optional[str] = None,
        template_path: Optional[str] = None,
    ) -> str:
        """导出完整角色 bundle，返回 bundle 目录路径。"""
        name = self._resolve_name(card, character_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bundle_dir = self.base_output_dir / f"{name}_{timestamp}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # 1. 角色设定卡 JSON
        self._save_json(card, bundle_dir / "character_card.json")

        # 2. 角色设定卡 Markdown
        if template_path:
            builder = CharacterCardBuilder(template_path)
            md_content = builder.to_markdown(card)
        else:
            md_content = self._card_to_markdown(card, prompt_bundle)
        (bundle_dir / "character_card.md").write_text(md_content, encoding="utf-8")

        # 3. Prompt bundle JSON
        self._save_json(prompt_bundle, bundle_dir / "prompt_bundle.json")

        # 4. Prompt bundle 可读文本
        self._save_prompt_text(prompt_bundle, bundle_dir / "prompts.txt")

        # 5. 收集生成图片
        if generation_results:
            images_dir = bundle_dir / "images"
            images_dir.mkdir(exist_ok=True)
            image_manifest = self._collect_images(generation_results, images_dir)
            self._save_json(image_manifest, bundle_dir / "image_manifest.json")

        # 6. 生成结果元数据（去掉 raw API 响应中的大体积数据）
        if generation_results:
            meta = self._build_generation_meta(generation_results)
            self._save_json(meta, bundle_dir / "generation_meta.json")

        # 7. 汇总 manifest
        manifest = self._build_manifest(
            card, prompt_bundle, generation_results, name, bundle_dir
        )
        self._save_json(manifest, bundle_dir / "manifest.json")

        return str(bundle_dir)

    def _resolve_name(self, card: Dict[str, Any], name: Optional[str]) -> str:
        if name:
            return self._sanitize(name)
        one_line = card.get("draft_profile", {}).get("one_line_concept", "")
        if one_line:
            return self._sanitize(one_line[:30])
        role = card.get("final_profile", {}).get("identity", {}).get("role_or_background", "")
        if role:
            return self._sanitize(role[:30])
        return "character"

    @staticmethod
    def _sanitize(text: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in text.strip())
        return safe.strip("_")[:40] or "character"

    @staticmethod
    def _save_json(data: Any, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _save_prompt_text(prompt_bundle: Dict[str, str], path: Path) -> None:
        lines: List[str] = []
        for key, prompt in prompt_bundle.items():
            if not prompt:
                continue
            label = key.replace("_prompt", "").replace("_", " ").title()
            lines.append(f"=== {label} ===")
            lines.append(prompt)
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _collect_images(
        self, generation_results: Dict[str, Dict[str, Any]], images_dir: Path
    ) -> Dict[str, List[str]]:
        """将各生成结果中的本地图片复制到 images_dir，返回 manifest。"""
        manifest: Dict[str, List[str]] = {}
        for key, result in generation_results.items():
            local_paths = result.get("local_paths", [])
            if not local_paths:
                continue
            label = key.replace("_prompt", "")
            copied: List[str] = []
            for i, src in enumerate(local_paths):
                src_path = Path(src)
                if src_path.exists():
                    dst = images_dir / f"{label}_{i+1}{src_path.suffix}"
                    shutil.copy2(src_path, dst)
                    copied.append(dst.name)
            if copied:
                manifest[label] = copied
        return manifest

    @staticmethod
    def _build_generation_meta(
        generation_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        meta: Dict[str, Any] = {}
        for key, result in generation_results.items():
            label = key.replace("_prompt", "")
            meta[label] = {
                "success": result.get("success", False),
                "image_count": len(result.get("urls", [])),
                "urls": result.get("urls", []),
                "local_paths": result.get("local_paths", []),
            }
        return meta

    def _build_manifest(
        self,
        card: Dict[str, Any],
        prompt_bundle: Dict[str, str],
        generation_results: Optional[Dict[str, Dict[str, Any]]],
        name: str,
        bundle_dir: Path,
    ) -> Dict[str, Any]:
        scenario = card.get("final_profile", {}).get(
            "scenario_type",
            card.get("scenario_guess", {}).get("value", ""),
        )
        mode = card.get("mode", {}).get("selected", "fast")

        prompt_keys = [k for k, v in prompt_bundle.items() if v]

        total_images = 0
        if generation_results:
            for r in generation_results.values():
                total_images += len(r.get("local_paths", []))

        return {
            "character_name": name,
            "scenario_type": scenario,
            "mode": mode,
            "exported_at": datetime.now().isoformat(),
            "files": {
                "character_card_json": "character_card.json",
                "character_card_md": "character_card.md",
                "prompt_bundle_json": "prompt_bundle.json",
                "prompts_txt": "prompts.txt",
                "image_manifest": "image_manifest.json" if generation_results else None,
                "generation_meta": "generation_meta.json" if generation_results else None,
            },
            "prompt_types_generated": prompt_keys,
            "total_images": total_images,
            "bundle_dir": str(bundle_dir),
        }

    def _card_to_markdown(
        self, card: Dict[str, Any], prompt_bundle: Dict[str, str]
    ) -> str:
        """不依赖 CharacterCardBuilder 实例的 markdown 生成。"""
        lines: List[str] = []
        lines.append("# 角色设定卡")
        lines.append("")

        # 草案判断
        sg = card.get("scenario_guess", {})
        lines.append("## 场景判断")
        lines.append(f"- 推荐场景: {sg.get('value', '')}")
        lines.append(f"- 置信度: {sg.get('confidence', '')}")
        reasoning = sg.get("reasoning", [])
        if reasoning:
            lines.append(f"- 原因: {'; '.join(str(r) for r in reasoning)}")
        lines.append("")

        # 草案概览
        draft = card.get("draft_profile", {})
        lines.append("## 草案概览")
        lines.append(f"- 一句话概述: {draft.get('one_line_concept', '')}")
        rec = draft.get("recommended_direction", {})
        for key in ["aesthetic", "identity", "appearance", "styling"]:
            if rec.get(key):
                lines.append(f"- {key}: {rec[key]}")
        sp = rec.get("signature_points", [])
        if sp:
            lines.append(f"- signature_points: {', '.join(str(s) for s in sp)}")
        assumptions = draft.get("assumptions", [])
        if assumptions:
            lines.append(f"- assumptions: {'; '.join(str(a) for a in assumptions)}")
        lines.append("")

        # 最终设定
        fp = card.get("final_profile", {})
        lines.append("## 最终设定")
        lines.append(f"- scenario_type: {fp.get('scenario_type', '')}")
        for section in ["identity", "physical_appearance", "styling", "consistency_profile"]:
            data = fp.get(section, {})
            if data:
                lines.append(f"- {section}: {json.dumps(data, ensure_ascii=False)}")
        lines.append("")

        # Prompts
        lines.append("## 输出 Prompts")
        for key in [
            "close_up_prompt",
            "medium_shot_prompt",
            "full_body_prompt",
            "three_view_prompt",
            "expression_sheet_prompt",
            "reference_composite_prompt",
        ]:
            prompt = prompt_bundle.get(key, "")
            if prompt:
                label = key.replace("_prompt", "").replace("_", " ").title()
                lines.append(f"### {label}")
                lines.append("```")
                lines.append(prompt)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

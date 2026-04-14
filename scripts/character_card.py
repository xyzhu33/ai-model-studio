#!/usr/bin/env python3
"""
Character card builder for virtual-character-builder skill.
将草案、模式选择、最终确认结果汇总为统一角色设定卡。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class CharacterCardBuilder:
    """构建角色设定卡。"""

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.template = self._load_template()

    def _load_template(self) -> Dict[str, Any]:
        with open(self.template_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def new_card(self) -> Dict[str, Any]:
        return copy.deepcopy(self.template)

    def build(
        self,
        scenario_guess: Dict[str, Any],
        source_summary: Dict[str, Any],
        draft_profile: Dict[str, Any],
        mode: str = "fast",
        final_profile: Optional[Dict[str, Any]] = None,
        generation_outputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        card = self.new_card()
        card["scenario_guess"] = scenario_guess or card["scenario_guess"]
        card["source_summary"] = source_summary or card["source_summary"]
        card["draft_profile"] = draft_profile or card["draft_profile"]
        card["mode"]["selected"] = mode or "fast"

        if final_profile:
            card["final_profile"] = self._deep_merge(card["final_profile"], final_profile)
        if generation_outputs:
            card["generation_outputs"] = self._deep_merge(card["generation_outputs"], generation_outputs)

        return card

    def apply_mode_defaults(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """根据模式自动补全一些默认值。"""
        mode = card.get("mode", {}).get("selected", "fast")
        final_profile = card.setdefault("final_profile", {})
        consistency = final_profile.setdefault("consistency_profile", {})

        if mode == "fast":
            consistency.setdefault("variation_rules", [])
            consistency["variation_rules"] = list(dict.fromkeys(consistency["variation_rules"] + [
                "Prefer stable front-facing outputs before stylized variations",
                "Preserve main silhouette and face identity across all outputs"
            ]))
        elif mode == "pro":
            consistency.setdefault("variation_rules", [])
            consistency["variation_rules"] = list(dict.fromkeys(consistency["variation_rules"] + [
                "Strictly preserve face, hair, body proportion, and outfit structure",
                "Only vary fields explicitly marked as allowed variations"
            ]))

        return card

    @staticmethod
    def build_seed_core(final_profile: Dict[str, Any]) -> str:
        identity = final_profile.get("identity", {})
        appearance = final_profile.get("physical_appearance", {})
        styling = final_profile.get("styling", {})
        consistency = final_profile.get("consistency_profile", {})

        parts: List[str] = ["same character"]

        apparent_age = identity.get("apparent_age")
        gender_expression = identity.get("gender_expression")
        role = identity.get("role_or_background")
        if apparent_age:
            parts.append(str(apparent_age))
        if gender_expression:
            parts.append(str(gender_expression))
        if role:
            parts.append(str(role))

        hair = appearance.get("hair", {})
        if hair.get("color"):
            parts.append(str(hair["color"]))
        if hair.get("style"):
            parts.append(str(hair["style"]))

        face = appearance.get("face", {})
        for key in ["shape", "features", "eye_shape", "eye_color"]:
            value = face.get(key)
            if isinstance(value, list):
                parts.extend([str(v) for v in value if v])
            elif value:
                parts.append(str(value))

        signature_points = styling.get("fit_to_refs", [])
        if signature_points:
            parts.extend([str(v) for v in signature_points if v])

        must_keep = consistency.get("must_keep", [])
        if must_keep:
            parts.extend([str(v) for v in must_keep if v])

        deduped = []
        seen = set()
        for item in parts:
            norm = item.strip().lower()
            if item and norm not in seen:
                deduped.append(item.strip())
                seen.add(norm)

        return ", ".join(deduped)

    def to_markdown(self, card: Dict[str, Any]) -> str:
        lines: List[str] = []
        lines.append("# 角色设定卡")
        lines.append("")

        scenario_guess = card.get("scenario_guess", {})
        lines.append("## 草案判断")
        lines.append(f"- 推荐场景: {scenario_guess.get('value', '')}")
        lines.append(f"- 置信度: {scenario_guess.get('confidence', '')}")
        reasoning = scenario_guess.get("reasoning", [])
        if reasoning:
            lines.append(f"- 原因: {'; '.join(reasoning)}")
        lines.append("")

        draft = card.get("draft_profile", {})
        lines.append("## 草案概览")
        lines.append(f"- 一句话概述: {draft.get('one_line_concept', '')}")
        rec = draft.get("recommended_direction", {})
        for key in ["aesthetic", "identity", "appearance", "styling"]:
            if rec.get(key):
                lines.append(f"- {key}: {rec.get(key)}")
        if rec.get("signature_points"):
            lines.append(f"- signature_points: {', '.join(rec.get('signature_points', []))}")
        if draft.get("assumptions"):
            lines.append(f"- assumptions: {'; '.join(draft.get('assumptions', []))}")
        lines.append("")

        lines.append("## 最终设定")
        final_profile = card.get("final_profile", {})
        lines.append(f"- scenario_type: {final_profile.get('scenario_type', '')}")
        identity = final_profile.get("identity", {})
        lines.append(f"- identity: {json.dumps(identity, ensure_ascii=False)}")
        appearance = final_profile.get("physical_appearance", {})
        lines.append(f"- appearance: {json.dumps(appearance, ensure_ascii=False)}")
        styling = final_profile.get("styling", {})
        lines.append(f"- styling: {json.dumps(styling, ensure_ascii=False)}")
        consistency = final_profile.get("consistency_profile", {})
        lines.append(f"- consistency: {json.dumps(consistency, ensure_ascii=False)}")
        lines.append("")

        outputs = card.get("generation_outputs", {})
        lines.append("## 输出 Prompts")
        for key in [
            "close_up_prompt",
            "medium_shot_prompt",
            "full_body_prompt",
            "three_view_prompt",
            "expression_sheet_prompt",
            "reference_composite_prompt",
        ]:
            if outputs.get(key):
                lines.append(f"### {key}")
                lines.append("```")
                lines.append(outputs[key])
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def save_json(self, card: Dict[str, Any], output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        return str(path)

    def save_markdown(self, card: Dict[str, Any], output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown(card))
        return str(path)

    def _deep_merge(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        merged = copy.deepcopy(base)
        for key, value in incoming.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

#!/usr/bin/env python3
"""
Prompt generator for virtual-character-builder skill.
将角色设定卡转换为 Wan2.7 可用 prompt bundle。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from character_card import CharacterCardBuilder


class PromptGenerator:
    """根据角色设定卡生成 prompt bundle。"""

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Phase E1 多样化候选方案 prompt 变体
    # ------------------------------------------------------------------

    # 3 组差异化面部特征方向，用于生成视觉上明显不同的候选方案
    FACE_VARIANTS: List[Dict[str, str]] = [
        {
            "label": "A — 柔和圆润型",
            "face_shape": "round soft face, gentle features",
            "eye_style": "large round eyes, warm gaze",
            "feature_emphasis": "soft jawline, full cheeks, youthful innocent look",
            "lighting_mood": "soft diffused lighting, warm tone",
        },
        {
            "label": "B — 立体高冷型",
            "face_shape": "oval sculpted face, high cheekbones",
            "eye_style": "narrow almond eyes, sharp confident gaze",
            "feature_emphasis": "defined jawline, angular features, cool elegant look",
            "lighting_mood": "directional studio lighting, cool tone",
        },
        {
            "label": "C — 自然清透型",
            "face_shape": "heart-shaped face, balanced proportions",
            "eye_style": "medium-sized eyes, natural relaxed expression",
            "feature_emphasis": "smooth forehead, tapered chin, fresh approachable look",
            "lighting_mood": "natural daylight feel, neutral tone",
        },
    ]

    # ------------------------------------------------------------------
    # Phase E2.5 发型变体 prompt 变体
    # ------------------------------------------------------------------

    # 3 组差异化发型变体方向，基于用户指定发型进行微调
    HAIR_VARIANTS: List[Dict[str, str]] = [
        {
            "label": "A — 基础发型",
            "description": "保持用户指定的发型基本不变，仅优化质感和细节",
            "hair_adjustment": "same hairstyle as specified, refined texture and details",
            "color_adjustment": "same hair color as specified, natural shine",
        },
        {
            "label": "B — 发型微调",
            "description": "在用户指定发型基础上进行适度调整（如直发变微卷、层次调整等）",
            "hair_adjustment": "slight variation from specified hairstyle, such as gentle waves or layered texture",
            "color_adjustment": "subtle tonal variation from specified hair color, natural-looking highlights",
        },
        {
            "label": "C — 发色微调",
            "description": "保持发型基本不变，调整发色至相近色系（如黑发调深棕、冷调暖调等）",
            "hair_adjustment": "same hairstyle structure as specified, maintained silhouette",
            "color_adjustment": "close color variation from specified hair color, harmonious tone adjustment",
        },
    ]

    def generate_portrait_prompt_variants(
        self, card: Dict[str, Any], n: int = 3
    ) -> List[str]:
        """生成 n 个差异化的面部特写 prompt，用于 Phase E1 候选方案。

        优先使用 character_analysis 中的个性化变体，如果没有则使用默认模板。
        每个 prompt 在保留用户指定的核心身份要素（发色、肤色等）的同时，
        通过不同的脸型、五官风格、光线氛围来产生视觉差异。

        Returns:
            包含 n 个不同 prompt 的列表
        """
        # 尝试从 character_analysis 获取个性化变体
        source_summary = card.get("source_summary", {})
        character_analysis = source_summary.get("character_analysis", {})
        recommended_variants = character_analysis.get("recommended_face_variants", {})

        variants: List[Dict[str, str]] = []

        # 如果有个性化变体，使用它们
        if recommended_variants and isinstance(recommended_variants, dict):
            variant_keys = ["variant_a", "variant_b", "variant_c"][:n]
            for key in variant_keys:
                variant_data = recommended_variants.get(key)
                if variant_data and isinstance(variant_data, dict):
                    # 将分析变体转换为与 FACE_VARIANTS 兼容的格式
                    variant_dict = {
                        "label": variant_data.get("label", key),
                        "face_shape": variant_data.get("face_shape_adjustment", ""),
                        "eye_style": variant_data.get("eye_style_adjustment", ""),
                        "feature_emphasis": variant_data.get("feature_emphasis", ""),
                        "lighting_mood": variant_data.get("lighting_mood", "")
                    }
                    # 过滤空值
                    variant_dict = {k: v for k, v in variant_dict.items() if v}
                    variants.append(variant_dict)

        # 如果没有足够的个性化变体，用默认模板补全
        if len(variants) < n:
            needed = n - len(variants)
            default_variants = self.FACE_VARIANTS[:needed]
            variants.extend(default_variants)

        prompts: List[str] = []
        for variant in variants:
            prompts.append(self._build_portrait_prompt(card, variant))

        return prompts

    def generate_hair_variants_prompts(self, card: Dict[str, Any], n: int = 3) -> List[str]:
        """生成 n 个差异化的发型变体 prompt，用于 Phase E2.5 候选方案。

        基于用户指定的发型信息（character_analysis.hair_analysis 和 final_profile.physical_appearance.hair）
        生成3个微调变体，即使已经指定了发型也要提供微调选项。

        Returns:
            包含 n 个不同发型变体 prompt 的列表
        """
        # 获取用户指定的发型信息
        source_summary = card.get("source_summary", {})
        character_analysis = source_summary.get("character_analysis", {})
        hair_analysis = character_analysis.get("hair_analysis", {})

        final_profile = card.get("final_profile", {})
        appearance = final_profile.get("physical_appearance", {})
        specified_hair = appearance.get("hair", {})

        # 提取基础发型信息
        base_hair_style = hair_analysis.get("hair_style") or specified_hair.get("style") or "long hair"
        base_hair_color = hair_analysis.get("hair_color") or specified_hair.get("color") or "black hair"
        base_hair_texture = hair_analysis.get("hair_texture") or specified_hair.get("texture") or "straight"

        # 使用默认发型变体模板
        variants = self.HAIR_VARIANTS[:n]
        prompts: List[str] = []

        for variant in variants:
            # 构建发型变体 prompt
            parts = ["close-up portrait, front view, face centered"]

            # 保留面部特征（从character_analysis中获取）
            face_core = character_analysis.get("face_core", {})
            if face_core:
                if face_core.get("face_shape"):
                    parts.append(face_core["face_shape"])
                if face_core.get("facial_features"):
                    parts.append(face_core["facial_features"])

            # 添加基础发型信息
            parts.append(base_hair_style)
            parts.append(base_hair_color)
            parts.append(base_hair_texture)

            # 添加变体调整
            hair_adj = variant.get("hair_adjustment", "")
            if hair_adj:
                parts.append(hair_adj)

            color_adj = variant.get("color_adjustment", "")
            if color_adj:
                parts.append(color_adj)

            # 通用设置
            parts.extend([
                "white background",
                "character identity reference",
                "high detail, sharp focus on facial features and hair",
                "same facial features as reference portrait, only hair variation",
            ])

            prompts.append(self._join_parts(self._dedupe_parts(parts)))

        return prompts

    def _build_portrait_prompt(
        self, card: Dict[str, Any], variant: Optional[Dict[str, str]] = None
    ) -> str:
        """构建单个面部特写 prompt，可选注入差异化变体特征。"""
        final_profile = card.get("final_profile", {})
        identity = final_profile.get("identity", {})
        appearance = final_profile.get("physical_appearance", {})
        consistency = final_profile.get("consistency_profile", {})

        parts: List[str] = ["close-up portrait, front view, face centered"]

        # 注入变体差异化特征（如有）
        if variant:
            for field in ["face_shape", "eye_style", "feature_emphasis"]:
                value = variant.get(field)
                if value and str(value).strip():
                    parts.append(str(value).strip())

        # 身份信息
        for key in ["apparent_age", "gender_expression", "ethnicity_or_reference"]:
            value = identity.get(key)
            if value:
                parts.append(str(value))

        # 如果没有变体，才使用设定卡中的面部特征（避免与变体冲突）
        if not variant:
            face = appearance.get("face", {})
            for key in ["shape", "features", "eye_shape", "eye_color"]:
                value = face.get(key)
                if isinstance(value, list):
                    parts.extend([str(v) for v in value if v])
                elif value:
                    parts.append(str(value))

        # 发型（核心身份要素 — 用户指定，所有变体共享）
        hair = appearance.get("hair", {})
        for key in ["color", "style", "length", "texture"]:
            value = hair.get(key)
            if value:
                parts.append(str(value))

        # 肤色
        skin = appearance.get("skin", {})
        for key in ["tone", "texture"]:
            value = skin.get(key)
            if value:
                parts.append(str(value))

        # 妆容
        makeup = final_profile.get("styling", {}).get("makeup", {})
        for value in makeup.values():
            if value:
                parts.append(str(value))

        # must_keep 中与面部相关的项
        must_keep = consistency.get("must_keep", [])
        for item in must_keep:
            item_lower = str(item).lower()
            if any(kw in item_lower for kw in ["hair", "face", "eye", "skin", "发", "脸", "眼"]):
                parts.append(str(item))

        # 光线氛围（变体差异化）
        if variant:
            lighting_mood = variant.get("lighting_mood")
            if lighting_mood and str(lighting_mood).strip():
                parts.append(str(lighting_mood).strip())
            else:
                parts.append("studio lighting")
            parts.extend([
                "white background",
                "character identity reference",
                "high detail, sharp focus on facial features",
            ])
        else:
            parts.extend([
                "white background",
                "studio lighting",
                "character identity reference",
                "high detail, sharp focus on facial features",
            ])

        return self._join_parts(self._dedupe_parts(parts))

    def generate_portrait_prompt(self, card: Dict[str, Any]) -> str:
        """生成 Phase 1 专用的面部特写 prompt。

        与 bundle 中的 close_up_prompt 不同：
        - 纯文生图，不包含服装/配饰描述（专注于面部身份确立）
        - 强调面部特征、发型、肤色等核心身份要素
        - 用于生成多个候选方案供用户选择"锚点人脸"
        """
        final_profile = card.get("final_profile", {})
        identity = final_profile.get("identity", {})
        appearance = final_profile.get("physical_appearance", {})
        consistency = final_profile.get("consistency_profile", {})

        parts: List[str] = ["close-up portrait, front view, face centered"]

        # 身份信息
        for key in ["apparent_age", "gender_expression", "ethnicity_or_reference"]:
            value = identity.get(key)
            if value:
                parts.append(str(value))

        # 面部特征
        face = appearance.get("face", {})
        for key in ["shape", "features", "eye_shape", "eye_color"]:
            value = face.get(key)
            if isinstance(value, list):
                parts.extend([str(v) for v in value if v])
            elif value:
                parts.append(str(value))

        # 发型（核心身份要素）
        hair = appearance.get("hair", {})
        for key in ["color", "style", "length", "texture"]:
            value = hair.get(key)
            if value:
                parts.append(str(value))

        # 肤色
        skin = appearance.get("skin", {})
        for key in ["tone", "texture"]:
            value = skin.get(key)
            if value:
                parts.append(str(value))

        # 妆容（影响面部观感）
        makeup = final_profile.get("styling", {}).get("makeup", {})
        for value in makeup.values():
            if value:
                parts.append(str(value))

        # must_keep 中与面部相关的项
        must_keep = consistency.get("must_keep", [])
        for item in must_keep:
            item_lower = str(item).lower()
            if any(kw in item_lower for kw in ["hair", "face", "eye", "skin", "发", "脸", "眼"]):
                parts.append(str(item))

        parts.extend([
            "white background",
            "studio lighting",
            "character identity reference",
            "high detail, sharp focus on facial features",
        ])

        return self._join_parts(self._dedupe_parts(parts))

    def _dedupe_parts(self, parts: List[str]) -> List[str]:
        """去重但保持顺序。"""
        result: List[str] = []
        seen = set()
        for part in parts:
            normalized = part.strip().lower()
            if part and normalized not in seen:
                result.append(part.strip())
                seen.add(normalized)
        return result

    def generate_bundle(self, card: Dict[str, Any]) -> Dict[str, str]:
        final_profile = card.get("final_profile", {})
        seed_core = final_profile.get("consistency_profile", {}).get("seed_prompt_core", "")
        if not seed_core:
            seed_core = CharacterCardBuilder.build_seed_core(final_profile)

        scenario_type = final_profile.get("scenario_type", card.get("scenario_guess", {}).get("value", ""))
        mode = card.get("mode", {}).get("selected", "fast")

        appearance = self._compose_appearance(final_profile)
        styling = self._compose_styling(final_profile)
        consistency = self._compose_consistency(final_profile, mode)
        scene_flavor = self._scenario_flavor(scenario_type)

        bundle = {
            "close_up_prompt": self._join_parts([
                "close-up portrait, front view, face centered",
                seed_core,
                appearance,
                styling.get("head_and_upper", ""),
                "white background, character reference sheet, studio lighting",
                scene_flavor,
                consistency,
                "high detail"
            ]),
            "medium_shot_prompt": self._join_parts([
                "medium shot, waist up, front view, framing from waist to head, upper body and face clearly visible, balanced body proportion, natural posture",
                seed_core,
                appearance,
                styling.get("medium_body", ""),
                "white background, character reference sheet, studio lighting",
                scene_flavor,
                consistency,
                "high detail"
            ]),
            "full_body_prompt": self._join_parts([
                "full body, front view, standing pose",
                seed_core,
                appearance,
                styling.get("full_body", ""),
                "white background, character reference sheet, shoes visible, full outfit visible, studio lighting",
                scene_flavor,
                consistency,
                "high detail"
            ]),
            "three_view_prompt": self._join_parts([
                "character reference sheet, full body, white background, studio lighting",
                seed_core,
                appearance,
                styling.get("full_body", ""),
                "First image: front view. Second image: right side view. Third image: back view.",
                "Keep the same hairstyle, outfit silhouette, body proportion, and identity across all three images.",
                consistency,
                scene_flavor,
                "high detail"
            ]),
            "expression_sheet_prompt": self._join_parts([
                "close-up portrait, white background, character expression sheet, studio lighting",
                seed_core,
                appearance,
                styling.get("head_and_upper", ""),
                "First image: neutral calm expression. Second image: gentle smile. Third image: sadness. Fourth image: anger. Fifth image: surprise. Sixth image: determined intense expression.",
                "Keep the same hairstyle, makeup, face identity, and core design across all images.",
                consistency,
                scene_flavor,
                "high detail"
            ]),
            # reference_composite_prompt 使用专门的方法生成，包含场景分析
            "reference_composite_prompt": self._build_reference_composite_prompt(card, appearance, styling)
        }

        if "剧情" not in scenario_type and "影视" not in scenario_type and "cinematic" not in scenario_type.lower():
            bundle["expression_sheet_prompt"] = ""

        if not card.get("source_summary", {}).get("reference_assets"):
            bundle["reference_composite_prompt"] = ""

        return bundle

    def _build_reference_composite_prompt(
        self,
        card: Dict[str, Any],
        appearance: str,
        styling: Dict[str, str],
    ) -> str:
        """构建 reference_composite prompt，融合场景分析和服装气质分析。

        关键改进：
        1. 一致性指令放在最前面（确保人物一致性）
        2. 场景信息只用 prompt 描述，不传场景图（避免锁定原图构图）
        3. 根据服装气质分析生成匹配的姿势和表情
        4. 聚焦产品展示，使用中景构图
        """
        source_summary = card.get("source_summary", {})
        scene_analysis = source_summary.get("scene_analysis", {})
        garment_analysis = source_summary.get("garment_analysis", {})

        parts: List[str] = []

        # 1. 一致性指令放在最前面（最高优先级）
        parts.extend([
            "CRITICAL: This must be the exact same person as shown in the first reference image",
            "Preserve the exact facial features, face shape, eye shape, nose, lips from the portrait reference",
            "same character, same identity, same face as reference portrait",
        ])

        # 2. 基础人物信息
        parts.append(appearance)

        # 3. 服装描述
        parts.append(styling.get("reference_driven", styling.get("full_body", "")))
        garment_refs = [r for r in source_summary.get("reference_assets", []) if r.get("type") == "garment"]
        if garment_refs:
            parts.append("wearing the exact garment from the reference image")

        # 4. 姿势和表情（根据服装气质分析）
        recommended_pose = garment_analysis.get("recommended_pose", {})
        recommended_expression = garment_analysis.get("recommended_expression", {})

        pose_parts = []
        if recommended_pose.get("body_stance"):
            pose_parts.append(recommended_pose["body_stance"])
        if recommended_pose.get("hand_placement"):
            pose_parts.append(recommended_pose["hand_placement"])
        if recommended_pose.get("body_angle"):
            pose_parts.append(recommended_pose["body_angle"])
        if recommended_pose.get("weight_distribution"):
            pose_parts.append(recommended_pose["weight_distribution"])
        if pose_parts:
            parts.append("pose: " + ", ".join(pose_parts))

        expression_parts = []
        if recommended_expression.get("overall_mood"):
            expression_parts.append(recommended_expression["overall_mood"])
        if recommended_expression.get("eye_direction"):
            expression_parts.append(recommended_expression["eye_direction"])
        if recommended_expression.get("mouth_expression"):
            expression_parts.append(recommended_expression["mouth_expression"])
        if recommended_expression.get("chin_position"):
            expression_parts.append(recommended_expression["chin_position"])
        if expression_parts:
            parts.append("expression: " + ", ".join(expression_parts))

        # 5. 构图（聚焦产品展示）
        recommended_camera = scene_analysis.get("recommended_camera", {})
        shot_type = recommended_camera.get("shot_type", "medium shot, three-quarter body framing")
        parts.append(shot_type)
        parts.append("the garment is the visual focus occupying main frame area")
        parts.append("garment details clearly visible")

        # 6. 场景环境描述（只用文字，不传场景图）
        environment = scene_analysis.get("environment", "")
        if environment:
            parts.append(f"scene: {environment}")

        # 7. 光照和色调
        lighting = scene_analysis.get("lighting", {})
        lighting_desc = []
        if lighting.get("type"):
            lighting_desc.append(lighting["type"])
        if lighting.get("quality"):
            lighting_desc.append(lighting["quality"])
        if lighting.get("color_temperature"):
            lighting_desc.append(f"{lighting['color_temperature']} color temperature")
        if lighting_desc:
            parts.append("lighting: " + ", ".join(lighting_desc))

        color_tone = scene_analysis.get("color_tone", {})
        tone_desc = []
        dominant_colors = color_tone.get("dominant_colors", [])
        if dominant_colors:
            tone_desc.append(f"{', '.join(dominant_colors)} tones")
        if color_tone.get("mood"):
            tone_desc.append(f"{color_tone['mood']} mood")
        if color_tone.get("contrast"):
            tone_desc.append(f"{color_tone['contrast']} contrast")
        if tone_desc:
            parts.append("color grading: " + ", ".join(tone_desc))

        # 8. 融合指令
        parts.extend([
            "character naturally blended into scene lighting",
            "soft realistic shadows",
            "seamless composition",
        ])

        # 9. 风格收尾
        style_essence = garment_analysis.get("style_essence", "")
        if style_essence:
            parts.append(f"{style_essence} aesthetic")
        parts.extend([
            "editorial fashion photography",
            "high detail, professional quality"
        ])

        return self._join_parts(self._dedupe_parts(parts))

    def _compose_appearance(self, final_profile: Dict[str, Any]) -> str:
        identity = final_profile.get("identity", {})
        appearance = final_profile.get("physical_appearance", {})

        parts: List[str] = []
        for key in ["apparent_age", "gender_expression", "ethnicity_or_reference", "role_or_background"]:
            value = identity.get(key)
            if value:
                parts.append(str(value))

        for section_name in ["body", "face", "hair", "skin", "hands"]:
            section = appearance.get(section_name, {})
            if isinstance(section, dict):
                for value in section.values():
                    if isinstance(value, list):
                        parts.extend([str(v) for v in value if v])
                    elif value:
                        parts.append(str(value))

        return self._dedupe_join(parts)

    def _compose_styling(self, final_profile: Dict[str, Any]) -> Dict[str, str]:
        styling = final_profile.get("styling", {})
        outfit = styling.get("outfit_core", {})
        makeup = styling.get("makeup", {})
        accessories = styling.get("accessories", {})
        palette = styling.get("palette", {})

        outfit_parts = self._flatten_values(outfit)
        makeup_parts = self._flatten_values(makeup)
        accessory_parts = self._flatten_values(accessories)
        palette_parts = self._flatten_values(palette)
        fit_to_refs = styling.get("fit_to_refs", [])

        all_parts = self._dedupe_join(outfit_parts + makeup_parts + accessory_parts + palette_parts)
        head_upper = self._dedupe_join(makeup_parts + accessory_parts + palette_parts)
        upper_body = self._dedupe_join(outfit_parts + makeup_parts + accessory_parts + palette_parts)
        reference_driven = self._dedupe_join(outfit_parts + accessory_parts + palette_parts + [str(x) for x in fit_to_refs])

        return {
            "head_and_upper": head_upper,
            "upper_body": upper_body,
            "medium_body": all_parts,
            "full_body": all_parts,
            "reference_driven": reference_driven,
        }

    def _compose_consistency(self, final_profile: Dict[str, Any], mode: str) -> str:
        consistency = final_profile.get("consistency_profile", {})
        must_keep = consistency.get("must_keep", [])
        variation_rules = consistency.get("variation_rules", [])

        parts: List[str] = ["consistent character", "same identity"]
        parts.extend([str(v) for v in must_keep if v])

        if mode == "fast":
            parts.append("stable silhouette")
        else:  # pro mode
            parts.append("strict continuity-safe design")

        parts.extend([str(v) for v in variation_rules if v])
        return self._dedupe_join(parts)

    def _scenario_flavor(self, scenario_type: str) -> str:
        scenario = (scenario_type or "").lower()
        if "mv" in scenario or "偶像" in scenario or "音乐" in scenario:
            return "stage-ready, iconic styling, performance energy"
        if "商业" in scenario or "模特" in scenario or "commercial" in scenario:
            return "commercial campaign, editorial fashion"
        if "剧情" in scenario or "影视" in scenario or "cinematic" in scenario:
            return "cinematic character reference, believable narrative character, emotional realism"
        return "premium visual design"

    def _reference_sentence(self, card: Dict[str, Any]) -> str:
        refs = card.get("source_summary", {}).get("reference_assets", [])
        if not refs:
            return ""

        lines = []
        for idx, ref in enumerate(refs, start=1):
            ref_type = ref.get("type", "reference") if isinstance(ref, dict) else "reference"
            label = ref.get("label", f"reference image {idx}") if isinstance(ref, dict) else f"reference image {idx}"
            lines.append(f"Use {label} as {ref_type} guidance")
        return "; ".join(lines)

    def _flatten_values(self, data: Dict[str, Any]) -> List[str]:
        parts: List[str] = []
        for value in data.values():
            if isinstance(value, list):
                parts.extend([str(v) for v in value if v])
            elif isinstance(value, dict):
                parts.extend(self._flatten_values(value))
            elif value:
                parts.append(str(value))
        return parts

    def _join_parts(self, parts: List[str]) -> str:
        return ", ".join([p.strip() for p in parts if p and str(p).strip()])

    def _dedupe_join(self, parts: List[str]) -> str:
        result: List[str] = []
        seen = set()
        for part in parts:
            normalized = part.strip().lower()
            if part and normalized not in seen:
                result.append(part.strip())
                seen.add(normalized)
        return ", ".join(result)

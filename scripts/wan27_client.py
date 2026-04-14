#!/usr/bin/env python3
"""
Wan2.7 API client for virtual-character-builder skill.
封装 DashScope Wan2.7 图像生成接口。
"""

from __future__ import annotations

import base64
import os
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Wan27Client:
    """Wan2.7 (万相2.7) 图像生成客户端。"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    MODEL = "wan2.7-image-pro"

    def __init__(self, api_key: Optional[str] = None, output_dir: str = "output"):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-DataInspection": "enable",
        }

    def _call(
        self,
        messages: List[Dict[str, Any]],
        n: int = 1,
        size: str = "1K",
        enable_sequential: bool = False,
        thinking: bool = True,
        timeout: int = 300,
    ) -> Tuple[bool, Dict[str, Any]]:
        url = f"{self.BASE_URL}/services/aigc/multimodal-generation/generation"
        payload: Dict[str, Any] = {
            "model": self.MODEL,
            "input": {"messages": messages},
            "parameters": {"size": size, "n": n, "watermark": False},
        }
        if enable_sequential:
            payload["parameters"]["enable_sequential"] = True
        if thinking:
            payload["parameters"]["thinking_mode"] = True

        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=timeout)
            data = resp.json()
            if resp.status_code == 200 and "output" in data:
                return True, data
            return False, data
        except Exception as e:
            return False, {"error": str(e)}

    @staticmethod
    def extract_image_urls(data: Dict[str, Any]) -> List[str]:
        """从 Wan2.7 返回中提取图片 URL。
        格式: output.choices[].message.content[].image
        """
        urls: List[str] = []
        for choice in data.get("output", {}).get("choices", []):
            for item in choice.get("message", {}).get("content", []):
                if item.get("type") == "image" and item.get("image"):
                    urls.append(item["image"])
        return urls

    def download_images(self, urls: List[str], prefix: str = "img") -> List[str]:
        """下载图片列表，返回本地路径。"""
        paths: List[str] = []
        for i, url in enumerate(urls):
            save_path = self.output_dir / f"{prefix}_{i+1}.png"
            try:
                resp = requests.get(url, timeout=120)
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    paths.append(str(save_path))
            except Exception:
                pass
        return paths

    # ------------------------------------------------------------------
    # 本地图片 → API 可用格式
    # ------------------------------------------------------------------

    @staticmethod
    def local_image_to_data_uri(path: str) -> str:
        """将本地图片文件转为 base64 data URI，可直接用于 API image 字段。"""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        ext = file_path.suffix.lower().lstrip(".")
        mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}
        mime = mime_map.get(ext, "png")
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{mime};base64,{data}"

    @classmethod
    def prepare_image_inputs(cls, image_sources: List[str]) -> List[str]:
        """将混合的图片来源（本地路径 / URL / data URI）统一转为 API 可用格式。

        - 以 http:// 或 https:// 开头 → 直接使用
        - 以 data: 开头 → 直接使用（已是 data URI）
        - 其他 → 视为本地路径，转 base64 data URI
        """
        result: List[str] = []
        for src in image_sources:
            if src.startswith("http://") or src.startswith("https://"):
                result.append(src)
            elif src.startswith("data:"):
                result.append(src)
            else:
                result.append(cls.local_image_to_data_uri(src))
        return result

    def _build_content_with_refs(
        self, prompt: str, reference_images: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """构建含参考图的 content 数组。参考图在前，文字 prompt 在后。"""
        content: List[Dict[str, str]] = []
        if reference_images:
            prepared = self.prepare_image_inputs(reference_images)
            for img in prepared:
                content.append({"image": img})
        content.append({"text": prompt})
        return content

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def generate_single_image(
        self,
        prompt: str,
        size: str = "1K",
        prefix: str = "single",
        reference_images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """文生图 / 图生图：单张图片。

        reference_images: 可选参考图列表（本地路径 / URL / data URI 均可）。
        传入后会自动转为 API 可用格式，作为 image-to-image 输入。
        """
        content = self._build_content_with_refs(prompt, reference_images)
        messages = [{"role": "user", "content": content}]
        ok, data = self._call(messages, n=1, size=size)
        result: Dict[str, Any] = {"success": ok, "raw": data, "urls": [], "local_paths": []}
        if ok:
            result["urls"] = self.extract_image_urls(data)
            result["local_paths"] = self.download_images(result["urls"], prefix=prefix)
        return result

    def generate_sequential_images(
        self,
        prompt: str,
        n: int = 3,
        size: str = "1K",
        prefix: str = "seq",
        reference_images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """组图模式：三视图 / 表情组等。支持可选参考图输入。"""
        content = self._build_content_with_refs(prompt, reference_images)
        messages = [{"role": "user", "content": content}]
        ok, data = self._call(messages, n=n, size=size, enable_sequential=True)
        result: Dict[str, Any] = {"success": ok, "raw": data, "urls": [], "local_paths": []}
        if ok:
            result["urls"] = self.extract_image_urls(data)
            result["local_paths"] = self.download_images(result["urls"], prefix=prefix)
        return result

    # ------------------------------------------------------------------
    # 两阶段角色一致性生成流程
    # ------------------------------------------------------------------

    def generate_portrait_options(
        self,
        prompt: Any = None,
        n: int = 3,
        size: str = "1K",
        prefix: str = "portrait_option",
        prompts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Phase 1：文生图 — 生成多个差异化面部特写候选方案。

        用于角色一致性流程的第一步：
        1. 纯文生图，不带服装参考（专注于面部/身份确立）
        2. 生成多个候选，让用户选择一个作为"锚点人脸"
        3. 选定的锚点图将用于后续所有景别的图生图

        关键改进：每个候选使用不同的 prompt 独立调用 API，
        确保候选方案之间有明显的视觉差异（不同脸型、五官、气质）。

        Args:
            prompt: 单个 prompt（向后兼容，会对所有候选使用同一 prompt）
            n: 候选数量（仅在 prompts 未提供时使用）
            size: 输出尺寸
            prefix: 文件名前缀
            prompts: 差异化 prompt 列表（推荐）。每个 prompt 对应一个候选方案。

        Returns:
            结果字典，包含所有候选图的 URL 和本地路径。
        """
        # 优先使用差异化 prompt 列表
        if prompts:
            prompt_list = prompts
        elif prompt:
            prompt_list = [prompt] * n
        else:
            raise ValueError("Must provide either 'prompt' or 'prompts'")

        all_urls: List[str] = []
        all_paths: List[str] = []
        all_raw: List[Dict[str, Any]] = []
        overall_success = True

        for i, p in enumerate(prompt_list):
            content = [{"text": p}]
            messages = [{"role": "user", "content": content}]
            ok, data = self._call(messages, n=1, size=size)
            all_raw.append(data)

            if ok:
                urls = self.extract_image_urls(data)
                all_urls.extend(urls)
                paths = self.download_images(urls, prefix=f"{prefix}_{i+1}")
                all_paths.extend(paths)
            else:
                overall_success = False

        return {
            "success": overall_success and len(all_urls) > 0,
            "raw": all_raw,
            "urls": all_urls,
            "local_paths": all_paths,
        }

    def select_anchor_portrait(self, portrait_path: str) -> str:
        """Phase 1.5：用户选定锚点人脸。

        将选定的特写图转为 data URI 格式，供后续图生图使用。

        Args:
            portrait_path: 选定的特写图文件路径（本地路径 / URL / data URI）

        Returns:
            可直接用于 API 的图片格式（data URI 或 URL）
        """
        prepared = self.prepare_image_inputs([portrait_path])
        return prepared[0]

    def generate_with_anchor(
        self,
        prompt: str,
        anchor_portrait: str,
        garment_refs: Optional[List[str]] = None,
        size: str = "1K",
        prefix: str = "anchored",
        enable_sequential: bool = False,
        n: int = 1,
    ) -> Dict[str, Any]:
        """Phase 2：以锚点人脸 + 可选服装参考图进行图生图。

        用于角色一致性流程的第二步：
        1. 锚点人脸放在 content 最前面（确保人物一致性）
        2. 服装参考图紧随其后（确保服装匹配）
        3. 文字 prompt 放在最后

        Args:
            prompt: 生成 prompt
            anchor_portrait: 锚点人脸（data URI / URL，由 select_anchor_portrait 返回）
            garment_refs: 可选服装参考图列表（已经过 prepare_image_inputs 处理）
            size: 输出尺寸
            prefix: 保存文件名前缀
            enable_sequential: 是否启用组图模式（三视图等）
            n: 生成数量

        Returns:
            生成结果字典
        """
        # 构建 content：锚点人脸 > 服装参考 > 文字 prompt
        content: List[Dict[str, str]] = []

        # 锚点人脸（最高优先级 — 角色一致性）
        content.append({"image": anchor_portrait})

        # 服装参考图（如有）
        if garment_refs:
            for ref in garment_refs:
                content.append({"image": ref})

        # 文字 prompt
        content.append({"text": prompt})

        messages = [{"role": "user", "content": content}]
        ok, data = self._call(messages, n=n, size=size, enable_sequential=enable_sequential)
        result: Dict[str, Any] = {"success": ok, "raw": data, "urls": [], "local_paths": []}
        if ok:
            result["urls"] = self.extract_image_urls(data)
            result["local_paths"] = self.download_images(result["urls"], prefix=prefix)
        return result

    def generate_consistent_bundle(
        self,
        prompt_bundle: Dict[str, str],
        anchor_portrait: str,
        garment_refs: Optional[List[str]] = None,
        size: str = "1K",
        garment_ref_keys: Optional[set] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Phase 2 批量版：用锚点人脸 + 服装参考图生成整个 prompt bundle。

        与 generate_bundle() 的关键区别：
        - 每个景别都以锚点人脸作为图生图输入，保证角色一致性
        - close_up_prompt 跳过（已在 Phase 1 中由用户选定）

        Args:
            prompt_bundle: prompt 字典（key → prompt text）
            anchor_portrait: 用户选定的锚点人脸（data URI / URL）
            garment_refs: 服装参考图列表（已转为 data URI / URL）
            size: 输出尺寸
            garment_ref_keys: 需要带服装参考图的 prompt key 集合
        """
        if garment_ref_keys is None:
            garment_ref_keys = {
                "medium_shot_prompt",
                "full_body_prompt",
                "three_view_prompt",
                "reference_composite_prompt",
            }

        results: Dict[str, Dict[str, Any]] = {}
        sequential_keys = {"three_view_prompt", "expression_sheet_prompt"}

        # 定义生成顺序（跳过 close_up，因为它已由 Phase 1 确定）
        ordered_keys = [
            "medium_shot_prompt",
            "full_body_prompt",
            "three_view_prompt",
            "expression_sheet_prompt",
            "reference_composite_prompt",
        ]

        for key in ordered_keys:
            prompt = prompt_bundle.get(key, "")
            if not prompt:
                continue

            prefix = key.replace("_prompt", "")
            refs = garment_refs if (garment_refs and key in garment_ref_keys) else None
            enable_seq = key in sequential_keys
            n = 1
            if key == "three_view_prompt":
                n = 3
            elif key == "expression_sheet_prompt":
                n = 6

            results[key] = self.generate_with_anchor(
                prompt=prompt,
                anchor_portrait=anchor_portrait,
                garment_refs=refs,
                size=size,
                prefix=prefix,
                enable_sequential=enable_seq,
                n=n,
            )

        return results

    # ------------------------------------------------------------------
    # 旧接口（向后兼容，但推荐使用两阶段流程）
    # ------------------------------------------------------------------

    def generate_with_references(
        self,
        prompt: str,
        reference_image_urls: List[str],
        size: str = "1K",
        prefix: str = "ref",
    ) -> Dict[str, Any]:
        """参考图驱动生成（兼容旧接口）。

        reference_image_urls 支持本地路径 / URL / data URI。
        """
        return self.generate_single_image(
            prompt, size=size, prefix=prefix, reference_images=reference_image_urls
        )

    def generate_bundle(
        self,
        prompt_bundle: Dict[str, str],
        size: str = "1K",
        reference_images: Optional[List[str]] = None,
        garment_ref_keys: Optional[set] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """批量生成整个 prompt bundle 中的所有图片（旧接口，不保证角色一致性）。

        推荐使用 generate_consistent_bundle() 代替。

        reference_images: 参考图列表（本地路径 / URL / data URI）。
        garment_ref_keys: 需要带参考图的 prompt key 集合。
        """
        if garment_ref_keys is None:
            garment_ref_keys = {
                "close_up_prompt",
                "medium_shot_prompt",
                "full_body_prompt",
                "three_view_prompt",
                "reference_composite_prompt",
            }

        results: Dict[str, Dict[str, Any]] = {}
        sequential_keys = {"three_view_prompt", "expression_sheet_prompt"}

        for key, prompt in prompt_bundle.items():
            if not prompt:
                continue

            refs = reference_images if (reference_images and key in garment_ref_keys) else None
            prefix = key.replace("_prompt", "")

            if key in sequential_keys:
                n = 3 if key == "three_view_prompt" else 6
                results[key] = self.generate_sequential_images(
                    prompt, n=n, size=size, prefix=prefix, reference_images=refs
                )
            else:
                results[key] = self.generate_single_image(
                    prompt, size=size, prefix=prefix, reference_images=refs
                )

        return results

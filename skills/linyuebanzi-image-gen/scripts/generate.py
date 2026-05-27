#!/usr/bin/env python3
"""
通用图像生成器
调用 MuleRun / APImart / Atlas Cloud API,支持 generation(纯文本生图)和 edit(带参考图修图)两种模式。
单张用 CLI 参数,批量用 manifest JSON。

用法:
    # 单张生图
    python generate.py --mode generation --prompt "..." --name-tag diagram-001 --output-dir ./out

    # 单张修图
    python generate.py --mode edit --prompt "..." --images "https://..." --name-tag cover --output-dir ./out

    # 从文件读 prompt
    python generate.py --mode generation --prompt-file ./prompt.txt --output-dir ./out

    # 批量(串行)
    python generate.py --manifest ./batch.json --output-dir ./out

    # 批量(并行)
    python generate.py --manifest ./batch.json --output-dir ./out --parallel

环境变量:
    MULERUN_API_KEY    --provider mulerun 时必填
    APIMART_API_KEY    --provider apimart 时必填
    ATLASCLOUD_API_KEY --provider atlascloud 时必填

Manifest JSON 格式:
    {
      "mode": "generation",
      "aspect_ratio": "16:9",
      "resolution": "2K",
      "items": [
        {"id": "img-001", "prompt": "..."},
        {"id": "img-002", "prompt": "...", "images": ["https://..."]}
      ]
    }

产出:
    单张: {name-tag}-{timestamp}.png / .txt / .json
    批量: {id}.png / {id}.txt / {id}.json + _run_metadata.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

from providers import get_provider, get_provider_class
from providers.base import download_image

# ============================================================
# 默认配置
# ============================================================

DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "2K"
DEFAULT_PROVIDER = "mulerun"

# ============================================================


def validate_item(item: dict) -> Optional[str]:
    missing = [f for f in ("id", "prompt") if f not in item or not item[f]]
    if missing:
        return f"缺少字段: {', '.join(missing)}"
    return None


def load_blocklist(blocklist_path: Optional[str]) -> Optional[list[str]]:
    if not blocklist_path:
        return None
    p = Path(blocklist_path)
    if not p.exists():
        print(f"✗ blocklist 文件不存在: {p}")
        sys.exit(1)
    terms = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not terms:
        return None
    print(f"✓ 加载 blocklist: {p} ({len(terms)} 个词)")
    return terms


def check_blocklist(prompt: str, terms: Optional[list[str]], context: str = "") -> None:
    if not terms:
        return
    hits = [t for t in terms if t in prompt]
    if not hits:
        return
    label = f" [{context}]" if context else ""
    print(f"✗ 提示词{label}命中 blocklist 禁用词,已停止生成")
    print(f"  命中的词: {', '.join(hits)}")
    sys.exit(1)


def process_single_item(
    item: dict, output_dir: Path, provider, mode: str,
    aspect_ratio: str, resolution: str, index: int, total: int,
) -> dict:
    item_id = item["id"]
    images = item.get("images")

    print(f"\n[{index}/{total}] {item_id}")

    task_id = provider.create_task(item["prompt"], mode, images, aspect_ratio, resolution)
    if not task_id:
        return {"id": item_id, "status": "failed", "stage": "create"}
    print(f"    ✓ task_id: {task_id}")

    print(f"    → 轮询中")
    result = provider.poll_task(task_id, mode)
    if not result:
        return {"id": item_id, "status": "failed", "stage": "poll", "task_id": task_id}

    result_images = result.get("images", [])
    if not result_images:
        return {"id": item_id, "status": "failed", "stage": "no_image", "task_id": task_id}

    prompt_path = output_dir / f"{item_id}.txt"
    prompt_path.write_text(item["prompt"], encoding="utf-8")

    image_paths = []
    for idx, image_url in enumerate(result_images):
        suffix = f"-{idx}" if len(result_images) > 1 else ""
        image_path = output_dir / f"{item_id}{suffix}.png"
        print(f"    → 下载图片({idx+1}/{len(result_images)}) → {image_path.name}")
        if not download_image(image_url, image_path):
            return {"id": item_id, "status": "failed", "stage": "download", "task_id": task_id}
        image_paths.append(str(image_path))
        print(f"    ✓ {image_path.stat().st_size // 1024} KB")

    meta_path = output_dir / f"{item_id}.json"
    meta_path.write_text(
        json.dumps({
            "id": item_id,
            "task_id": task_id,
            "mode": mode,
            "image_urls": result_images,
            "local_images": image_paths,
            "params": {"aspect_ratio": aspect_ratio, "resolution": resolution},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "id": item_id, "status": "completed",
        "image_urls": result_images, "local_images": image_paths,
        "task_id": task_id,
    }


def _download_item(iid: str, item: dict, poll_result: Optional[dict],
                   output_dir: Path, task_id: str) -> dict:
    if not poll_result:
        return {"id": iid, "status": "failed", "stage": "poll", "task_id": task_id}

    images = poll_result.get("images", [])
    if not images:
        return {"id": iid, "status": "failed", "stage": "no_image", "task_id": task_id}

    prompt_path = output_dir / f"{iid}.txt"
    prompt_path.write_text(item["prompt"], encoding="utf-8")

    image_paths = []
    for idx, image_url in enumerate(images):
        suffix = f"-{idx}" if len(images) > 1 else ""
        image_path = output_dir / f"{iid}{suffix}.png"
        if not download_image(image_url, image_path):
            return {"id": iid, "status": "failed", "stage": "download", "task_id": task_id}
        image_paths.append(str(image_path))

    return {"id": iid, "status": "completed", "image_urls": images, "local_images": image_paths, "task_id": task_id}


def run_parallel(items: list, output_dir: Path, provider, mode: str,
                 aspect_ratio: str, resolution: str) -> list:
    total = len(items)
    print(f"\n{'='*60}")
    print(f"并行模式 · {total} 项同时跑")
    print(f"{'='*60}")

    task_entries = []
    for idx, item in enumerate(items, 1):
        err = validate_item(item)
        if err:
            print(f"  [{idx}/{total}] ✗ 跳过: {err}")
            task_entries.append((item.get("id", "?"), item, None, "validate"))
            continue

        item_id = item["id"]
        print(f"  [{idx}/{total}] {item_id} → 创建任务")
        task_id = provider.create_task(item["prompt"], mode, item.get("images"), aspect_ratio, resolution)
        if not task_id:
            task_entries.append((item_id, item, None, "create"))
        else:
            print(f"    ✓ task_id={task_id}")
            task_entries.append((item_id, item, task_id, None))

    print(f"\n  并行轮询中...")
    poll_results = {}
    with ThreadPoolExecutor(max_workers=len(task_entries)) as executor:
        futures = {}
        for iid, _, tid, _ in task_entries:
            if tid:
                futures[executor.submit(provider.poll_task, tid, mode)] = iid
        for future in as_completed(futures):
            iid = futures[future]
            try:
                poll_results[iid] = future.result()
            except Exception as e:
                print(f"    ✗ {iid} 轮询异常: {e}")
                poll_results[iid] = None

    print(f"\n  并行下载中...")
    results = []
    with ThreadPoolExecutor(max_workers=len(task_entries)) as executor:
        futures = {}
        for iid, item, tid, failed_stage in task_entries:
            if failed_stage:
                results.append({"id": iid, "status": "failed", "stage": failed_stage})
                continue
            if tid is None:
                continue
            futures[executor.submit(
                _download_item, iid, item, poll_results.get(iid), output_dir, tid,
            )] = iid
        for future in as_completed(futures):
            iid = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"id": iid, "status": "failed", "stage": "exception"})

    return results


def run_single(mode: str, prompt: str, images: Optional[list[str]], name_tag: str,
               output_dir: Path, provider, aspect_ratio: str, resolution: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_stem = f"{name_tag}-{timestamp}"

    print(f"→ 创建{mode}任务")

    task_id = provider.create_task(prompt, mode, images, aspect_ratio, resolution)
    if not task_id:
        print("✗ 创建任务失败")
        sys.exit(1)
    print(f"✓ task_id: {task_id}")

    print(f"→ 轮询中(最多等 {provider.POLL_MAX_TIMES * provider.POLL_INTERVAL}s)")
    result = provider.poll_task(task_id, mode)
    if not result:
        print("✗ 任务失败或超时")
        sys.exit(1)

    result_images = result.get("images", [])
    if not result_images:
        print("✗ API 成功但无图片")
        sys.exit(1)

    prompt_path = output_dir / f"{file_stem}.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    image_paths = []
    for idx, image_url in enumerate(result_images):
        suffix = f"-{idx}" if len(result_images) > 1 else ""
        image_path = output_dir / f"{file_stem}{suffix}.png"
        print(f"→ 下载图片({idx+1}/{len(result_images)}) → {image_path.name}")
        if not download_image(image_url, image_path):
            sys.exit(1)
        image_paths.append(image_path)
        print(f"✓ {image_path.stat().st_size // 1024} KB")

    meta_path = output_dir / f"{file_stem}.json"
    meta_path.write_text(
        json.dumps({
            "task_id": task_id,
            "mode": mode,
            "image_urls": result_images,
            "params": {"aspect_ratio": aspect_ratio, "resolution": resolution},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print(f"✓ 生成完毕,共 {len(result_images)} 张图片")
    for p in image_paths:
        print(f"  📁 {p}")
    print(f"  📝 {prompt_path}")
    print("=" * 60)
    print(f"  不满意可改 .txt 提示词后重跑:")
    print(f"  python {Path(__file__).name} --mode {mode} --prompt-file {prompt_path} --name-tag {name_tag}-v2")


def main():
    # 确保 providers 包可被导入 (脚本直接运行时的路径问题)
    sys.path.insert(0, str(Path(__file__).parent))

    parser = argparse.ArgumentParser(description="通用图像生成器 (MuleRun / APImart / Atlas Cloud)")

    parser.add_argument("--provider", choices=["mulerun", "apimart", "atlascloud"], default=DEFAULT_PROVIDER,
                        help=f"API 提供商(默认 {DEFAULT_PROVIDER})")
    parser.add_argument("--mode", choices=["generation", "edit"], help="生成模式: generation(纯文本生图) 或 edit(带参考图)")
    prompt_src = parser.add_mutually_exclusive_group()
    prompt_src.add_argument("--prompt", type=str, help="提示词文本")
    prompt_src.add_argument("--prompt-file", type=str, help="提示词文件路径")
    prompt_src.add_argument("--manifest", type=str, help="批量 manifest JSON 路径")
    parser.add_argument("--images", type=str, help="参考图 URL,多个用逗号分隔(edit 模式)")
    parser.add_argument("--name-tag", type=str, default="image", help="单张模式文件命名前缀(默认 image)")
    parser.add_argument("--output-dir", type=str, default="./output", help="输出目录(默认 ./output)")
    parser.add_argument("--aspect-ratio", type=str, default=DEFAULT_ASPECT_RATIO, help=f"纵横比(默认 {DEFAULT_ASPECT_RATIO})")
    parser.add_argument("--resolution", type=str, default=DEFAULT_RESOLUTION, help=f"分辨率(默认 {DEFAULT_RESOLUTION})")
    parser.add_argument("--parallel", action="store_true", help="批量模式启用并行执行")
    parser.add_argument("--blocklist", type=str, help="禁用词表文件路径(每行一个词,命中即停止)")
    args = parser.parse_args()

    # Provider 决策: 显式传了就用显式的,否则自动检测
    provider_name = args.provider
    has_mulerun = bool(os.environ.get("MULERUN_API_KEY"))
    has_apimart = bool(os.environ.get("APIMART_API_KEY"))
    has_atlascloud = bool(os.environ.get("ATLASCLOUD_API_KEY"))
    if args.provider == DEFAULT_PROVIDER and not has_mulerun:
        if has_apimart:
            provider_name = "apimart"
            print(f"  自动检测: APIMART_API_KEY 已设置,切换到 apimart")
        elif has_atlascloud:
            provider_name = "atlascloud"
            print(f"  自动检测: ATLASCLOUD_API_KEY 已设置,切换到 atlascloud")

    provider_cls = get_provider_class(provider_name)

    # 加载 blocklist
    blocklist = load_blocklist(args.blocklist)

    # 鉴权
    env_var = provider_cls.env_var
    api_key = os.environ.get(env_var)
    if not api_key:
        print(f"✗ 未找到环境变量 {provider_cls.env_var}")
        print(f"  请先设置: export {provider_cls.env_var}=sk-xxx")
        sys.exit(1)

    provider = get_provider(provider_name, api_key)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 批量模式
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"✗ manifest 不存在: {manifest_path}")
            sys.exit(1)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"✗ manifest JSON 解析失败: {e}")
            sys.exit(1)

        mode = manifest.get("mode", "generation")
        aspect_ratio = manifest.get("aspect_ratio", args.aspect_ratio)
        resolution = manifest.get("resolution", args.resolution)
        items = manifest.get("items", [])

        if not isinstance(items, list) or not items:
            print("✗ manifest.items 必须是非空数组")
            sys.exit(1)

        total = len(items)
        print("=" * 60)
        print(f"批量{mode}模式 · {total} 项 · {'并行' if args.parallel else '串行'} · provider={provider_name}")
        print(f"  参数: aspect_ratio={aspect_ratio}, resolution={resolution}")
        print(f"  输出: {output_dir}")
        print("=" * 60)

        if args.parallel:
            filtered = []
            results = []
            for idx, item in enumerate(items, 1):
                err = validate_item(item)
                if err:
                    print(f"\n[{idx}/{total}] ✗ 跳过: {err}")
                    results.append({"id": item.get("id", "?"), "status": "failed", "stage": "validate"})
                    continue
                try:
                    check_blocklist(item["prompt"], blocklist, context=item.get("id", f"item-{idx}"))
                except SystemExit:
                    results.append({"id": item.get("id", "?"), "status": "failed", "stage": "blocklist"})
                    continue
                filtered.append(item)
            results += run_parallel(filtered, output_dir, provider, mode, aspect_ratio, resolution)
        else:
            results = []
            for idx, item in enumerate(items, 1):
                err = validate_item(item)
                if err:
                    print(f"\n[{idx}/{total}] ✗ 跳过: {err}")
                    results.append({"id": item.get("id", "?"), "status": "failed", "stage": "validate"})
                    continue
                check_blocklist(item["prompt"], blocklist, context=item.get("id", f"item-{idx}"))
                results.append(process_single_item(item, output_dir, provider, mode, aspect_ratio, resolution, idx, total))

        # 写运行元数据
        meta_path = output_dir / "_run_metadata.json"
        meta_path.write_text(
            json.dumps({
                "timestamp": datetime.now().strftime("%Y%m%d-%H%M%S"),
                "provider": provider_name,
                "mode": mode,
                "total": total,
                "results": results,
                "params": {"aspect_ratio": aspect_ratio, "resolution": resolution},
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        success_count = sum(1 for r in results if r["status"] == "completed")
        print()
        print("=" * 60)
        print(f"{'✓' if success_count == total else '⚠'} 完成 {success_count}/{total}")
        print(f"  📁 {output_dir}")
        print(f"  📋 {meta_path}")
        print("=" * 60)
        if success_count < total:
            sys.exit(1)
        return

    # 单张模式
    if not args.mode:
        print("✗ 单张模式必须指定 --mode generation 或 --mode edit")
        sys.exit(1)

    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        p = Path(args.prompt_file)
        if not p.exists():
            print(f"✗ 文件不存在: {p}")
            sys.exit(1)
        prompt = p.read_text(encoding="utf-8")
    else:
        print("✗ 必须指定 --prompt、--prompt-file 或 --manifest")
        sys.exit(1)

    images = None
    if args.images:
        images = [u.strip() for u in args.images.split(",") if u.strip()]

    if args.mode == "edit" and not images:
        print("✗ edit 模式必须通过 --images 提供参考图 URL")
        sys.exit(1)

    check_blocklist(prompt, blocklist)
    run_single(args.mode, prompt, images, args.name_tag, output_dir, provider, args.aspect_ratio, args.resolution)


if __name__ == "__main__":
    main()

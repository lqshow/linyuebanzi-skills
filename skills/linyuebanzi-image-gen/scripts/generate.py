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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================

PROVIDERS = {
    "mulerun": {
        "env_var": "MULERUN_API_KEY",
        "create_url": "https://api.mulerun.com/vendors/google/v1/nano-banana-2",
        "poll_url": "https://api.mulerun.com/vendors/google/v1/nano-banana-2",
    },
    "apimart": {
        "env_var": "APIMART_API_KEY",
        "create_url": "https://api.apimart.ai/v1/images/generations",
        "poll_url": "https://api.apimart.ai/v1/tasks",
    },
    "atlascloud": {
        "env_var": "ATLASCLOUD_API_KEY",
        "create_url": "https://api.atlascloud.ai/api/v1/model/generateImage",
        "poll_url": "https://api.atlascloud.ai/api/v1/model/prediction",
    },
}

DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "2K"
DEFAULT_PROVIDER = "mulerun"

POLL_INTERVAL = 5
POLL_MAX_TIMES = 36  # 3 分钟

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# ============================================================


def http_request(method: str, url: str, headers: dict, data: bytes | None = None) -> dict:
    if "User-Agent" not in headers and "user-agent" not in headers:
        headers = {**headers, "User-Agent": DEFAULT_USER_AGENT}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return {"status": resp.status, "body": json.loads(body) if body else {}}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return {"status": e.code, "body": err_body, "error": str(e)}
    except Exception as e:
        return {"status": 0, "body": "", "error": str(e)}


def _build_create_payload(provider: str, prompt: str, mode: str, images: list[str] | None,
                          aspect_ratio: str, resolution: str) -> tuple[str, dict]:
    """返回 (create_url, payload)"""
    cfg = PROVIDERS[provider]

    if provider == "mulerun":
        path = "edit" if mode == "edit" else "generation"
        create_url = f"{cfg['create_url']}/{path}"
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if mode == "edit" and images:
            payload["images"] = images
        return create_url, payload

    if provider == "apimart":
        payload = {
            "model": "gpt-image-2-official",
            "prompt": prompt,
            "size": aspect_ratio,
            "resolution": resolution.lower(),
            "quality": "high",
            "n": 1,
        }
        if images:
            payload["image_urls"] = images
        return cfg["create_url"], payload

    # atlascloud
    size_map = {
        "16:9": "2560x1440",
        "9:16": "1440x2560",
        "1:1": "1024x1024",
    }
    size = size_map.get(aspect_ratio, "2560x1440")
    model = "openai/gpt-image-2/edit" if mode == "edit" else "openai/gpt-image-2/text-to-image"
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": "high",
    }
    if mode == "edit" and images:
        payload["images"] = images
    return cfg["create_url"], payload


def _parse_task_id(provider: str, resp: dict) -> str | None:
    if provider == "mulerun":
        return resp["body"]["task_info"]["id"]
    if provider == "apimart":
        data = resp["body"].get("data")
        if isinstance(data, list) and data:
            return data[0].get("task_id")
        return None
    # atlascloud: {"data":{"id":"xxx"}}
    data = resp["body"].get("data", {})
    return data.get("id")


def _build_poll_url(provider: str, task_id: str, mode: str = "generation") -> str:
    cfg = PROVIDERS[provider]
    if provider == "mulerun":
        path = "edit" if mode == "edit" else "generation"
        return f"{cfg['poll_url']}/{path}/{task_id}"
    if provider == "apimart":
        return f"{cfg['poll_url']}/{task_id}?language=zh"
    # atlascloud
    return f"{cfg['poll_url']}/{task_id}"


def _parse_poll_status(provider: str, resp: dict) -> tuple[str, dict]:
    """返回 (status, raw_body), status 归一化为 completed/polling/failed"""
    if provider == "mulerun":
        task_info = resp["body"].get("task_info", {})
        status = task_info.get("status", "unknown")
        if status in ("completed", "succeeded"):
            return "completed", resp["body"]
        if status in ("failed", "error"):
            return "failed", resp["body"]
        return "polling", resp["body"]

    if provider == "apimart":
        data = resp["body"].get("data", {})
        status = data.get("status", "unknown")
        if status == "completed":
            return "completed", data
        if status in ("failed", "cancelled"):
            return "failed", data
        return "polling", data

    # atlascloud: resp["data"]["status"] = processing/completed/succeeded/failed
    data = resp["body"].get("data", {})
    status = data.get("status", "unknown")
    if status in ("completed", "succeeded"):
        return "completed", data
    if status in ("failed", "error"):
        return "failed", data
    return "polling", data


def _extract_images(provider: str, poll_body: dict) -> list[str]:
    """从轮询结果中提取图片 URL 列表,归一化为平铺的 URL 数组"""
    if provider == "mulerun":
        return poll_body.get("images", [])

    if provider == "apimart":
        result = poll_body.get("result", {})
        image_items = result.get("images", [])
        urls = []
        for item in image_items:
            item_urls = item.get("url", [])
            urls.extend(item_urls)
        return urls

    # atlascloud: data.outputs[0] is a URL string
    outputs = poll_body.get("outputs", [])
    return [u for u in outputs if isinstance(u, str) and u.startswith("http")]


def create_task(prompt: str, api_key: str, mode: str, images: list[str] | None = None,
                aspect_ratio: str = DEFAULT_ASPECT_RATIO, resolution: str = DEFAULT_RESOLUTION,
                provider: str = DEFAULT_PROVIDER) -> str | None:
    create_url, payload = _build_create_payload(provider, prompt, mode, images, aspect_ratio, resolution)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = http_request("POST", create_url, headers, json.dumps(payload).encode("utf-8"))
    if not (200 <= resp["status"] < 300):
        print(f"    ✗ 创建任务失败,HTTP {resp['status']}")
        print(f"      响应: {resp.get('body')}")
        return None

    return _parse_task_id(provider, resp)


def poll_task(task_id: str, api_key: str, mode: str,
              provider: str = DEFAULT_PROVIDER) -> dict | None:
    url = _build_poll_url(provider, task_id, mode)
    headers = {"Authorization": f"Bearer {api_key}"}

    for i in range(POLL_MAX_TIMES):
        time.sleep(POLL_INTERVAL)
        elapsed = (i + 1) * POLL_INTERVAL
        resp = http_request("GET", url, headers)
        if resp["status"] != 200:
            print(f"    [第 {i+1} 次,已等 {elapsed}s] HTTP {resp['status']},继续等")
            continue

        status, poll_body = _parse_poll_status(provider, resp)

        if status == "completed":
            print(f"    ✓ 完成,耗时约 {elapsed}s")
            return {"images": _extract_images(provider, poll_body)}
        elif status == "failed":
            print(f"    ✗ 任务失败: {json.dumps(poll_body, ensure_ascii=False)}")
            return None
        else:
            print(f"    [第 {i+1} 次,已等 {elapsed}s] 状态: {status}")

    print(f"    ✗ 轮询超时({POLL_MAX_TIMES * POLL_INTERVAL}s)")
    return None


def download_image(url: str, save_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            save_path.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    ✗ 下载失败: {e}")
        print(f"      可手动打开: {url}")
        return False


def validate_item(item: dict) -> str | None:
    missing = [f for f in ("id", "prompt") if f not in item or not item[f]]
    if missing:
        return f"缺少字段: {', '.join(missing)}"
    return None


def load_blocklist(blocklist_path: str | None) -> list[str] | None:
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


def check_blocklist(prompt: str, terms: list[str] | None, context: str = "") -> None:
    if not terms:
        return
    hits = [t for t in terms if t in prompt]
    if not hits:
        return
    label = f" [{context}]" if context else ""
    print(f"✗ 提示词{label}命中 blocklist 禁用词,已停止生成")
    print(f"  命中的词: {', '.join(hits)}")
    sys.exit(1)


def resolve_item_mode(item: dict, manifest_mode: str) -> str:
    if manifest_mode == "mixed":
        return item.get("mode", "generation")
    return manifest_mode


def process_single_item(
    item: dict, output_dir: Path, api_key: str, mode: str,
    aspect_ratio: str, resolution: str, index: int, total: int,
    provider: str = DEFAULT_PROVIDER,
) -> dict:
    item_id = item["id"]
    images = item.get("images")

    print(f"\n[{index}/{total}] {item_id}")

    task_id = create_task(item["prompt"], api_key, mode, images, aspect_ratio, resolution, provider=provider)
    if not task_id:
        return {"id": item_id, "status": "failed", "stage": "create"}
    print(f"    ✓ task_id: {task_id}")

    print(f"    → 轮询中")
    result = poll_task(task_id, api_key, mode, provider=provider)
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


def poll_one(task_id: str, api_key: str, mode: str, item_id: str, provider: str = DEFAULT_PROVIDER) -> tuple:
    result = poll_task(task_id, api_key, mode, provider=provider)
    return (item_id, result, task_id)


def run_parallel(items: list, output_dir: Path, api_key: str, manifest_mode: str,
                 aspect_ratio: str, resolution: str, provider: str = DEFAULT_PROVIDER) -> list:
    total = len(items)
    print(f"\n{'='*60}")
    print(f"并行模式 · {total} 项同时跑")
    print(f"{'='*60}")

    # Step 1: 串行创建所有任务
    task_entries = []
    for idx, entry in enumerate(items, 1):
        # entry is either a dict (item) or tuple (item, item_mode)
        if isinstance(entry, tuple):
            item, item_mode = entry
        else:
            item, item_mode = entry, manifest_mode

        err = validate_item(item)
        if err:
            print(f"  [{idx}/{total}] ✗ 跳过: {err}")
            task_entries.append((item.get("id", "?"), item, None, "validate", item_mode))
            continue

        item_id = item["id"]
        print(f"  [{idx}/{total}] {item_id} → 创建任务 ({item_mode})")
        task_id = create_task(item["prompt"], api_key, item_mode, item.get("images"), aspect_ratio, resolution, provider=provider)
        if not task_id:
            task_entries.append((item_id, item, None, "create", item_mode))
        else:
            print(f"    ✓ task_id={task_id}")
            task_entries.append((item_id, item, task_id, None, item_mode))

    # Step 2: 并行轮询
    print(f"\n  并行轮询中...")
    poll_results = {}
    with ThreadPoolExecutor(max_workers=len(task_entries)) as executor:
        futures = {
            executor.submit(poll_one, tid, api_key, item_mode, iid, provider): iid
            for iid, _, tid, _, item_mode in task_entries if tid
        }
        for future in as_completed(futures):
            iid = futures[future]
            try:
                _, poll_result, _ = future.result()
                poll_results[iid] = poll_result
            except Exception as e:
                print(f"    ✗ {iid} 轮询异常: {e}")
                poll_results[iid] = None

    # Step 3: 并行下载
    print(f"\n  并行下载中...")
    results = []
    with ThreadPoolExecutor(max_workers=len(task_entries)) as executor:
        futures = {}
        for iid, item, tid, failed_stage, item_mode in task_entries:
            if failed_stage:
                results.append({"id": iid, "status": "failed", "stage": failed_stage})
                continue
            if tid is None:
                continue
            futures[executor.submit(
                _download_item, iid, item, poll_results.get(iid), output_dir, item_mode, api_key, tid,
            )] = iid
        for future in as_completed(futures):
            iid = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"id": iid, "status": "failed", "stage": "exception"})

    return results


def _download_item(iid: str, item: dict, poll_result: dict | None,
                   output_dir: Path, mode: str, api_key: str, task_id: str) -> dict:
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


def run_single(mode: str, prompt: str, images: list[str] | None, name_tag: str,
               output_dir: Path, api_key: str, aspect_ratio: str, resolution: str,
               provider: str = DEFAULT_PROVIDER) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_stem = f"{name_tag}-{timestamp}"

    item_id = file_stem
    print(f"→ 创建{mode}任务")

    task_id = create_task(prompt, api_key, mode, images, aspect_ratio, resolution, provider=provider)
    if not task_id:
        print("✗ 创建任务失败")
        sys.exit(1)
    print(f"✓ task_id: {task_id}")

    print(f"→ 轮询中(最多等 {POLL_MAX_TIMES * POLL_INTERVAL}s)")
    result = poll_task(task_id, api_key, mode, provider=provider)
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
    provider = args.provider
    has_mulerun = bool(os.environ.get("MULERUN_API_KEY"))
    has_apimart = bool(os.environ.get("APIMART_API_KEY"))
    has_atlascloud = bool(os.environ.get("ATLASCLOUD_API_KEY"))
    if args.provider == DEFAULT_PROVIDER and not has_mulerun:
        if has_apimart:
            provider = "apimart"
            print(f"  自动检测: APIMART_API_KEY 已设置,切换到 apimart")
        elif has_atlascloud:
            provider = "atlascloud"
            print(f"  自动检测: ATLASCLOUD_API_KEY 已设置,切换到 atlascloud")

    # 加载 blocklist
    blocklist = load_blocklist(args.blocklist)

    # 鉴权
    env_var = PROVIDERS[provider]["env_var"]
    api_key = os.environ.get(env_var)
    if not api_key:
        print(f"✗ 未找到环境变量 {env_var}")
        print(f"  请先设置: export {env_var}=sk-xxx")
        sys.exit(1)

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
        print(f"批量{mode}模式 · {total} 项 · {'并行' if args.parallel else '串行'} · provider={provider}")
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
                item_mode = resolve_item_mode(item, mode)
                filtered.append((item, item_mode))
            results += run_parallel(filtered, output_dir, api_key, mode, aspect_ratio, resolution, provider=provider)
        else:
            results = []
            for idx, item in enumerate(items, 1):
                err = validate_item(item)
                if err:
                    print(f"\n[{idx}/{total}] ✗ 跳过: {err}")
                    results.append({"id": item.get("id", "?"), "status": "failed", "stage": "validate"})
                    continue
                check_blocklist(item["prompt"], blocklist, context=item.get("id", f"item-{idx}"))
                item_mode = resolve_item_mode(item, mode)
                results.append(process_single_item(item, output_dir, api_key, item_mode, aspect_ratio, resolution, idx, total, provider=provider))

        # 写运行元数据
        meta_path = output_dir / "_run_metadata.json"
        meta_path.write_text(
            json.dumps({
                "timestamp": datetime.now().strftime("%Y%m%d-%H%M%S"),
                "provider": provider,
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
    run_single(args.mode, prompt, images, args.name_tag, output_dir, api_key, args.aspect_ratio, args.resolution, provider=provider)


if __name__ == "__main__":
    main()

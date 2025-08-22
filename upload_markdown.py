import argparse
import json
import mimetypes
import os
import sys
import time
import shutil
from typing import Dict, List, Optional, Set, Tuple

from dify_knowledge_api import DifyKnowledgeAPI


def find_markdown_files(directory_path: str) -> List[str]:
    """Return a sorted list of Markdown file paths in the given directory."""
    if not os.path.isdir(directory_path):
        return []
    markdown_suffixes = (".md", ".markdown")
    file_names = [
        os.path.join(directory_path, file_name)
        for file_name in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, file_name))
    ]
    markdown_files = [
        file_path for file_path in file_names if file_path.lower().endswith(markdown_suffixes)
    ]
    markdown_files.sort()
    return markdown_files


def fetch_existing_document_names(
    api_client: DifyKnowledgeAPI,
    dataset_id: str,
    page_limit: int = 100,
) -> Set[str]:
    """Return a set of normalized document names already in dataset.

    Normalization: lowercased raw name, and lowercased name without extension.
    """
    normalized: Set[str] = set()
    page = 1
    while True:
        ok, body = api_client.documents.list_documents(
            dataset_id=dataset_id,
            page=page,
            limit=page_limit,
        )
        if not ok or not isinstance(body, dict):
            break
        items = body.get("data") or []
        for item in items:
            name_value = item.get("name")
            if not name_value:
                continue
            lower = str(name_value).lower()
            normalized.add(lower)
            base_no_ext = os.path.splitext(lower)[0]
            normalized.add(base_no_ext)
        has_more = bool(body.get("has_more"))
        if not has_more:
            break
        page += 1
    return normalized


def wait_for_batch_completion(
    api_client: DifyKnowledgeAPI,
    dataset_id: str,
    batch_id: str,
    poll_interval_seconds: int,
    indexing_timeout_seconds: int,
) -> Tuple[bool, Optional[List[Dict]]]:
    """Poll indexing status until completed or timeout/error.

    Returns (completed_successfully, items_or_none)
    """
    start_time = time.time()
    deadline = start_time + float(indexing_timeout_seconds)
    last_message = None
    while time.time() < deadline:
        ok, body = api_client.documents.get_indexing_status(
            dataset_id=dataset_id,
            batch_id=batch_id,
        )
        if not ok or not isinstance(body, dict):
            # Transient issues; wait and retry
            time.sleep(poll_interval_seconds)
            continue

        items = body.get("data") or []
        if not items:
            time.sleep(poll_interval_seconds)
            continue

        # Determine overall status
        any_error = False
        all_completed = True
        progress_notes: List[str] = []
        for item in items:
            status = item.get("indexing_status")
            completed_at = item.get("completed_at")
            error = item.get("error")
            completed_segments = item.get("completed_segments")
            total_segments = item.get("total_segments")
            if error:
                any_error = True
            if not completed_at and (status != "completed"):
                all_completed = False
            if completed_segments is not None and total_segments is not None:
                progress_notes.append(f"{completed_segments}/{total_segments}")
            elif status:
                progress_notes.append(str(status))

        message = ", ".join(progress_notes) if progress_notes else "waiting"
        if message != last_message:
            print(f"       indexing: {message}", flush=True)
            last_message = message

        if any_error:
            return False, items
        if all_completed:
            return True, items

        time.sleep(poll_interval_seconds)

    return False, items if 'items' in locals() else None


def copy_missing_output_files_to_markdown(
    api_client: DifyKnowledgeAPI,
    dataset_id: str,
    output_dir: str,
    markdown_dir: str,
) -> Tuple[int, int, int]:
    """Copy files from output_dir to markdown_dir if not present in the dataset.

    Returns (copied_count, skipped_count, considered_count).
    """
    if not os.path.isdir(output_dir):
        return 0, 0, 0

    os.makedirs(markdown_dir, exist_ok=True)

    candidates: List[str] = []
    for file_name in os.listdir(output_dir):
        source_path = os.path.join(output_dir, file_name)
        if not os.path.isfile(source_path):
            continue
        lower_name = file_name.lower()
        if lower_name.endswith((".md", ".markdown")):
            candidates.append(source_path)

    existing_names = fetch_existing_document_names(
        api_client=api_client,
        dataset_id=dataset_id,
    )

    copied_count = 0
    skipped_count = 0
    for source_path in candidates:
        file_name = os.path.basename(source_path)
        base_no_ext = os.path.splitext(file_name)[0]
        lower_file = file_name.lower()
        lower_base = base_no_ext.lower()

        if lower_file in existing_names or lower_base in existing_names:
            skipped_count += 1
            continue

        destination_path = os.path.join(markdown_dir, file_name)
        if os.path.exists(destination_path):
            skipped_count += 1
            continue

        shutil.copy2(source_path, destination_path)
        copied_count += 1

    return copied_count, skipped_count, len(candidates)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=
        "Upload Markdown files from a local directory to a Dify knowledge base sequentially.")
    parser.add_argument(
        "--dataset-id",
        default=os.getenv("DIFY_DATASET_ID"),
        help="Target dataset ID. Can also be set via DIFY_DATASET_ID env var.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("DIFY_API_KEY"),
        help="Dify API key. Can also be set via DIFY_API_KEY env var.",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("DIFY_API_BASE", "https://llm.bupt.edu.cn/v1"),
        help="API base URL. Default: https://llm.bupt.edu.cn/v1 (override with DIFY_API_BASE)",
    )
    parser.add_argument(
        "--dir",
        default=os.getenv("MARKDOWN_DIR", "markdown"),
        help="Directory containing Markdown files. Default: ./markdown",
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("OUTPUT_DIR", "output"),
        help="Directory containing source Markdown files to filter from. Default: ./output",
    )
    parser.add_argument(
        "--copy-missing-from-output",
        action="store_true",
        help=(
            "Before uploading, copy files from --output-dir to --dir if they are not in the dataset."
        ),
    )
    parser.add_argument(
        "--copy-missing-only",
        action="store_true",
        help=(
            "Only perform copying missing files from --output-dir to --dir and then exit."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("DIFY_HTTP_TIMEOUT", "120")),
        help="HTTP timeout in seconds for each upload. Default: 120",
    )
    parser.add_argument(
        "--indexing-timeout",
        type=int,
        default=int(os.getenv("DIFY_INDEXING_TIMEOUT", "600")),
        help="Max seconds to wait for indexing to complete per file. Default: 600",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.getenv("DIFY_POLL_INTERVAL", "5")),
        help="Seconds between status polls. Default: 5",
    )
    parser.add_argument(
        "--fallback-timeout-seconds",
        type=int,
        default=int(os.getenv("DIFY_FALLBACK_TIMEOUT", "300")),
        help="Seconds to wait for indexing before triggering fallback (delete and retry). Default: 300",
    )
    parser.add_argument(
        "--fallback-retry-wait-seconds",
        type=int,
        default=int(os.getenv("DIFY_FALLBACK_RETRY_WAIT", "300")),
        help="Seconds to wait after deletion before re-uploading. Default: 300",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.dataset_id:
        print("[ERROR] Missing --dataset-id (or set DIFY_DATASET_ID)")
        return 2
    if not args.api_key:
        print("[ERROR] Missing --api-key (or set DIFY_API_KEY)")
        return 2
    if not args.api_base:
        print("[ERROR] Missing --api-base (or set DIFY_API_BASE)")
        return 2

    # Initialize the Dify API client
    api_client = DifyKnowledgeAPI(
        api_base=args.api_base,
        api_key=args.api_key,
        timeout_seconds=args.timeout
    )

    print(f"Using API base: {args.api_base}")
    print(f"Dataset ID: {args.dataset_id}")
    print(f"Timeout: {args.timeout} seconds")
    print()

    target_dir = os.path.abspath(args.dir)
    output_dir = os.path.abspath(args.output_dir)

    if getattr(args, "copy_missing_from_output", False) or getattr(args, "copy_missing_only", False):
        print("Preparing markdown directory by copying non-indexed files from output...", flush=True)
        copied, skipped, considered = copy_missing_output_files_to_markdown(
            api_client=api_client,
            dataset_id=args.dataset_id,
            output_dir=output_dir,
            markdown_dir=target_dir,
        )
        print(
            f"Prepared. Considered: {considered}, Copied: {copied}, Skipped: {skipped}",
            flush=True,
        )
        if getattr(args, "copy_missing_only", False):
            return 0

    files = find_markdown_files(target_dir)
    if not files:
        print(f"[WARN] No Markdown files found in: {target_dir}")
        return 0

    print(f"Uploading {len(files)} Markdown file(s) from '{target_dir}' to dataset '{args.dataset_id}'...")
    print("Fetching existing documents for skip-check...", flush=True)
    existing_names = fetch_existing_document_names(
        api_client=api_client,
        dataset_id=args.dataset_id,
    )
    print(f"Found {len(existing_names)} existing name entries.", flush=True)
    total = len(files)
    success_count = 0
    failure_count = 0

    for index, file_path in enumerate(files, start=1):
        file_name = os.path.basename(file_path)
        base_no_ext = os.path.splitext(file_name)[0]
        lower_file = file_name.lower()
        lower_base = base_no_ext.lower()
        if lower_file in existing_names or lower_base in existing_names:
            print(f"[{index}/{total}] Skipped (exists): {file_name}", flush=True)
            success_count += 1
            continue

        print(f"[{index}/{total}] Uploading: {file_name}", flush=True)
        ok, result = api_client.documents.create_document_from_file(
            dataset_id=args.dataset_id,
            file_path=file_path,
            indexing_technique="high_quality",
        )
        if ok:
            success_count += 1
            document_id = None
            batch_id = None
            if isinstance(result, dict):
                document_id = (
                    (result.get("document") or {}).get("id") if result.get("document") else None
                )
                batch_id = result.get("batch")
            print(
                f"    -> Success. Document ID: {document_id or '-'}; Batch: {batch_id or '-'}",
                flush=True,
            )
            if batch_id:
                print("       Waiting for indexing to complete...", flush=True)
                completed, items = wait_for_batch_completion(
                    api_client=api_client,
                    dataset_id=args.dataset_id,
                    batch_id=batch_id,
                    poll_interval_seconds=args.poll_interval,
                    indexing_timeout_seconds=min(args.indexing_timeout, args.fallback_timeout_seconds),
                )
                if completed:
                    print("       -> Indexing completed.", flush=True)
                else:
                    print("       -> Indexing exceeded fallback timeout; attempting delete and retry...", flush=True)
                    if document_id:
                        deleted, del_result = api_client.documents.delete_document(
                            dataset_id=args.dataset_id,
                            document_id=document_id,
                        )
                        if deleted:
                            print("       -> Deleted stuck document. Waiting before retry...", flush=True)
                            time.sleep(args.fallback_retry_wait_seconds)
                            print("       -> Retrying upload...", flush=True)
                            re_ok, re_result = api_client.documents.create_document_from_file(
                                dataset_id=args.dataset_id,
                                file_path=file_path,
                                indexing_technique="high_quality",
                            )
                            if re_ok:
                                re_batch_id = None
                                if isinstance(re_result, dict):
                                    re_batch_id = re_result.get("batch")
                                if re_batch_id:
                                    print("       -> Waiting for indexing after retry...", flush=True)
                                    re_completed, _ = wait_for_batch_completion(
                                        api_client=api_client,
                                        dataset_id=args.dataset_id,
                                        batch_id=re_batch_id,
                                        poll_interval_seconds=args.poll_interval,
                                        indexing_timeout_seconds=args.indexing_timeout,
                                    )
                                    if re_completed:
                                        print("       -> Retry indexing completed.", flush=True)
                                    else:
                                        failure_count += 1
                                        print("       -> Retry indexing failed or timed out.", flush=True)
                                else:
                                    failure_count += 1
                                    print("       -> Retry upload did not return batch id.", flush=True)
                            else:
                                failure_count += 1
                                print("       -> Retry upload failed.", flush=True)
                        else:
                            failure_count += 1
                            print("       -> Delete failed; cannot retry.", flush=True)
                    else:
                        failure_count += 1
                        print("       -> No document id; cannot delete and retry.", flush=True)
        else:
            failure_count += 1
            print("    -> Failed.")
            if isinstance(result, dict):
                status_code = result.get("status_code") or result.get("status")
                message = result.get("message") or result.get("error") or result.get("text")
                code = result.get("code")
                if status_code or code or message:
                    print(f"       code={code or '-'} status={status_code or '-'} message={message or '-'}")
            else:
                print("       Unknown error.")

    print(
        f"Done. Success: {success_count}, Failed: {failure_count}, Total: {total}",
        flush=True,
    )
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())



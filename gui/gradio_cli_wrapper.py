"""Minimal Gradio front-end that wraps inference.py via subprocess."""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INFERENCE_SCRIPT = PROJECT_ROOT / "inference.py"

DEFAULTS = {
    "model_type": "bs_roformer",
    "config_path": "ckpt/bs_rofomer/BS-Rofo-SW-Fixed.yaml",
    "start_check_point": "ckpt/bs_rofomer/BS-Rofo-SW-Fixed.ckpt",
    "input_folder": "audio/",
    "store_dir": "separated/",
    "device_ids": "0",
}


def build_command(
    *,
    model_type: str,
    config_path: str,
    start_check_point: str,
    input_folder: str,
    store_dir: str,
    extract_instrumental: bool,
    use_tta: bool,
    force_cpu: bool,
    device_ids: str,
) -> List[str]:
    """Construct the CLI command used to launch inference.py."""

    cmd: List[str] = [
        sys.executable,
        str(INFERENCE_SCRIPT),
        "--model_type",
        model_type,
        "--config_path",
        config_path,
        "--start_check_point",
        start_check_point,
        "--input_folder",
        input_folder,
        "--store_dir",
        store_dir,
    ]

    if extract_instrumental:
        cmd.append("--extract_instrumental")
    if use_tta:
        cmd.append("--use_tta")
    if force_cpu:
        cmd.append("--force_cpu")

    device_ids = (device_ids or "").strip()
    if device_ids:
        cmd.append("--device_ids")
        cmd.extend(_split_device_ids(device_ids))

    return cmd


def _split_device_ids(value: str) -> Iterable[str]:
    return value.replace(",", " ").split()


def run_inference(
    model_type: str,
    config_path: str,
    start_check_point: str,
    input_folder: str,
    store_dir: str,
    extract_instrumental: bool,
    use_tta: bool,
    force_cpu: bool,
    device_ids: str,
) -> str:
    cmd = build_command(
        model_type=model_type,
        config_path=config_path,
        start_check_point=start_check_point,
        input_folder=input_folder,
        store_dir=store_dir,
        extract_instrumental=extract_instrumental,
        use_tta=use_tta,
        force_cpu=force_cpu,
        device_ids=device_ids,
    )

    quoted_cmd = " ".join(shlex.quote(part) for part in cmd)

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return f"Failed to run inference script: {exc}\nCommand: {quoted_cmd}"

    output_sections = [
        f"$ {quoted_cmd}",
        "",
        completed.stdout.strip(),
        completed.stderr.strip(),
    ]
    return "\n".join(section for section in output_sections if section)


def create_demo() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown(
            """
            ## BS-RoFormer CLI Wrapper
            填写与 `split-by-bs-rofomer.sh` 相同的参数，点击 **Run** 即可触发
            `inference.py`，结果会写入 `store_dir`。
            """
        )

        with gr.Row():
            model_type = gr.Textbox(label="Model Type", value=DEFAULTS["model_type"], scale=1)
            device_ids = gr.Textbox(label="Device IDs (e.g. 0 or 0 1)", value=DEFAULTS["device_ids"], scale=1)

        config_path = gr.Textbox(label="Config Path", value=DEFAULTS["config_path"])
        checkpoint_path = gr.Textbox(label="Checkpoint Path", value=DEFAULTS["start_check_point"])
        input_folder = gr.Textbox(label="Input Folder", value=DEFAULTS["input_folder"])
        store_dir = gr.Textbox(label="Store Dir", value=DEFAULTS["store_dir"])

        with gr.Row():
            extract_instrumental = gr.Checkbox(label="Extract Instrumental", value=True)
            use_tta = gr.Checkbox(label="Use TTA (slower)", value=False)
            force_cpu = gr.Checkbox(label="Force CPU", value=False)

        run_button = gr.Button("Run inference")
        logs = gr.Textbox(label="CLI output", lines=20)

        run_button.click(
            fn=run_inference,
            inputs=[
                model_type,
                config_path,
                checkpoint_path,
                input_folder,
                store_dir,
                extract_instrumental,
                use_tta,
                force_cpu,
                device_ids,
            ],
            outputs=logs,
        )

    return demo


demo = create_demo()


def main() -> None:
    demo.launch()


if __name__ == "__main__":
    main()

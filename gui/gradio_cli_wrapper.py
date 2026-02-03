"""Minimal Gradio front-end that wraps inference.py via subprocess."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Iterator, List

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INFERENCE_SCRIPT = PROJECT_ROOT / "inference.py"

DEFAULTS = {
    "model_type": "bs_roformer",
    "config_path": "ckpt/bs_rofomer/BS-Rofo-SW-Fixed.yaml",
    "start_check_point": "ckpt/bs_rofomer/BS-Rofo-SW-Fixed.ckpt",
    "input_file": "audio/sea.wav",
    "store_dir": "separated/",
    "device_ids": "0",
}


def build_command(
    *,
    model_type: str,
    config_path: str,
    start_check_point: str,
    input_file: str,
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
        "--input_file",
        input_file,
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
    input_file: str,
    store_dir: str,
    model_type: str = DEFAULTS["model_type"],
    config_path: str = DEFAULTS["config_path"],
    start_check_point: str = DEFAULTS["start_check_point"],
    extract_instrumental: bool = False,
    use_tta: bool = False,
    force_cpu: bool = False,
    device_ids: str = DEFAULTS["device_ids"],
) -> str:
    """Run inference.py as a subprocess and capture its output.
        audio file(song.wav/.mp3/etc) will be separated into store_dir/song/{tracks}.wav

        you may just need to fill in input_file and store_dir,
        leave other parameters as default for BS-RoFormer inference.

        for agent:
        this function may take a while to finish(about 1 min for a typical song), depending on the model and hardware you use.
        u can check the folder store_dir to see if the results are generated.
        feel free to do other things while waiting :)
        you'd better use absolute path for folder to avoid confusion.


    Args:
        input_file: Path to input audio file.
        store_dir: Path to output folder. file will have its own subfolder under store_dir to store the separated tracks. you'd better use absolute path here to avoid confusion. Attention: you'd better can an empty folder for this argument to avoid mixing old and new results.
        model_type: Model type to use.
        config_path: Path to model config file.
        start_check_point: Path to model checkpoint file.
        extract_instrumental: Whether to extract instrumental track.
        use_tta: Whether to use test-time augmentation.
        force_cpu: Whether to force CPU usage.
        device_ids: Device IDs to use.

    """
    if input_file == store_dir:
        return "Error: input_file and store_dir must be different to avoid overwriting files."
    cmd = build_command(
        model_type=model_type,
        config_path=config_path,
        start_check_point=start_check_point,
        input_file=input_file,
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
            model_type = gr.Textbox(
                label="Model Type", value=DEFAULTS["model_type"], scale=1
            )
            device_ids = gr.Textbox(
                label="Device IDs (e.g. 0 or 0 1)",
                value=DEFAULTS["device_ids"],
                scale=1,
            )

        config_path = gr.Textbox(label="Config Path", value=DEFAULTS["config_path"])
        checkpoint_path = gr.Textbox(
            label="Checkpoint Path", value=DEFAULTS["start_check_point"]
        )
        input_file = gr.Textbox(label="Input File", value=DEFAULTS["input_file"])
        store_dir = gr.Textbox(label="Store Dir", value=DEFAULTS["store_dir"])

        with gr.Row():
            extract_instrumental = gr.Checkbox(
                label="Extract Instrumental", value=False
            )
            use_tta = gr.Checkbox(label="Use TTA (slower)", value=False)
            force_cpu = gr.Checkbox(label="Force CPU", value=False)

        run_button = gr.Button("Run inference")
        logs = gr.Textbox(label="CLI output", lines=20)

        run_button.click(
            fn=run_inference,
            inputs=[
                input_file,
                store_dir,
                model_type,
                config_path,
                checkpoint_path,
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
    demo.launch(mcp_server=True, server_port=7867)


if __name__ == "__main__":
    main()

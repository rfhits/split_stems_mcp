# BS-RoFormer Gradio 批量推理最小方案

## 背景与约束
- 现有 `inference.py` 已经可以批量处理一个输入目录并将结果写入 `store_dir`。
- **禁止修改** `inference.py` 及其现有行为；新能力只能在其基础上追加。
- 目标只是一个“能用的简单演示版”Gradio 页面：填写 `input_folder`、`store_dir`、`config`、`checkpoint` 等，再点击按钮即可触发与 CLI 同样的推理流程。
- 不做音频上传、在线试听或打包下载，Gradio 仅作参数收集与任务触发。
- 后续仍需要将该 Gradio 页面用作 MCP server 的入口，但 MCP 只需包装相同的触发逻辑，不需要额外协议实现。

## 总体思路
1. **沿用 CLI**：将 Gradio 视为一个前端壳，底层直接调用 `python inference.py ...`（或 `split-by-bs-rofomer.sh`）。
   - 通过 `subprocess.run` 执行，参数取自前端填写的表单。
   - 复用 CLI 的所有能力（TTA、instrumental、progress bar 等），无需复制 `run_folder` 逻辑。
2. **日志与结果展示**：
   - 采集子进程的 `stdout/stderr`，在 Gradio 中用 `Textbox`/`Markdown` 展示执行日志。
   - 由于输出仍写入用户指定的 `store_dir`，Gradio 提供一个“打开目录”的提示即可。
3. **MCP 集成**：
   - Gradio ≥ 5.49 自带 MCP server。对外暴露同一个 `demo` 对象即可。
   - MCP 调用时传递与 UI 相同的表单字段；server 端仍然通过 CLI 完成工作。

## 模块划分
- `gui/gradio_cli_wrapper.py`（新增）
  - `build_command(form_inputs: dict) -> list[str]`
    - 生成类 `split-by-bs-rofomer.sh` 的命令行：`[sys.executable, "inference.py", "--model_type", ...]`。
  - `run_inference(**kwargs) -> str`
    - 用 `subprocess.run(..., capture_output=True, text=True)` 执行命令，返回日志文本。
  - `demo = gr.Blocks(...)`
    - 表单字段：`model_type`, `config_path`, `start_check_point`, `input_folder`, `store_dir`, `extract_instrumental`, `use_tta`, `force_cpu`, `device_ids`。
    - 点击按钮后调用 `run_inference`，将日志显示在 `gr.Textbox`。
  - `main()`：`demo.launch()`。
- README / docs 更新
  - 简要说明如何运行：`uv run bs-roformer-gradio` 或 `python -m gui.gradio_cli_wrapper`。

## 参数策略
- **默认值**：与 `split-by-bs-rofomer.sh` 相同，方便直接点击运行：
  - `model_type=bs_roformer`
  - `config_path=ckpt/bs_rofomer/BS-Rofo-SW-Fixed.yaml`
  - `start_check_point=ckpt/bs_rofomer/BS-Rofo-SW-Fixed.ckpt`
  - `input_folder=audio/`, `store_dir=separated/`
- **安全性**：保证所有路径均以字符串传入，不做额外校验，保持最小实现。

## MCP 使用
- 暴露 `demo` 给 MCP：`python -m gradio mcp gui.gradio_cli_wrapper:demo`。
- MCP 客户端输入同样的表单字段（或直接传 JSON 参数），Gradio MCP 将它们映射到 `run_inference`。
- 输出即 CLI 日志文本，可提示用户在本地 `store_dir` 查看结果。

## 实施步骤
1. 新建 `gui/gradio_cli_wrapper.py`，实现上述逻辑。
2. 在 `pyproject.toml` 的 `[project.scripts]` 中确认 `bs-roformer-gradio = "gui.gradio_cli_wrapper:main"`（若已存在则保持一致）。
3. README/`.tasks/tasks.md` 中补充“如何启动 Gradio UI 和 MCP server”。
4. 手动验证：
   - CLI 方式仍可运行 `split-by-bs-rofomer.sh`。
   - `python -m gui.gradio_cli_wrapper`，在浏览器里填写默认参数，点击运行并检查 `separated/`。
   - `python -m gradio mcp gui.gradio_cli_wrapper:demo`，通过 MCP 客户端发起一次调用。

该方案做到：**零改动**现有推理代码、最小 UI 实现、后续 MCP 也能直接沿用。

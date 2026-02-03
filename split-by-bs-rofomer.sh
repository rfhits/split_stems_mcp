uv run python inference.py \
    --model_type bs_roformer \
    --config_path ckpt/bs_rofomer/BS-Rofo-SW-Fixed.yaml \
    --start_check_point ckpt/bs_rofomer/BS-Rofo-SW-Fixed.ckpt \
    --input_file audio/sea.wav \
    --store_dir separated/

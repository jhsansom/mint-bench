#!/bin/bash

export HF_HOME=/data/jhsansom/model_weights

MODEL="Qwen/Qwen3-8B"

vllm serve $MODEL \
  --reasoning-parser deepseek_r1 \
  --quantization fp8 \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.75 \
  --max-model-len 8192 \
  --port 8080
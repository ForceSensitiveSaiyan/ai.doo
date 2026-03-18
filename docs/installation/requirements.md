# Hardware Requirements

## Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 16 GB | 32 GB |
| **Storage** | 50 GB SSD | 100 GB+ NVMe |
| **GPU** | NVIDIA with 8 GB VRAM | NVIDIA with 16+ GB VRAM |
| **OS** | Ubuntu 22.04+ / Debian 12+ | Ubuntu 24.04 LTS |

## GPU Support

ai.doo uses [Ollama](https://ollama.ai) for local AI inference. GPU acceleration is strongly recommended.

**Supported GPUs:**

- **NVIDIA** (recommended): Any GPU with CUDA support and 8+ GB VRAM. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
- **AMD ROCm**: Supported via Ollama's ROCm build. Start with `make up ROCM=1`.
- **CPU-only**: Works but significantly slower. Start with `make up CPU=1`.

## Software Prerequisites

| Software | Version | Required For |
|----------|---------|--------------|
| Docker | 24.0+ | All services |
| Docker Compose | v2.20+ | Orchestration |
| curl | Any | Installer script |
| NVIDIA Container Toolkit | Latest | GPU inference |

## Model Storage

AI models are stored in a shared Docker volume (`ollama_models`). Budget storage based on the models you plan to use:

| Model | Size |
|-------|------|
| llama3.2:3b | ~2 GB |
| llama3.1:8b | ~4.7 GB |
| qwen2.5-coder:14b | ~9 GB |

## Network

- All services communicate over an internal Docker network (`ollama_network`).
- No outbound internet required after initial setup (model downloads).
- Default ports: Ollama `:11434`, Hub `:2000`, PIKA `:8000`, VERA backend `:4000`, VERA frontend `:3000`.

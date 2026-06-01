# Local AI Inference Stack with Podman

A containerized AI inference stack built on Rocky Linux using Podman, featuring a local LLM server, a web-based chat interface, and a production-grade monitoring solution.

---

## Project Overview

This project deploys a fully local AI stack using open-source tools and OCI-compliant containers managed by Podman. The stack consists of four containers connected through an isolated virtual network (`llm-net`), and the entire deployment is automated using a Jenkins CI/CD pipeline.

The project was developed as part of the UVT × IBM MLOps collaboration, with the goal of demonstrating container fundamentals, networking, monitoring, and deployment automation in a real-world context.

---

## Stack Architecture

```
┌─────────────────────────────────────────────────────┐
│                  llm-net (bridge network)            │
│                                                     │
│  ┌─────────────┐        ┌─────────────────────┐     │
│  │ llama-server│◄───────│     open-webui      │     │
│  │  port 8080  │        │     port 3000       │     │
│  └─────────────┘        └─────────────────────┘     │
│                                                     │
│  ┌─────────────┐        ┌─────────────────────┐     │
│  │ prometheus  │◄───────│      grafana        │     │
│  │  port 9090  │        │     port 4000       │     │
│  └─────────────┘        └─────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## Containers

### 1. llama-server
- **Image:** `ghcr.io/ggml-org/llama.cpp:server`
- **Port:** `8080`
- **Purpose:** Runs the Qwen2.5 0.5B Instruct model (Q4_K_M quantized) and exposes an OpenAI-compatible REST API for inference requests.
- **Model:** Downloaded from HuggingFace and stored at `/opt/models/model.gguf`

### 2. open-webui
- **Image:** `ghcr.io/open-webui/open-webui:main`
- **Port:** `3000`
- **Purpose:** Provides a ChatGPT-like web interface for interacting with the local AI model. Communicates with `llama-server` through the internal `llm-net` network.

### 3. Prometheus *(custom container)*
- **Image:** `localhost/my-prometheus:latest`
- **Port:** `9090`
- **Purpose:** Scrapes and stores metrics from the running containers every 15 seconds. Built from a custom Containerfile with a baked-in configuration file.

### 4. Grafana
- **Image:** `docker.io/grafana/grafana:latest`
- **Port:** `4000`
- **Purpose:** Connects to Prometheus and visualizes container metrics through a live dashboard. Shows container health, uptime, and scrape performance.

---

## Project Structure

```
ibm-mlops/
├── Containerfile       # Prometheus custom image definition
├── prometheus.yml      # Prometheus scraping configuration
├── Jenkinsfile         # CI/CD pipeline definition
├── stack.yaml          # Kubernetes-compatible deployment YAML
└── README.md           # Project documentation
```

---

## Prerequisites

- Rocky Linux 9
- Podman installed and configured
- Jenkins installed and running on port `8081`
- At least 6 GB RAM and 20 GB disk space

---

## Manual Setup

If you want to run the stack manually without Jenkins:

**Step 1 — Create the models directory:**
```bash
sudo mkdir -p /opt/models
```

**Step 2 — Create the container network:**
```bash
sudo podman network create llm-net
```

**Step 3 — Download the AI model:**
```bash
sudo curl -L -o /opt/models/model.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
```

**Step 4 — Build the Prometheus image:**
```bash
sudo podman build -t my-prometheus .
```

**Step 5 — Run all containers:**
```bash
sudo podman run -d --name llama-server --network llm-net \
  -v /opt/models:/models:Z -p 8080:8080 \
  ghcr.io/ggml-org/llama.cpp:server \
  -m /models/model.gguf --host 0.0.0.0 --port 8080

sudo podman run -d --name open-webui --network llm-net \
  -p 3000:8080 \
  -e OPENAI_API_BASE_URL=http://llama-server:8080/v1 \
  -e OPENAI_API_KEY=sk-no-key-required \
  ghcr.io/open-webui/open-webui:main

sudo podman run -d --name prometheus --network llm-net \
  -p 9090:9090 localhost/my-prometheus:latest

sudo podman run -d --name grafana --network llm-net \
  -p 4000:3000 docker.io/grafana/grafana:latest
```

---

## Automated Setup with Jenkins

The entire deployment is automated via a Jenkins pipeline with the following stages:

| Stage | Description |
|-------|-------------|
| Create /opt/models directory | Creates the directory for storing the AI model |
| Create podman network | Creates the isolated `llm-net` bridge network |
| Download model | Downloads the Qwen model from HuggingFace (skipped if already present) |
| Start llama-server | Deploys the AI inference container |
| Start open-webui | Deploys the chat interface container |
| Start Prometheus | Deploys the metrics collection container |
| Start Grafana | Deploys the visualization container |
| Verify containers | Confirms all containers are running correctly |

To run the pipeline:
1. Open Jenkins at `http://localhost:8081`
2. Open the `AI-deploy` pipeline
3. Click **Build Now**

---

## Accessing the Stack

| Service | URL | Description |
|---------|-----|-------------|
| Chat Interface | http://localhost:3000 | Open WebUI — interact with the AI |
| AI API | http://localhost:8080 | llama-server REST API |
| Metrics | http://localhost:9090 | Prometheus raw metrics |
| Dashboard | http://localhost:4000 | Grafana monitoring dashboard |

---

## Monitoring

Prometheus scrapes metrics from all containers every 15 seconds. The Grafana dashboard visualizes:

- Container uptime (`up` metric)
- Scrape duration
- Samples collected per container

To configure Grafana:
1. Open `http://localhost:4000`
2. Login with `admin` / `admin`
3. Go to **Connections → Data Sources**
4. Add Prometheus at `http://prometheus:9090`
5. Build a dashboard using the available metrics

---

## Kubernetes Deployment

The stack can be deployed to a Kubernetes cluster using the generated YAML:

```bash
# Generate from running containers
sudo podman generate kube llama-server open-webui prometheus grafana > stack.yaml

# Deploy to Kubernetes
kubectl apply -f stack.yaml

# Or replay with Podman
podman play kube stack.yaml
```

---

## Technologies Used

- **Rocky Linux 9** — Enterprise-grade Linux distribution
- **Podman** — Daemonless, rootless container engine
- **llama.cpp** — Efficient LLM inference engine
- **Qwen2.5 0.5B** — Lightweight quantized language model
- **Open WebUI** — ChatGPT-like interface for local models
- **Prometheus** — Metrics collection and monitoring
- **Grafana** — Metrics visualization and dashboards
- **Jenkins** — CI/CD automation server
- **Kubernetes** — Container orchestration (via generated YAML)

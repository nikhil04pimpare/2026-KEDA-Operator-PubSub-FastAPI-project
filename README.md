# 2026 KEDA + Pub/Sub + FastAPI Demo

TL;DR
-----

Local demo wiring: HTTP publisher (FastAPI) -> Pub/Sub emulator (Docker) -> KEDA `ScaledJob` -> Kubernetes Jobs -> short-lived worker pods.

Why this repo
-------------

- Prototype serverless-style batch jobs locally without GCP costs.
- Learn KEDA `ScaledJob` workflows and Pub/Sub integration.
- Small, focused code and manifests so you can iterate quickly.

Highlights
---------

- FastAPI publisher: `POST /publish` to push messages.
- Pub/Sub emulator: Docker Compose service on port `8085`.
- KEDA `ScaledJob`: scales worker Jobs based on subscription backlog.
- Worker: pulls one message, does work, acks, and exits.

Quickstart (2 minutes)
----------------------

1) Start the emulator:

```bash
docker-compose up -d
```

2) Build images:

```bash
docker build -t publisher:latest ./publisher
docker build -t worker:latest ./worker
# for kind: kind load docker-image publisher:latest worker:latest
```

3) Deploy to Kubernetes (KEDA must be installed):

```bash
kubectl apply -f k8s/
```

4) Publish a message:

```bash
kubectl port-forward svc/publisher 8080:80
curl -X POST http://localhost:8080/publish -H "Content-Type: application/json" -d '{"data":"hello"}'
```

5) Watch worker jobs spin up:

```bash
kubectl get pods -w
```

Repository layout
-----------------

```
keda-pubsub-fastapi/
├── docker-compose.yml
├── publisher/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── worker/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── k8s/
    ├── publisher-deployment.yaml
    ├── gcp-pubsub-trigger-auth.yaml
    ├── scaledjob-pubsub.yaml
    └── manual-worker-pod.yaml
```

Architecture (short)
--------------------

[ HTTP POST ] -> FastAPI Publisher -> Pub/Sub Emulator -> KEDA ScaledJob -> Kubernetes Jobs -> Worker Pods

How it works
------------

- The `publisher` creates the Pub/Sub topic/subscription on startup (when emulator is present).
- The `publisher` exposes `POST /publish` to send messages.
- The `k8s/scaledjob-pubsub.yaml` tells KEDA to monitor the subscription backlog and create Jobs (each Job runs one `worker` instance).
- Each `worker` pulls 1 message, processes it, acknowledges it, and exits.

Prerequisites
-------------

- Docker Desktop (with Kubernetes) or Kind/Minikube
- kubectl
- Helm (to install KEDA)

Installation (commands)
-----------------------

Install KEDA:

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

Start emulator and deploy:

```bash
docker-compose up -d
docker build -t publisher:latest ./publisher
docker build -t worker:latest ./worker
kubectl apply -f k8s/
```

Troubleshooting
---------------

- KEDA logs show "google application credentials not found": create the dummy secret in `k8s/gcp-pubsub-trigger-auth.yaml` (the file in this repo contains a small JSON placeholder so KEDA's parser is satisfied).
- Images not found in k8s: set `imagePullPolicy: Never` for local images or push images to a registry. For Kind use `kind load docker-image`.
- ScaledJob shows 0 pending jobs: the GCP scaler may not support the emulator fully; use a manual worker pod to verify the message flow, or supply a real service account JSON to the TriggerAuthentication if testing against GCP.

FAQ
---

Q: Do I need a real `credentials.json` for local testing?

A: No — a minimal dummy JSON stored in a k8s Secret satisfies KEDA's config parser for the emulator. Replace with a real service-account JSON only when running against GCP.

Q: Why does KEDA sometimes not create Jobs even when messages are in the emulator?

A: The GCP Pub/Sub scaler may rely on APIs not implemented by the emulator. For local E2E validation either use a simulator to create Jobs from emulator backlog or test workers manually.


### 4. Observe worker processing via manual run or KEDA-created Jobs

*(See the Troubleshooting section below if the emulator isn’t immediately detected by the KEDA scaler).*

---

## 📂 Files of Interest

Here are the critical layout configurations and system manifests used across this setup:

* **`publisher/`** — Contains the FastAPI event publisher codebase and its optimization `Dockerfile`.
* **`worker/`** — Houses the specialized batch subscriber worker logic alongside its deployment `Dockerfile`.
* **`pubsub-emulator/`** — Holds the local infrastructure stack blueprints and the primary `docker-compose.yml`.
* **`k8s/`** — The orchestration core containing:
* `publisher-deployment.yaml`
* `scaledjob-pubsub.yaml`
* `manual-worker-pod.yaml`
* `gcp-pubsub-trigger-auth.yaml`



---

## 🤝 How to Contribute

**Owner**

This repository is maintained by **Nikhil Pimpare**. For questions, feature requests, or collaboration, open an issue or submit a PR and tag the owner.

**Use cases**

- Local prototyping of event-driven batch workloads using Pub/Sub semantics.
- Learning and testing KEDA `ScaledJob` behavior without cloud costs.
- Demonstrating single-message worker Job patterns for batch pipelines.
- CI smoke tests for message-driven job workflows (emulator-based).

**Contributing**

- **Issues:** Open an issue describing the problem or enhancement with steps to reproduce.
- **PRs:** Fork, create a feature branch (`feature/<short-desc>`), run the checks below, and open a PR against `main` with a clear description and test steps.
- **Testing locally:** Build images and run the emulator locally as shown in Quickstart. If adding code, include a short test procedure in your PR description.
- **Code style:** Keep Python idiomatic (PEP8). Use small, focused commits. Add documentation updates for any behavior changes.
- **Review:** PRs will be reviewed by the maintainer; expect iterative feedback.

Suggested PR targets: add metrics endpoints, Prometheus ServiceMonitors, CI that runs the emulator tests, or improved Kind/Minikube instructions.

---

Cleanup
-------

```bash
kubectl delete -f k8s/
docker-compose down
```
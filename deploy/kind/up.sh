#!/usr/bin/env bash
# Create a kind cluster with Traefik ingress and install the chart from local images.
# App is then served at http://localhost:8081
set -euo pipefail
cd "$(dirname "$0")/../.."

CLUSTER=coding-harness
CTX="kind-$CLUSTER"

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config deploy/kind/kind-config.yaml
fi

helm repo add traefik https://traefik.github.io/charts >/dev/null 2>&1 || true
helm repo update traefik >/dev/null
helm upgrade --install traefik traefik/traefik --kube-context "$CTX" \
  -n traefik --create-namespace \
  --set ports.web.hostPort=80 --set ports.websecure.hostPort=443 \
  --set service.type=ClusterIP \
  --set-string 'nodeSelector.ingress-ready=true' \
  --set 'tolerations[0].key=node-role.kubernetes.io/control-plane' \
  --set 'tolerations[0].operator=Exists' --set 'tolerations[0].effect=NoSchedule' \
  --set ingressClass.isDefaultClass=true
kubectl --context "$CTX" -n traefik rollout status deploy/traefik --timeout=180s

docker build -t coding-harness-api:dev --target api backend
docker build -t coding-harness-worker:dev --target worker backend
docker build -t coding-harness-frontend:dev frontend
kind load docker-image --name "$CLUSTER" coding-harness-api:dev coding-harness-worker:dev coding-harness-frontend:dev

helm upgrade --install coding-harness deploy/helm/coding-harness --kube-context "$CTX" \
  -n coding-harness --create-namespace \
  -f deploy/helm/coding-harness/values-dev.yaml \
  --wait --timeout 5m
helm test coding-harness --kube-context "$CTX" -n coding-harness
echo "Ready: http://localhost:8081"

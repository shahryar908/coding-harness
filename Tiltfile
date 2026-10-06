# Live local cluster: `tilt up` (expects the kind cluster from deploy/kind/up.sh, or any current context).
allow_k8s_contexts(['kind-coding-harness'])

docker_build('coding-harness-api', 'backend', target='api')
docker_build('coding-harness-worker', 'backend', target='worker')
docker_build('coding-harness-frontend', 'frontend')

k8s_yaml(helm(
    'deploy/helm/coding-harness',
    name='coding-harness',
    namespace='coding-harness',
    values=['deploy/helm/coding-harness/values-dev.yaml'],
    # Fixed dev secrets so re-renders don't rotate them (helm template can't look up existing ones).
    set=[
        'secrets.jwtSecret=dev-only-jwt-secret-change-me',
        'postgresql.auth.password=dev-only-postgres-password',
        'api.image.pullPolicy=IfNotPresent',
        'frontend.image.pullPolicy=IfNotPresent',
        'worker.image.pullPolicy=IfNotPresent',
    ],
))

k8s_resource('coding-harness-api', port_forwards='8000:8000', resource_deps=['coding-harness-postgresql'])
k8s_resource('coding-harness-frontend', port_forwards='8080:8080')
k8s_resource('coding-harness-worker', port_forwards='8100:8100')
k8s_resource('coding-harness-postgresql')

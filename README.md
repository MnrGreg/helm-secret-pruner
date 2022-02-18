
## Helm Secret pruner
- Helm by default keeps a history of the last 10 releases manifests as Kubernetes secrets.
- 10 secrets x 2000 namespaces = 20000 secrets
- <20000 causes cluster wide list timeouts across cert-manager,kyverno,nginx-ingress
- https://github.com/jetstack/cert-manager/issues/3748

### Toggle Dry-run environment variable as needed
```yaml
            env:
            - name: DRYRUN
              value: "TRUE"
```

### Configure namespace label selector variable if needed
```yaml
            env:
            - name: LABEL_SELECTOR
              value: "businessunit"
```

### Build and deploy
```shell
export DOCKER_REPO=helmsecretpruner
export DOCKER_TAG=v0.0.1
export DOCKER_REGISTRY=registry-1.docker.io
export DOCKER_ORG=mrgregmay
docker build -t $DOCKER_REGISTRY/$DOCKER_ORG/$DOCKER_REPO:$DOCKER_TAG .
docker push $DOCKER_REGISTRY/$DOCKER_ORG/$DOCKER_REPO:$DOCKER_TAG
```

### Deploy
```shell
export NAMESPACE=<namespace>
cat *.yaml | envsubst | kubectl apply -f -
```

### Trigger Manual Cronjob creation
```shell
kubectl create job  --from cronjob/helmsecretpruner -n $NAMESPACE helmsecretpruner-manual001
```
#!/usr/bin/env python3
"""
Removes all but the last superseded Helm secret from all businessunit labeled namespaces
Uses official Kubernetes Python client https://github.com/kubernetes-client/python
It designed to run within the cluster it is pruning and the service account requires RBAC to delete secrets from all namespaces
"""

from kubernetes import client
import time
import os

DRYRUN = os.environ.get("DRYRUN")
LABEL_SELECTOR = os.environ.get("LABEL_SELECTOR")
SECRET_TYPE = "type=helm.sh/release.v1"
CLUSTER_ENDPOINT = "https://kubernetes.default:443"
BEARER_TOKEN = open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r').read()

def main():

    # setup kubernetes client config
    aConfiguration = client.Configuration()
    aConfiguration.host = CLUSTER_ENDPOINT
    aConfiguration.verify_ssl = True
    aConfiguration.ssl_ca_cert = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    aConfiguration.api_key = {"authorization": "Bearer " + BEARER_TOKEN}
    aApiClient = client.ApiClient(aConfiguration)
    v1 = client.CoreV1Api(aApiClient)

    # fetch namespaces with label=LABEL_SELECTOR else fetch all namespaces
    if LABEL_SELECTOR:
        namespaces = v1.list_namespace(label_selector=LABEL_SELECTOR, async_req=False, watch=False)
    else:
        namespaces = v1.list_namespace(async_req=False, watch=False)

    # loop through each namespace
    for namespace in namespaces.items:
        superseded_secrets = []
        secrets = v1.list_namespaced_secret(namespace.metadata.name, field_selector=SECRET_TYPE)

        #determine all helm app release names
        appnames = []
        for secret in secrets.items:
            if secret.metadata.labels['status'] == "superseded":
                if secret.metadata.labels["name"] not in appnames:
                    appnames.append(secret.metadata.labels["name"])

        # cycle through secrets by app release - removing all but the youngest per release
        for appname in appnames:
            superseded_secrets = []
            for secret in secrets.items:
                if secret.metadata.labels['status'] == "superseded" and secret.metadata.labels["name"] == appname:
                    secret_doc = {
                        "fullname": secret.metadata.name,
                        "resource_version": int(secret.metadata.resource_version)
                    }
                    superseded_secrets.append(secret_doc)

            # sort secrets by resource version (age)
            sorted_superseded_secrets = sorted(superseded_secrets, key=lambda x:(x['resource_version']), reverse=False)

            # if more than 2 secrets exist for a release, remove all but the last 1
            if len(sorted_superseded_secrets) >= 2:
                for i in range(0, len(sorted_superseded_secrets)-1):
                    if DRYRUN.lower() != "true":
                        print("Deleting: %s/%s" % (namespace.metadata.name,sorted_superseded_secrets[i]['fullname']))
                        v1.delete_namespaced_secret(sorted_superseded_secrets[i]['fullname'],namespace.metadata.name)
                        time.sleep(2)
                    else:
                        print("Dry-run: would delete: %s/%s" % (namespace.metadata.name,sorted_superseded_secrets[i]['fullname']))

if __name__ == "__main__":
    main()
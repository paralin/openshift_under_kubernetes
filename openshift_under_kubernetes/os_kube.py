import os
import pykube
import requests

from pykube.config import KubeConfig
from pykube.http import HTTPClient
from pykube.objects import Pod, Namespace, Service, ReplicationController, Secret

'''
Deploys OpenShift to Kubernetes
'''
class OpenshiftKubeDeployer:
    def __init__(self, config_path, context_override, enable_secure):
        self.config_path = config_path
        self.context_override = context_override
        self.enable_secure = enable_secure
        pass
    def load_and_check_config(self):
        if not os.path.exists(self.config_path):
            print("Config does not exist at path " + self.config_path + "!")
            return False
        try:
            self.config = KubeConfig.from_file(self.config_path)
        except:
            print("Config at path " + self.config_path + " failed to validate!")
            return False
        # Check current context
        if self.context_override != None:
            if self.context_override not in self.config.contexts:
                print("Context override " + self.context_override + " not in list of contexts.")
                return False
            self.config.set_current_context(self.context_override)
        elif self.config.current_context == None:
            print("Context not set, not sure which to use.")
            return False

        curr_ctx = self.config.contexts[self.config.current_context]
        self.api = HTTPClient(self.config)
        if not self.enable_secure:
            print('[note] we are in insecure mode, disabling warnings')
            requests.packages.urllib3.disable_warnings()
            self.api.session.verify = False
        return True

    def fetch_namespaces(self):
        self.namespace_list = Namespace.objects(self.api).all().response["items"]
        print("Currently there are " + str(len(self.namespace_list)) + " namespaces in the cluster.")
        if len(self.namespace_list) <= 0:
            return False
        self.namespace_names = []
        for ns in self.namespace_list:
            self.namespace_names.append(ns["metadata"]["name"])
        return True

    def fetch_openshift_setup(self):
        # Check if we have the openshift namespaces
        self.has_openshift_ns = "openshift-origin" in self.namespace_names
        # Check the replication controller
        try:
            self.openshift_rc = ReplicationController.objects(self.api).filter(namespace="openshift-origin", selector={"name": "openshift"}).get()
        except:
            self.openshift_rc = None
        self.consider_openshift_deployed = self.has_openshift_ns and self.openshift_rc != None

    def print_openshift_basic_status(kube_deployer):
        print("It looks like we " + ("do" if kube_deployer.has_openshift_ns else "do not") + " have the openshift-origin namespace, and " + ("do" if kube_deployer.openshift_rc != None else "do not") + " have a working ReplicationController.")
        print("Currently I " + ("do" if kube_deployer.consider_openshift_deployed else "do not") + " consider this a complete OpenShift deployment.")

    def fetch_info(self, skip_namespaces=False):
        if not skip_namespaces:
            self.fetch_namespaces()
        self.fetch_openshift_setup()

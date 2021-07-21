import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from cache_service import CRMProjects, CRMProjectIam, CRMFolders, CRMFolderIam, ServiceAccountService, \
    ServiceAccountKeyService, BQDataset, BQDatasets, GCSBuckets, GCSBucketACL, \
    ServiceManagement

class GcpIamIterator:
    def __init__(self, use_cache=True):
        credentials = GoogleCredentials.get_application_default()
        google_crm_service = build('cloudresourcemanager', 'v1',
                                   credentials=credentials)
        google_crm_service_v2 = build('cloudresourcemanager', 'v2',
                                   credentials=credentials)
        google_iam_service = build('iam', 'v1', credentials=credentials)
        google_bq_service = build('bigquery', 'v2', credentials=credentials)
        google_gcs_service = build('storage', 'v1', credentials=credentials)
        google_service_management = build('servicemanagement', 'v1',
                                          credentials=credentials)
        self.crm_service = CRMProjects(google_crm_service, use_cache)
        self.crm_iam_service = CRMProjectIam(google_crm_service, use_cache)
        self.crm_folders_service = CRMFolders(google_crm_service_v2, use_cache)
        self.crm_folders_iam_service = CRMFolderIam(google_crm_service_v2, use_cache)
        self.sa_service = ServiceAccountService(google_iam_service, use_cache)
        self.sak_service = ServiceAccountKeyService(google_iam_service,
                                                    use_cache)
        self.datasets_service = BQDatasets(google_bq_service, use_cache)
        self.dataset_iam_service = BQDataset(google_bq_service, use_cache)
        self.gcs_service = GCSBuckets(google_gcs_service, use_cache)
        self.gcs_acl_service = GCSBucketACL(google_gcs_service, use_cache)
        self.service_management = ServiceManagement(google_service_management,
                                                    use_cache)

    def list_projects(self):
        response = self.crm_service.get()

        projects = []

        while response:
            for project in response['projects']:
                if len(projects) == 0:
                    yield project
                    continue

                for requestedProject in projects:
                    if project['projectId'] == requestedProject:
                        yield project

            if 'nextPageToken' in response:
                response = self.crm_service.get(
                    nextPageToken=response['nextPageToken'])
            else:
                response = None

    def list_folders(self, parent):
        response = self.crm_folders_service.get(parent=parent)

        while response:
            for folder in response['folders']:
                yield folder

            if 'nextPageToken' in response:
                response = self.crm_folders_service.get(
                    nextPageToken=response['nextPageToken'])
            else:
                response = None

    def list_nested_folders(self, folders_list, parent):
        folders = []
        folders_map = {}
        folders_to_fetch = []

        # Create a map of folders and nested folders
        for folder in folders_list:
            if folder['name'] not in folders_map:
                folders_map[folder['name']] = []
            if folder['parent'] not in folders_map:
                folders_map[folder['parent']] = []

            folders_map[folder['parent']].append(folder['name'])

        children = [parent]

        # Create a flat list of all desired folders
        hasChildren = True
        while hasChildren is True:
            if not children:
                hasChildren = False
                break

            parent = children[0]
            folders_to_fetch.append(parent)

            for child in folders_map[parent]:
                children.append(child)
                folders_to_fetch.append(child)

            children.remove(parent)

        folders_to_fetch = list(dict.fromkeys(folders_to_fetch))

        for folder in folders_list:
            if folder['name'] in folders_to_fetch:
                folders.append(folder)

        return folders

    def list_folder_iam(self, folder_id):
        try:
            iam_policy = self.crm_folders_iam_service.get(folder_id=folder_id)
        except HttpError as e:
            if e.resp.status == 403:
                logging.warning("403 received for folder_id: {0}, content: {1}"
                                .format(folder_id, e.content))
                return
            else:
                raise e

        if 'bindings' in iam_policy:
            for binding in iam_policy['bindings']:
                yield binding

    def list_projects_in_folders(self, all_projects, folders):
        projects = []
        for project in all_projects:
            parent = project['parent']['type'] + "s/" + project['parent']['id']
            for folder in folders:
                if parent == folder['name']:
                    projects.append(project)

        return projects

    def list_project_iam(self, project_id):
        try:
            iam_policy = self.crm_iam_service.get(project_id=project_id)
        except HttpError as e:
            if e.resp.status == 403:
                logging.warning("403 received for project_id: {0}, content: {1}"
                                .format(project_id, e.content))
                return
            else:
                raise e

        if 'bindings' in iam_policy:
            for binding in iam_policy['bindings']:
                yield binding

    def list_service_accounts(self, project_id):
        try:
            response = self.sa_service.get(project_id=project_id)
        except HttpError as e:
            if e.resp.status == 404:
                logging.info("404 received for project_id: {0}, content: {1}"
                             .format(project_id, e.content))
                return
            elif e.resp.status == 403:
                logging.warning("403 received for project_id: {0}, content: {1}"
                                .format(project_id, e.content))
                return
            else:
                raise e

        while response:
            for account in response['accounts']:
                yield account

            if 'nextPageToken' in response:
                response = self.sa_service \
                    .get(project_id=project_id,
                         nextPageToken=response['nextPageToken'])
            else:
                response = None

    def list_service_account_keys(self, email):
        response = self.sak_service.get(email=email)

        if 'keys' in response:
            for key in response['keys']:
                yield key

    def list_datasets(self, project_id):
        response = None
        try:
            response = self.datasets_service.get(project_id=project_id)
        except HttpError as e:
            if e.resp.status == 400:
                logging.warning("400 received for project_id: {0}, content: {1}"
                                .format(project_id, e.content))
                return

        while response:
            if 'datasets' in response:
                for dataset in response['datasets']:
                    yield dataset

            if 'nextPageToken' in response:
                response = self.datasets_service.get(project_id=project_id,
                                                     pageToken=response[
                                                         'nextPageToken'])
            else:
                response = None

    def list_dataset_access(self, project_id, dataset_id):
        response = self.dataset_iam_service.get(project_id=project_id,
                                                dataset_id=dataset_id)
        if 'access' in response:
            for access in response['access']:
                yield access

    def list_buckets(self, project_id):
        try:
            response = self.gcs_service.get(project_id=project_id)
        except HttpError as e:
            if e.resp.status == 400:
                logging.warning(
                    "400 received during listing buckets for project_id: {0}, "
                    "content: {1}".format(project_id, e.content))
                return
            elif e.resp.status == 403:
                logging.warning(
                    "403 received during listing buckets for project_id: {0}, "
                    "content: {1}".format(project_id, e.content))
                return
            else:
                raise e

        while response:
            if 'items' in response:
                for bucket in response['items']:
                    yield bucket

            if 'nextPageToken' in response:
                response = self.gcs_service.get(project_id=project_id,
                                                pageToken=response[
                                                    'nextPageToken'])
            else:
                response = None

    def list_bucket_access(self, bucket_id):
        try:
            response = self.gcs_acl_service.get(bucket_id=bucket_id)
        except HttpError as e:
            if e.resp.status == 403:
                logging.warning("403 received for bucket_id: {0}, content: {1}"
                                .format(bucket_id, e.content))
                return
            else:
                raise e

        for item in response['items']:
            yield item

    def list_enabled_services(self, project_id):
        try:
            response = self.service_management.get(project_id=project_id)
        except HttpError as e:
            if e.resp.status == 400 or e.resp.status == 403 \
                    or e.resp.status == 404:
                logging.warning(
                    "{0} received during listing services for project_id: {1}, "
                    "content: {2}".format(e.resp.status, project_id, e.content))
                return
            else:
                raise e

        while response:
            if 'services' in response:
                for service in response['services']:
                    yield service

            if 'nextPageToken' in response:
                response = self.service_management.get(project_id=project_id,
                                                       pageToken=response[
                                                           'nextPageToken'])
            else:
                response = None

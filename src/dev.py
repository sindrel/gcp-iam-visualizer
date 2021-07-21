import logging
import sys

from gcp_iam_iterator import GcpIamIterator
from visualization.graph import Node, Edge
from visualization import template_renderer

logging.basicConfig(
    format='%(asctime)s %(levelname)-5s %(filename)-12s %(message)s',
    level=logging.DEBUG, stream=sys.stdout)

if __name__ == '__main__':
    print("Starting")

    parent = "folders/2348"

    iam_iterator = GcpIamIterator(use_cache=False)

    all_folders = list(iam_iterator.list_folders())
    all_projects = list(iam_iterator.list_projects())

    folders = list(iam_iterator.list_nested_folders(folders_list=all_folders, parent=parent))
    projects = list(iam_iterator.list_projects_in_folders(all_projects=all_projects, folders=folders))

    print(projects)

    print("Done")
    
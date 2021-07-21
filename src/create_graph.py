import logging
import sys

from gcp_iam_iterator import GcpIamIterator
from visualization.graph import Node, Edge
from visualization import template_renderer

logging.basicConfig(
    format='%(asctime)s %(levelname)-5s %(filename)-12s %(message)s',
    level=logging.DEBUG, stream=sys.stdout)

def create_graph(iam_iterator, projects, folders):
    nodes = {}
    edges = []
    folder_nodes = {}
    
    # Get folders and folder IAM
    for counter, folder in enumerate(folders):
        folder_id = folder['name']

        logging.info("Parsing folder [{0}] with ID {1}"
                     .format(counter, folder_id))
        folder_node = Node("folder", "f:" + folder_id, folder['displayName'], properties={'name': folder['displayName']})
        nodes[folder_node.id] = folder_node
        folder_nodes[folder_id] = folder_node.id

        for binding in iam_iterator.list_folder_iam(folder_id):
            role = binding['role']
            for member in binding['members']:
                member_type = member.split(":")[0]
                member_name = member.split(":")[1]

                user_node = Node(member_type, member_name,
                                member_name,
                                properties={'email': member_name})
                edges.append(Edge(user_node, folder_node, role=role))
                nodes[user_node.id] = user_node

    # Connect folder to parent folder node
    for counter, folder in enumerate(folders):
        folder_id = folder['name']

        if folder['parent'] in folder_nodes:
            edges.append(Edge(nodes[folder_nodes[folder['parent']]], nodes[folder_nodes[folder_id]], role="folder_connection"))

    # Get projects and project IAM
    for counter, project in enumerate(projects):
        project_id = project['projectId']

        logging.info("Parsing project [{0}] with ID: {1}"
                     .format(counter, project_id))

        project_properties = {k: v for k, v in project.items() if
                              k in ['projectNumber', 'name', 'createTime',
                                    'projectId']}

        project_node = Node("project", "p:" + project_id, project_id,
                             properties=project_properties)
        nodes[project_node.id] = project_node

        for binding in iam_iterator.list_project_iam(project_id):
            role = binding['role']
            for member in binding['members']:
                member_type = member.split(":")[0]
                member_name = member.split(":")[1]

                if member_type == "deleted":
                    member_type = member.split(":")[1]
                    member_name = "deleted:" + member.split(":")[2]

                if member_name.endswith("@cloudservices.gserviceaccount.com"):
                    logging.debug("Ignoring Google APIs Service Agent service account " + member_name)
                    continue

                user_node = Node(member_type, member_name,
                                member_name,
                                properties={'email': member_name})
                edges.append(Edge(user_node, project_node, role=role))
                nodes[user_node.id] = user_node

        # Connect project to parent folder node
        if project['parent']['type'] == "folder" and "folders/" + project['parent']['id'] in folder_nodes:
            logging.debug("Parent folder found!")
            edges.append(Edge(nodes[folder_nodes["folders/" + project['parent']['id']]], project_node, role="folder_connection"))

    return nodes.values(), edges

# Main routine
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Arguments missing")
        print(f"Usage: {sys.argv[0]} <scope> <output>")
        print(f"Example: {sys.argv[0]} 'folders/2837234232' graph.html")
        exit(1)

    parent = sys.argv[1]
    output = sys.argv[2]

    print("Scope set to: " + parent)
    print("Output path: " + output)

    iam_iterator = GcpIamIterator(use_cache=False)

    # Fetch all projects and folders
    all_projects = list(iam_iterator.list_projects())
    all_folders = list(iam_iterator.list_folders(parent=parent))

    # Filter folders and projects
    folders = list(iam_iterator.list_nested_folders(folders_list=all_folders, parent=parent))
    projects = list(iam_iterator.list_projects_in_folders(all_projects=all_projects, folders=folders))

    # Construct graph
    nodes, edges = create_graph(iam_iterator, projects=projects, folders=folders)

    # Output to file (.html)
    template_renderer.render(nodes, edges, output)

    print("Output saved to: " + output)
    print("Done")

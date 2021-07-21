import json
import random

from jinja2 import Environment, PackageLoader
from visualization import graph

def create_html(nodes_string, edges_string, role_color_map, output_name, nodes):
    env = Environment(loader=PackageLoader('visualization', '.'))
    template = env.get_template('visualization.template')

    default_type_filters = []
    labels = []
    projects = []
    users = []
    groups = []
    serviceAccounts = []

    for type in graph.type_properties:
        if graph.type_properties[type]['default']:
            default_type_filters.append(type)

    for node in nodes:
        if node.name:
            labels.append(node.name)
        if node.node_type == "project":
            projects.append(node.name)
        if node.node_type == "user":
            users.append(node.name)
        if node.node_type == "group":
            groups.append(node.name)
        if node.node_type == "serviceAccount":
            serviceAccounts.append(node.name)

    html = template.render(nodes_string=nodes_string,
                           edges_string=edges_string,
                           type_properties=graph.type_properties,
                           default_type_filters=default_type_filters,
                           labels=sorted(labels),
                           projects=sorted(projects),
                           users=sorted(users),
                           groups=sorted(groups),
                           serviceAccounts=sorted(serviceAccounts),
                           all_roles_list=sorted(list(role_color_map.keys())),
                           all_roles=role_color_map)
    with open(output_name, "w+") as resource_file:
        resource_file.write(html)

def get_description(node):
    desc = node.get_type_name() + "</br>"
    if node.title:
        desc = desc + node.title + "</br>"
    if node.properties:
        for k, v in node.properties.items():
            desc = desc + k + ": " + str(v) + "<br/>"
    return desc

def render(nodes, edges, output_name):
    color_map = roles_to_color_map(edges=edges)
    formatted_nodes, formatted_edges = format_graph(nodes, edges, color_map)
    nodes_string = ",".join(formatted_nodes)
    edges_string = ",".join(formatted_edges)

    create_html(nodes_string, edges_string, color_map, output_name, nodes)

def color_for_role(role, all_roles):
    if role == "folder_connection":
        return '#EA4335'

    if role == "owner":
        return "#ff4000"

    if role == "editor":
        return "#333333"

    random_int = random.randint(0,16777215)
    hex_color = str(hex(random_int))
    hex_color ='#'+ hex_color[2:]
    return hex_color

def sanitize_role(role):
    return str(role).replace('roles/', '') \
        .lower() \
        .replace('writer', 'editor') \
        .replace('reader', 'viewer')

def roles_to_color_map(edges):
    all_roles = list({sanitize_role(e.role) for e in edges if e.role})
    role_map = {}
    for role in all_roles:
        role_map[role] = color_for_role(role, all_roles)
    role_map['other'] = '#00c0ff'
    return role_map

def format_graph(nodes, edges, role_color_map):
    nodes_string = []
    node_ids = {}

    for counter, node in enumerate(nodes):
        #print("node name: " + node.name)
        #print("node node_type: " + node.node_type)

        node_ids[node.id] = counter
        value = {
            'id': counter,
            'shape': 'icon',
            'label': node.name,
            'type': node.node_type,
            'icon': {
                'face': 'FontAwesome',
                'code': node.get_font_code(),
                'size': node.get_size(),
                'color': node.get_color()
            }
        }
        description = get_description(node)
        if description:
            value['title'] = description
        nodes_string.append(json.dumps(value).replace("\\\\", "\\"))

    edges_string = []

    for edge in edges:
        value = {
            'from': node_ids[edge.node_from.id],
            'to': node_ids[edge.node_to.id],
            'arrows': 'to',
        }
        if edge.label:
            value['label'] = edge.label
        if edge.title:
            value['title'] = edge.title
        if edge.role:
            value['type'] = "role"
        value['role'] = sanitize_role(edge.role) if edge.role else 'other'
        value['color'] = role_color_map[value['role']]
        edges_string.append(json.dumps(value))

    return nodes_string, edges_string

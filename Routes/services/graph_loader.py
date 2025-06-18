from collections import defaultdict
from Routes.models import RouteEdge

route_graphs = defaultdict(dict)    # route_id -> {node_id: [(neighbor_node_id, distance)]}
node_routes = defaultdict(set)      # node_id -> set(route_ids)

_loaded = False

def build_graphs():
    global _loaded
    if _loaded:
        return
    print("Construyendo grafos de rutas...")
    for route_edge in RouteEdge.objects.select_related('edge', 'route'):
        edge = route_edge.edge
        route_id = route_edge.route_id

        route_graphs[route_id].setdefault(edge.source_id, []).append((edge.target_id, edge.distance))
        node_routes[edge.source_id].add(route_id)
        node_routes[edge.target_id].add(route_id)

    _loaded = True
    print("Rutas cargadas:", len(route_graphs))

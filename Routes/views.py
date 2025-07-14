import networkx as nx
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from rest_framework.views import APIView
from rest_framework.response import Response
from Nodes.models import Node, Edge
from Routes.models import Route, RouteEdge

# Ajusta estos parámetros según tu preferencia
WALK_PENALTY = 2.5        # Caminata vale 2.5x metros respecto a ir en bus
TRANSFER_PENALTY = 800    # Penalización fija por cambio de bus o de modo, en "metros virtuales"
MAX_ROUTE_CANDIDATES = 6  # Busca hasta 6 rutas candidatas

graph_cache = None

def get_nearest_node(lat, lng, max_distance=400):
    user_point = Point(lng, lat, srid=4326)
    nearby_nodes = Node.objects.filter(
        location__distance_lte=(user_point, D(m=max_distance))
    ).annotate(
        distance=Distance('location', user_point)
    ).order_by('distance')
    return nearby_nodes.first()

def build_transport_graph():
    G = nx.DiGraph()

    # 1. Nodos
    for node in Node.objects.all():
        G.add_node(node.id, osm_id=node.osm_id, location=node.location)

    # 2. Edges de caminata (calles), en ambos sentidos y penalizados
    for edge in Edge.objects.all():
        G.add_edge(
            edge.source_id,
            edge.target_id,
            weight=edge.distance * WALK_PENALTY,
            type='walk'
        )
        G.add_edge(
            edge.target_id,
            edge.source_id,
            weight=edge.distance * WALK_PENALTY,
            type='walk'
        )

    # 3. Edges de bus (solo según sentido del RouteEdge)
    for route_edge in RouteEdge.objects.select_related('edge', 'route'):
        edge = route_edge.edge
        G.add_edge(
            edge.source_id,
            edge.target_id,
            weight=edge.distance,
            type='bus',
            route_id=route_edge.route_id,
            route_name=route_edge.route.name,
            direction=route_edge.direction,
            order=route_edge.order
        )
    return G

def describe_path(G, path):
    steps = []
    current_mode = None
    current_route = None
    current_direction = None
    segment = []
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge_data = G.get_edge_data(u, v)
        mode = edge_data.get('type')
        route = edge_data.get('route_id')
        direction = edge_data.get('direction')
        step = {
            "from_node": u,
            "to_node": v,
            "mode": mode,
            "route_id": route,
            "route_name": edge_data.get('route_name'),
            "direction": direction,
            "distance": edge_data.get('weight')
        }
        # Agrupa por modo/ruta/dirección
        if mode != current_mode or route != current_route or direction != current_direction:
            if segment:
                steps.append(segment)
            segment = [step]
            current_mode = mode
            current_route = route
            current_direction = direction
        else:
            segment.append(step)
    if segment:
        steps.append(segment)
    return steps

def count_bus_segments(G, path):
    """Cuenta cuántos segmentos de bus diferentes hay en el path."""
    last_route = None
    last_mode = None
    bus_segments = 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge_data = G.get_edge_data(u, v)
        mode = edge_data.get('type')
        route = edge_data.get('route_id')
        if mode == "bus":
            if route != last_route or mode != last_mode:
                bus_segments += 1
        last_route = route
        last_mode = mode
    return bus_segments

def step_instructions(segment, node_objs):
    first = segment[0]
    last = segment[-1]
    if first["mode"] == "walk":
        return f"Camina {int(sum(step['distance'] / WALK_PENALTY for step in segment))} metros desde ({node_objs[first['from_node']].location.y}, {node_objs[first['from_node']].location.x}) hasta ({node_objs[last['to_node']].location.y}, {node_objs[last['to_node']].location.x})"
    elif first["mode"] == "bus":
        return (
            f"Sube al bus {first['route_name']} (ID {first['route_id']}) dirección {'ida' if first['direction']=='I' else 'vuelta'} "
            f"desde ({node_objs[first['from_node']].location.y}, {node_objs[first['from_node']].location.x}) "
            f"y bájate en ({node_objs[last['to_node']].location.y}, {node_objs[last['to_node']].location.x})"
        )
    else:
        return "Sigue la ruta"

def penalized_path_length(G, path):
    length = 0
    last_mode = None
    last_route = None
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge_data = G.get_edge_data(u, v)
        length += edge_data['weight']
        mode = edge_data.get('type')
        route = edge_data.get('route_id')
        # Penaliza cada vez que cambias de bus o de caminata a bus (y viceversa)
        if last_mode is not None and (mode != last_mode or (mode == 'bus' and route != last_route)):
            length += TRANSFER_PENALTY
        last_mode = mode
        last_route = route
    return length

def find_best_route_with_penalty(G, start_id, end_id, max_candidates=MAX_ROUTE_CANDIDATES):
    try:
        candidates = nx.shortest_simple_paths(G, start_id, end_id, weight='weight')
        best = None
        best_score = float('inf')
        count = 0
        for path in candidates:
            score = penalized_path_length(G, path)
            if score < best_score:
                best = path
                best_score = score
            count += 1
            if count >= max_candidates:
                break
        return best
    except Exception:
        return None
def find_best_direct_route(G, start_node, end_node):
    """
    Busca la mejor ruta directa (un solo bus), aunque implique caminata al inicio o fin.
    """
    # 1. Encuentra todas las rutas de bus que pasen cerca de ambos nodos
    from Routes.models import RouteNode

    # Todos los RouteNode de subida cerca del inicio
    start_routenodes = RouteNode.objects.filter(
        node=start_node
    ).select_related('route')
    # Todos los RouteNode de bajada cerca del destino
    end_routenodes = RouteNode.objects.filter(
        node=end_node
    ).select_related('route')

    direct_candidates = []
    for s in start_routenodes:
        for e in end_routenodes:
            if (
                s.route_id == e.route_id and
                s.direction == e.direction and
                s.order < e.order
            ):
                direct_candidates.append((s, e))
    if not direct_candidates:
        return None

    # 2. Elige la ruta directa con menor distancia de bus
    best = None
    best_dist = float('inf')
    for s, e in direct_candidates:
        # Busca el path real entre los dos RouteNodes usando solo los edges de ese route y direction
        # Crea un subgrafo solo para esa ruta y sentido
        bus_edges = [
            (re.edge.source_id, re.edge.target_id, re.edge.distance)
            for re in RouteEdge.objects.filter(route=s.route, direction=s.direction)
        ]
        bus_G = nx.DiGraph()
        for u, v, d in bus_edges:
            bus_G.add_edge(u, v, weight=d)
        try:
            bus_path = nx.shortest_path(bus_G, s.node_id, e.node_id, weight='weight')
            bus_dist = nx.shortest_path_length(bus_G, s.node_id, e.node_id, weight='weight')
        except nx.NetworkXNoPath:
            continue

        # Caminata desde start_node real a s.node (si es distinto)
        walk_dist_start = 0 if s.node_id == start_node.id else G.get_edge_data(start_node.id, s.node_id, {}).get('weight', float('inf'))
        # Caminata desde e.node al destino real
        walk_dist_end = 0 if e.node_id == end_node.id else G.get_edge_data(e.node_id, end_node.id, {}).get('weight', float('inf'))
        total_walk = (walk_dist_start + walk_dist_end) / WALK_PENALTY

        # Penalización si el paradero está lejos (opcional: puedes poner un máximo)
        total_score = bus_dist + (walk_dist_start + walk_dist_end)
        if total_score < best_dist:
            best = {
                "route": s.route,
                "direction": s.direction,
                "bus_path": bus_path,
                "bus_dist": bus_dist,
                "start_walk": (start_node.id, s.node_id, walk_dist_start / WALK_PENALTY),
                "end_walk": (e.node_id, end_node.id, walk_dist_end / WALK_PENALTY),
                "total_walk": total_walk,
                "total_score": total_score
            }
            best_dist = total_score
    return best

class OptimalRouteView(APIView):
    """
    Devuelve ruta óptima, priorizando rutas directas de bus.
    """
    def post(self, request):
        global graph_cache
        lat1 = request.data.get("lat1")
        long1 = request.data.get("long1")
        lat2 = request.data.get("lat2")
        long2 = request.data.get("long2")

        try:
            lat1, long1 = float(lat1), float(long1)
            lat2, long2 = float(lat2), float(long2)
        except (TypeError, ValueError):
            return Response({"error": "Coordenadas inválidas"}, status=400)

        if graph_cache is None:
            graph_cache = build_transport_graph()
        G = graph_cache

        # Nodos más cercanos
        start_node = get_nearest_node(lat1, long1)
        end_node = get_nearest_node(lat2, long2)
        if not start_node or not end_node:
            return Response({"error": "No se encontraron nodos cercanos."}, status=404)

        # 1. Intenta ruta directa
        direct = find_best_direct_route(G, start_node, end_node)
        if direct:
            # Arma la respuesta tipo steps + polyline
            node_objs = Node.objects.in_bulk(
                [n for n in direct["bus_path"]] +
                [direct["start_walk"][0], direct["start_walk"][1], direct["end_walk"][0], direct["end_walk"][1]]
            )
            polyline = []

            # Caminata inicio
            walk_init = []
            if direct["start_walk"][2] > 0 and direct["start_walk"][0] != direct["start_walk"][1]:
                walk_init = [node_objs[direct["start_walk"][0]], node_objs[direct["start_walk"][1]]]
                polyline += [
                    {"lat": walk_init[0].location.y, "lng": walk_init[0].location.x},
                    {"lat": walk_init[1].location.y, "lng": walk_init[1].location.x}
                ]
            # Bus
            bus_coords = [
                {"lat": node_objs[nid].location.y, "lng": node_objs[nid].location.x}
                for nid in direct["bus_path"]
            ]
            polyline += bus_coords

            # Caminata final
            walk_end = []
            if direct["end_walk"][2] > 0 and direct["end_walk"][0] != direct["end_walk"][1]:
                walk_end = [node_objs[direct["end_walk"][0]], node_objs[direct["end_walk"][1]]]
                polyline += [
                    {"lat": walk_end[0].location.y, "lng": walk_end[0].location.x},
                    {"lat": walk_end[1].location.y, "lng": walk_end[1].location.x}
                ]

            # Steps
            steps = []
            if walk_init:
                steps.append({
                    "type": "walk",
                    "from": {"lat": walk_init[0].location.y, "lng": walk_init[0].location.x},
                    "to": {"lat": walk_init[1].location.y, "lng": walk_init[1].location.x},
                    "distance": int(direct["start_walk"][2]),
                    "instructions": "Camina hasta el paradero de subida"
                })
            steps.append({
                "type": "bus",
                "route_id": direct["route"].id,
                "route_name": direct["route"].name,
                "direction": direct["direction"],
                "from": {"lat": node_objs[direct["bus_path"][0]].location.y, "lng": node_objs[direct["bus_path"][0]].location.x},
                "to": {"lat": node_objs[direct["bus_path"][-1]].location.y, "lng": node_objs[direct["bus_path"][-1]].location.x},
                "distance": int(direct["bus_dist"]),
                "instructions": f"Sube al bus {direct['route'].name} y bájate en la parada más cercana a tu destino"
            })
            if walk_end:
                steps.append({
                    "type": "walk",
                    "from": {"lat": walk_end[0].location.y, "lng": walk_end[0].location.x},
                    "to": {"lat": walk_end[1].location.y, "lng": walk_end[1].location.x},
                    "distance": int(direct["end_walk"][2]),
                    "instructions": "Camina hasta tu destino final"
                })

            return Response({
                "direct_route": True,
                "start_node": {
                    "id": start_node.id,
                    "osm_id": start_node.osm_id,
                    "lat": start_node.location.y,
                    "lng": start_node.location.x
                },
                "end_node": {
                    "id": end_node.id,
                    "osm_id": end_node.osm_id,
                    "lat": end_node.location.y,
                    "lng": end_node.location.x
                },
                "polyline": polyline,
                "steps": steps,
                "summary": {
                    "total_walk_m": int(direct["total_walk"]),
                    "total_bus_m": int(direct["bus_dist"]),
                    "total_transfers": 0
                }
            })

        # 2. Si no hay ruta directa, usa la lógica multimodal penalizada (como antes)
        path = find_best_route_with_penalty(G, start_node.id, end_node.id)
        if not path:
            return Response({"error": "No se encontró ruta disponible entre los puntos."}, status=404)
        node_objs = Node.objects.in_bulk(path)
        polyline = [{"lat": node_objs[nid].location.y, "lng": node_objs[nid].location.x} for nid in path]
        steps = describe_path(G, path)
        steps_list = []
        total_walk = 0
        total_bus = 0
        for segment in steps:
            first = segment[0]
            last = segment[-1]
            segment_distance = sum(step["distance"] for step in segment)
            if first["mode"] == "walk":
                total_walk += segment_distance / WALK_PENALTY
            else:
                total_bus += segment_distance
            steps_list.append({
                "type": first["mode"],
                "route_id": first.get("route_id"),
                "route_name": first.get("route_name"),
                "direction": first.get("direction"),
                "from": {
                    "lat": node_objs[first["from_node"]].location.y,
                    "lng": node_objs[first["from_node"]].location.x,
                },
                "to": {
                    "lat": node_objs[last["to_node"]].location.y,
                    "lng": node_objs[last["to_node"]].location.x,
                },
                "distance": int(segment_distance if first["mode"] == "bus" else segment_distance / WALK_PENALTY),
                "instructions": step_instructions(segment, node_objs)
            })

        return Response({
            "direct_route": False,
            "start_node": {
                "id": start_node.id,
                "osm_id": start_node.osm_id,
                "lat": start_node.location.y,
                "lng": start_node.location.x
            },
            "end_node": {
                "id": end_node.id,
                "osm_id": end_node.osm_id,
                "lat": end_node.location.y,
                "lng": end_node.location.x
            },
            "polyline": polyline,
            "steps": steps_list,
            "summary": {
                "total_distance_m": int(total_walk + total_bus),
                "total_walk_m": int(total_walk),
                "total_bus_m": int(total_bus),
                "total_transfers": sum(1 for i in range(1, len(steps)) if steps[i][0]["mode"] != steps[i-1][0]["mode"] or (steps[i][0]["mode"] == "bus" and steps[i][0]["route_id"] != steps[i-1][0]["route_id"]))
            }
        })

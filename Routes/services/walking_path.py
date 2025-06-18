import networkx as nx
from Nodes.models import Node, Edge
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

def find_nearest_node(lat, lng, max_distance=500):
    point = Point(lng, lat, srid=4326)
    return Node.objects.filter(
        location__distance_lte=(point, D(m=max_distance))
    ).annotate(
        distance=Distance('location', point)
    ).order_by('distance').first()

def compute_walking_path(graph, start_coord, end_node):
    # Encuentra nodo más cercano al punto de inicio
    origin_node = find_nearest_node(start_coord[0], start_coord[1])
    if not origin_node:
        return None, None

    # Usa el grafo para calcular camino peatonal
    try:
        path = nx.shortest_path(graph, origin_node.osm_id, end_node.osm_id, weight='weight')
        distance = nx.shortest_path_length(graph, origin_node.osm_id, end_node.osm_id, weight='weight')
        return path, distance
    except Exception:
        return None, None

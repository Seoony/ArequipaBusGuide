import networkx as nx
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Nodes.models import Node, Edge

# Singleton para grafo en memoria
graph_cache = None

def build_graph():
    global graph_cache
    if graph_cache is not None:
        return graph_cache

    G = nx.DiGraph()
    for edge in Edge.objects.select_related('source', 'target').all():
        G.add_edge(
            edge.source_id,
            edge.target_id,
            weight=edge.distance,
            geometry=edge.geometry
        )
    graph_cache = G
    return G

def find_nearest_node(lat, lng, max_distance=400):
    point = Point(lng, lat, srid=4326)
    return Node.objects.filter(
        location__distance_lte=(point, D(m=max_distance))
    ).annotate(
        distance=Distance('location', point)
    ).order_by('distance').first()

class OptimalRouteView(APIView):
    def post(self, request):
        data = request.data
        origin = data.get("origin")
        destination = data.get("destination")

        if not origin or not destination:
            return Response({"error": "origin and destination are required"}, status=400)

        user_start_node = find_nearest_node(origin['lat'], origin['lng'])
        user_end_node = find_nearest_node(destination['lat'], destination['lng'])

        if not user_start_node or not user_end_node:
            return Response({"error": "No nearby bus route found"}, status=404)

        G = build_graph()

        try:
            path = nx.shortest_path(G, user_start_node.id, user_end_node.id, weight='weight')
        except nx.NetworkXNoPath:
            return Response({"error": "No path found"}, status=404)

        return Response({
            "path_node_ids": path,
            "start_node": user_start_node.id,
            "end_node": user_end_node.id
        }, status=200)

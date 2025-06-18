import json
import os
import django
import numpy as np
from scipy.spatial import KDTree

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArequipaBusGuide.settings')
django.setup()

from django.contrib.gis.geos import Point
from Nodes.models import Node

def build_kdtree():
    """
    Carga todos los nodos y construye el KDTree con sus coordenadas.
    """
    all_nodes = list(Node.objects.all())
    coords = [(node.location.y, node.location.x) for node in all_nodes]  # (lat, lng)
    tree = KDTree(coords)
    return tree, all_nodes, coords

def find_closest_node_kdtree(lat, lng, tree, all_nodes, coords, max_distance_m=50):
    """
    Busca el nodo más cercano usando KDTree.
    """
    distance_deg, idx = tree.query((lat, lng))
    distance_meters = distance_deg * 111_000  # Aproximación: ~111 km por grado
    if distance_meters <= max_distance_m:
        return all_nodes[idx]
    return None

def update_route_nodes():
    try:
        # Construir el índice KDTree una vez
        print("Cargando nodos en memoria y construyendo KDTree...")
        tree, all_nodes, coords = build_kdtree()
        print(f"Total de nodos cargados: {len(all_nodes)}")

        # Leer el archivo JSON
        with open('routes_with_coordinates.json', 'r') as f:
            companies_data = json.load(f)

        if not isinstance(companies_data, dict):
            raise ValueError("JSON data must be un diccionario de empresas")

        updated_companies = {}

        for company_name, company_data in companies_data.items():
            print(f"\nProcesando empresa: {company_name}")

            if not isinstance(company_data, dict) or 'routes' not in company_data:
                print(f"Saltando empresa {company_name} - formato inválido")
                continue

            updated_routes = []

            for route in company_data['routes']:
                if not isinstance(route, dict) or 'coordinates' not in route:
                    print("Saltando ruta - formato inválido")
                    continue

                updated_route = route.copy()
                coordinates = route.get('coordinates', {})
                if not isinstance(coordinates, dict):
                    print(f"Saltando ruta por 'coordinates' inválido: {coordinates}")
                    continue

                def process_path(path_name):
                    updated_path = []
                    for node in coordinates.get(path_name, []):
                        if not isinstance(node, dict) or 'lat' not in node or 'lng' not in node:
                            continue
                        closest_node = find_closest_node_kdtree(
                            node['lat'], node['lng'], tree, all_nodes, coords
                        )
                        if closest_node:
                            updated_path.append({
                                'lat': closest_node.location.y,
                                'lng': closest_node.location.x,
                                'osm_id': closest_node.osm_id
                            })
                        else:
                            updated_path.append(node)
                    return updated_path

                updated_route['coordinates']['path1'] = process_path('path1')
                updated_route['coordinates']['path2'] = process_path('path2')
                updated_routes.append(updated_route)

            updated_company = company_data.copy()
            updated_company['routes'] = updated_routes
            updated_companies[company_name] = updated_company

        # Guardar el JSON actualizado
        with open('routes_updated.json', 'w') as f:
            json.dump(updated_companies, f, indent=2)

        print("\n¡Actualización de nodos completada exitosamente!")

    except json.JSONDecodeError as e:
        print(f"Error leyendo el archivo JSON: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    update_route_nodes()

import json

def load_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def remove_duplicate_nodes(path):
    if not path:
        return path
    
    # Initialize result with first node
    result = [path[0]]
    
    # Compare each node with the previous one
    for i in range(1, len(path)):
        current = path[i]
        previous = result[-1]
        
        # Check if current node is different from previous
        if (current['lat'] != previous['lat'] or 
            current['lng'] != previous['lng']):
            result.append(current)
    
    return result

def update_markers_with_path_starts(data):
    # Crear una copia del diccionario original
    result = data.copy()
    
    # Procesar cada empresa
    for empresa in result:
        # Procesar cada ruta de la empresa
        for route in result[empresa]['routes']:
            if 'coordinates' in route:
                # Remove duplicate nodes from path1
                if 'path1' in route['coordinates'] and route['coordinates']['path1']:
                    route['coordinates']['path1'] = remove_duplicate_nodes(route['coordinates']['path1'])
                    # Update first marker with first node of path1
                    if 'markers' in route['coordinates'] and len(route['coordinates']['markers']) > 0:
                        first_path1_node = route['coordinates']['path1'][0]
                        route['coordinates']['markers'][0]['position'] = {
                            'lat': first_path1_node['lat'],
                            'lng': first_path1_node['lng']
                        }
                        # Agregar osm_id solo si existe
                        if 'osm_id' in first_path1_node:
                            route['coordinates']['markers'][0]['position']['osm_id'] = first_path1_node['osm_id']
                
                # Remove duplicate nodes from path2
                if 'path2' in route['coordinates'] and route['coordinates']['path2']:
                    route['coordinates']['path2'] = remove_duplicate_nodes(route['coordinates']['path2'])
                    # Update second marker with first node of path2
                    if 'markers' in route['coordinates'] and len(route['coordinates']['markers']) > 1:
                        first_path2_node = route['coordinates']['path2'][0]
                        route['coordinates']['markers'][1]['position'] = {
                            'lat': first_path2_node['lat'],
                            'lng': first_path2_node['lng']
                        }
                        # Agregar osm_id solo si existe
                        if 'osm_id' in first_path2_node:
                            route['coordinates']['markers'][1]['position']['osm_id'] = first_path2_node['osm_id']
    
    return result

def main():
    # Cargar el archivo JSON
    input_file = 'routes_with_coordinates_updated.json'
    output_file = 'coordinates_updated.json'
    
    try:
        # Cargar datos
        data = load_json_file(input_file)
        
        # Actualizar los markers con los primeros nodos de cada path y eliminar duplicados
        result = update_markers_with_path_starts(data)
        
        # Guardar resultado
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Archivo procesado exitosamente. Resultado guardado en {output_file}")
        
    except Exception as e:
        print(f"Error procesando el archivo: {str(e)}")

if __name__ == "__main__":
    main() 
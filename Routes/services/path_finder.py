import heapq
from .graph_loader import build_graphs, route_graphs, node_routes

def find_routes_with_transfers(origin_id, destination_id, max_paths=2, max_transfers=2):
  build_graphs()

  result_paths = []
  visited = set()
  queue = []
  print(node_routes[origin_id])
  for route_id in node_routes[origin_id]:
    heapq.heappush(queue, (0, 0, origin_id, route_id, [(origin_id, route_id)]))

  while queue and len(result_paths) < max_paths:
    transfers, cost, current_node, current_route, path = heapq.heappop(queue)
    state_id = (current_node, current_route)
    if state_id in visited:
      continue
    visited.add(state_id)

    if current_node == destination_id:
      result_paths.append({
        "path": path,
        "transfers": transfers,
        "total_cost": cost
      })
      continue

    neighbors = route_graphs[current_route].get(current_node, [])
    for next_node, dist in neighbors:
      heapq.heappush(queue, (
        transfers,
        cost + dist,
        next_node,
        current_route,
        path + [(next_node, current_route)]
      ))

    if transfers < max_transfers:
      for alt_route in node_routes[current_node]:
        if alt_route != current_route:
          heapq.heappush(queue, (
            transfers + 1,
            cost,
            current_node,
            alt_route,
            path
          ))

  return result_paths

from django.db import models
from Nodes.models import Node, Edge

# Create your models here.
class TransportCompany(models.Model):
  name = models.CharField(max_length=255, unique=True)
  business_url = models.URLField()
  
  class Meta:
    db_table = 'transport_companies'

  def __str__(self):
    return self.name
    

class Route(models.Model):
  company = models.ForeignKey(TransportCompany, on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  route_url = models.URLField()
  start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='routes_start')
  end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='routes_end')
  
  # Route descriptions for both directions
  forward_description = models.TextField(blank=True, null=True)  # For "ida" direction
  return_description = models.TextField(blank=True, null=True)   # For "vuelta" direction
  
  class Meta:
    db_table = 'routes'

  def __str__(self):
    return f"{self.name} - {self.company.name}"


class RouteEdge(models.Model):
  route = models.ForeignKey(Route, on_delete=models.CASCADE)
  edge = models.ForeignKey(Edge, on_delete=models.CASCADE)
  order = models.IntegerField()  # To maintain the sequence of edges in the route
  direction = models.CharField(max_length=1, choices=[('I', 'Ida'), ('V', 'Vuelta')])

  class Meta:
    db_table = 'route_edges'
    ordering = ['order']

  def __str__(self):
    return f"Route {self.route.name} - Edge {self.edge.id}"


class RouteNode(models.Model):
  route = models.ForeignKey(Route, on_delete=models.CASCADE)
  node = models.ForeignKey(Node, on_delete=models.CASCADE)
  order = models.IntegerField()
  direction = models.CharField(max_length=1, choices=[('I', 'Ida'), ('V', 'Vuelta')])

  class Meta:
    db_table = 'route_nodes'
    ordering = ['order']

  def __str__(self):
    return f"Route {self.route.name} - Node {self.node.id}"
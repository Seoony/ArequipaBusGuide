from django.db import models
from django.contrib.gis.db import models as gis_models
# Create your models here.
class Node(models.Model):
  osm_id = models.CharField(max_length=255, unique=True)
  location = gis_models.PointField(srid=4326)  # (lng, lat)
  
  class Meta:
    db_table = 'nodes'

  def __str__(self):
    return f"Node {self.osm_id}"
      

class Edge(models.Model):
  source = models.ForeignKey(Node, related_name='edges_from', on_delete=models.CASCADE)
  target = models.ForeignKey(Node, related_name='edges_to', on_delete=models.CASCADE)
  distance = models.FloatField()  # Puedes precomputar la distancia si quieres
  geometry = gis_models.LineStringField()  # Geometría del camino
  
  class Meta:
    db_table = 'edges'

  def __str__(self):
    return f"Edge from {self.source_id} to {self.target_id}"

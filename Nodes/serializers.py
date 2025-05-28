from rest_framework import serializers
from .models import Node, Edge

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['id', 'latitude', 'longitude', 'name', 'description']
        read_only_fields = ['id']

class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ['id', 'start_node', 'end_node', 'distance', 'description']
        read_only_fields = ['id']

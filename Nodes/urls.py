from django.urls import path
from .views import NodeViewSet, EdgeViewSet

urlpatterns = [
    # Node endpoints
    path('node/', NodeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('node/<int:pk>/', NodeViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),

    # Edge endpoints
    path('edge/', EdgeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('edge/<int:pk>/', EdgeViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]

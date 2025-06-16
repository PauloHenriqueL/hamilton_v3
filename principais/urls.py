from django.urls import path
from . import views 

urlpatterns = [
    # URLs de Views baseadas em templates
    path('consulta/list/', views.ConsultaListView.as_view(), name='consulta-list'),
    path('consulta/create/', views.ConsultaCreateView.as_view(), name='consulta-create'),
    path('consulta/<int:pk>/detail/', views.ConsultaDetailView.as_view(), name='consulta-detail'),
    path('consulta/<int:pk>/update/', views.ConsultaUpdateView.as_view(), name='consulta-update'),
    path('consulta/<int:pk>/delete/', views.ConsultaDeleteView.as_view(), name='consulta-delete'),
    path('api/pacientes/<int:pk>/valor_sessao/', views.paciente_valor_sessao, name='paciente-valor-sessao'),
    
    path('api/v1/consulta/', views.ConsultaListCreateAPIView.as_view(), name='consulta-list-create-api'),
    path('api/v1/consulta/<int:pk>/', views.ConsultaRetrieveUpdateDestroyAPIView.as_view(), name='consulta-detail-api'),

    path('altadesistencia/nova/', views.AltaDesistenciaCreateView.as_view(), name='altadesistencia-create'),
    
    path('api/v1/paciente/', views.PacienteListCreateAPIView.as_view(), name='paciente-list-create-api'),
    path('api/v1/paciente/<int:pk>/', views.PacienteRetrieveUpdateDestroyAPIView.as_view(), name='paciente-detail-api'),
    
    path('api/v1/terapeuta/', views.TerapeutaListCreateAPIView.as_view(), name='terapeuta-list-create-api'),
    path('api/v1/terapeuta/<int:pk>/', views.TerapeutaRetrieveUpdateDestroyAPIView.as_view(), name='terapeuta-detail-api'),

    path('api/v1/avaliacao', views.AvaliacaoListCreateAPIView.as_view(), name='avaliacao-list'),
    path('api/v1/avaliacao/<int:pk>', views.AvaliacaoRetrieveUpdateDestroyAPIView.as_view(), name='avaliacao-update'),

    path('api/v1/altadesistencia', views.AltadesistenciaListCreateAPIView.as_view(), name='altadesistencia-list'),
    path('api/v1/altadesistencia/<int:pk>', views.AltadesistenciaRetrieveUpdateDestroyAPIView.as_view(), name='altadesistencia-update'),
]
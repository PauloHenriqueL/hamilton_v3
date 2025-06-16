from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .metrics import get_consulta_metrics, get_terapeuta_metrics


@login_required
@permission_required('auth.view_user', raise_exception=True)
def dashboard_view(request):
    """
    View principal do dashboard com métricas simplificadas
    """
    try:
        # Buscar métricas principais
        metrics = get_consulta_metrics()
        
        # Buscar métricas de terapeutas
        metricas_terapeutas = get_terapeuta_metrics()
        
        context = {
            'metrics': metrics,
            'metricas_terapeutas': metricas_terapeutas,
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # Log do erro para debugging
        print(f"Erro no dashboard: {e}")
        
        # Contexto com valores padrão em caso de erro
        context = {
            'metrics': {
                'taxa_adesao': '0,0',
                'consultas_realizadas': 0,
                'consultas_marcadas': 0,
                'receita_total_recebida': '0,00',
                'receita_total_esperada': '0,00',
                'receita_total_acordada': '0,00',
                'captacao_pacientes_mes': 0,
                'pacientes_ativos': 0,
                'terapeutas_ativos': 0,
                'total_sessoes_mes': 0,
                'preco_medio_acordado': '0,00',
                'preco_medio_esperado': '0,00',
                'preco_medio_realizado': '0,00',
            },
            'metricas_terapeutas': [],
            'error_message': 'Erro ao carregar métricas. Verifique o banco de dados.',
        }
        
        return render(request, 'dashboard.html', context)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .metrics import (
    get_consulta_metrics, 
    get_terapeuta_metrics,
    get_receita_pix_mensal,
    get_porcentagem_pacientes_com_consultas,
    get_monthly_consultas_data,
    get_daily_consultas_data,
    get_daily_valor_data
)
import json


@login_required
@permission_required('auth.view_user', raise_exception=True)
def dashboard_view(request):
    """
    View principal do dashboard com métricas completas
    """
    try:
        # Buscar todas as métricas
        metrics = get_consulta_metrics()
        metricas_terapeutas = get_terapeuta_metrics()
        porcentagem_pacientes_consultas = get_porcentagem_pacientes_com_consultas()
        receita_pix_mensal = get_receita_pix_mensal()
        monthly_consultas_data = get_monthly_consultas_data()
        daily_consultas_data = get_daily_consultas_data()
        daily_valor_data = get_daily_valor_data()
        
        context = {
            # Métricas principais
            'metrics': metrics,
            'metricas_terapeutas': metricas_terapeutas,
            'porcentagem_pacientes_consultas': porcentagem_pacientes_consultas,
            
            # Dados para gráficos (convertidos para JSON)
            'receita_pix_mensal': json.dumps(receita_pix_mensal),
            'monthly_consultas_data': json.dumps(monthly_consultas_data),
            'daily_consultas_data': json.dumps(daily_consultas_data),
            'daily_valor_data': json.dumps(daily_valor_data),
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # Log do erro para debugging
        print(f"Erro no dashboard: {e}")
        
        # Contexto com valores padrão em caso de erro
        context = {
            'metrics': {
                'taxa_adesao': '0.0',
                'consultas_realizadas': 0,
                'consultas_marcadas': 0,
                'receita_total_recebida': '0,00',
                'receita_acordada_mensal': '0,00',
                'captacao_pacientes_mes': 0,
                'pacientes_ativos': 0,
                'terapeutas_ativos': 0,
                'preco_medio_realizado': '0,00',
                'tempo_medio_match': '0.0',
                'porcentagem_inadimplentes': '0.0'
            },
            'metricas_terapeutas': [],
            'porcentagem_pacientes_consultas': {
                'pacientes_com_consultas': 0,
                'total_pacientes_ativos': 0,
                'porcentagem': '0.0'
            },
            'receita_pix_mensal': json.dumps({'months': [], 'values': []}),
            'monthly_consultas_data': json.dumps({'months': [], 'values': []}),
            'daily_consultas_data': json.dumps({'dates': [], 'values': []}),
            'daily_valor_data': json.dumps({'dates': [], 'values': []}),
            'error_message': 'Erro ao carregar métricas. Verifique o banco de dados.',
        }
        
        return render(request, 'dashboard.html', context)
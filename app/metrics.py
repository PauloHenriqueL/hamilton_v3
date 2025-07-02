from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from django.utils.formats import number_format
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from principais import models


def get_terapeuta_metrics():
    try:
        # Definir período dos últimos 31 dias
        hoje = timezone.now().date()
        data_limite = hoje - timedelta(days=31)
        
        terapeutas_stats = models.Terapeuta.objects.select_related('fk_associado').annotate(
            total_consultas=Count('consulta', filter=Q(consulta__dat_consulta__gte=data_limite)),
            total_consultasrealizadas=Count('consulta', filter=Q(consulta__is_realizado=True, consulta__dat_consulta__gte=data_limite)),
            pacientes_ativos=Count('consulta__fk_paciente', distinct=True, filter=Q(
                consulta__fk_paciente__is_active=True, 
                consulta__dat_consulta__gte=data_limite
            )),
            valor_recebido=Sum('consulta__vlr_pago', filter=Q(consulta__vlr_pago__gt=0, consulta__dat_consulta__gte=data_limite)),
            receita_acordada=Sum('consulta__vlr_consulta', filter=Q(consulta__dat_consulta__gte=data_limite)),
        ).filter(
            is_active=True
        ).values(
            'fk_associado__nome',
            'total_consultas',
            'total_consultasrealizadas', 
            'pacientes_ativos',
            'valor_recebido',
            'receita_acordada',
        )
        
        metricas_detalhadas = []
        for stats in terapeutas_stats:
            total_consultas = stats['total_consultas'] or 0
            total_realizadas = stats['total_consultasrealizadas'] or 0
            valor_recebido = stats['valor_recebido'] or Decimal('0.00')
            receita_acordada = stats['receita_acordada'] or Decimal('0.00')
            
            taxa_adesao = (total_realizadas / total_consultas * 100) if total_consultas > 0 else 0
            diferenca = receita_acordada - valor_recebido
            status_diferenca = "positivo" if diferenca > 0 else ("negativo" if diferenca < 0 else "igual")
            
            if total_consultas > 0:
                metricas_detalhadas.append({
                    'nome': stats['fk_associado__nome'],
                    'taxa_adesao': number_format(taxa_adesao, decimal_pos=1),
                    'pacientes_ativos': stats['pacientes_ativos'] or 0,
                    'total_consultas': total_consultas,
                    'total_consultasrealizadas': total_realizadas,
                    'valor_recebido': number_format(valor_recebido, decimal_pos=2, force_grouping=True),
                    'receita_acordada': number_format(receita_acordada, decimal_pos=2, force_grouping=True),
                    'diferenca': number_format(abs(diferenca), decimal_pos=2, force_grouping=True),
                    'status_diferenca': status_diferenca,
                })
        
        return metricas_detalhadas
        
    except Exception as e:
        print(f"Erro ao buscar métricas de terapeutas: {e}")
        return []


def get_receita_pix_mensal():
    """Receita por Mês (Últimos 6 meses) - MANTIDO PARA GRÁFICOS"""
    try:
        today = timezone.now().date()
        six_months_ago = today - timedelta(days=180)  # Mantido para gráficos
        
        # Query para receita PIX mensal
        monthly_pix = models.Consulta.objects.filter(
            dat_consulta__gte=six_months_ago,
            vlr_pago__gt=0
        ).annotate(
            month=TruncMonth('dat_consulta')
        ).values('month').annotate(
            receita_pix_total=Sum('vlr_pago')
        ).order_by('month')
        
        return {
            'months': [item['month'].strftime('%b/%Y') for item in monthly_pix],
            'values': [float(item['receita_pix_total'] or 0) for item in monthly_pix]
        }
    except Exception as e:
        print(f"Erro ao buscar receita PIX mensal: {e}")
        return {'months': [], 'values': []}


def get_porcentagem_pacientes_com_consultas():
    try:
        hoje = timezone.now().date()
        data_limite = hoje - timedelta(days=31)  # Mudado para 31 dias

        # Total de pacientes ativos
        total_pacientes_ativos = models.Paciente.objects.filter(is_active=True).count()
        
        # Pacientes únicos com consultas nos últimos 31 dias
        pacientes_com_consultas = models.Paciente.objects.filter(
            consulta__dat_consulta__gte=data_limite,
            is_active=True
        ).distinct().count()
        
        # Calcular porcentagem
        porcentagem = (pacientes_com_consultas / total_pacientes_ativos * 100) if total_pacientes_ativos > 0 else 0
        
        return {
            'pacientes_com_consultas': pacientes_com_consultas,
            'total_pacientes_ativos': total_pacientes_ativos,
            'porcentagem': number_format(porcentagem, decimal_pos=1)
        }
    except Exception as e:
        print(f"Erro ao calcular porcentagem de pacientes com consultas: {e}")
        return {'pacientes_com_consultas': 0, 'total_pacientes_ativos': 0, 'porcentagem': '0.0'}


def get_consulta_metrics():
    """Obter métricas principais do dashboard - ÚLTIMOS 31 DIAS"""
    try:
        hoje = timezone.now().date()
        data_limite = hoje - timedelta(days=31)  # Últimos 31 dias
        primeiro_dia_mes = hoje.replace(day=1)

        # Query principal para métricas de consultas (ÚLTIMOS 31 DIAS)
        consulta_stats = models.Consulta.objects.filter(
            dat_consulta__gte=data_limite  # Filtro para últimos 31 dias
        ).aggregate(
            # Taxa de Adesão
            total_consultas_marcadas=Count('pk_consulta'),
            total_consultas_realizadas=Count('pk_consulta', filter=Q(is_realizado=True)),
            
            # Receitas
            receita_total_recebida=Sum('vlr_pago', filter=Q(vlr_pago__gt=0)),
            
            # Porcentagem de inadimplentes
            consultas_valor_zero=Count('pk_consulta', filter=Q(vlr_pago=0)),
            consultas_valor_positivo=Count('pk_consulta', filter=Q(vlr_pago__gt=0))
        )
        
        # Query para métricas de pacientes (ÚLTIMOS 31 DIAS para alguns campos)
        paciente_stats = models.Paciente.objects.aggregate(
            # Pacientes ativos (total, não apenas 31 dias)
            pacientes_ativos=Count('pk_paciente', filter=Q(is_active=True)),
            
            # Captação dos últimos 31 dias (mudado de mês atual para 31 dias)
            captacao_mes=Count('pk_paciente', filter=Q(
                created_at__gte=timezone.make_aware(datetime.combine(data_limite, datetime.min.time()))
            )),
            
            # Receita acordada de pacientes ativos com consultas nos últimos 31 dias
            receita_acordada_mensal=Sum('vlr_sessao', filter=Q(
                is_active=True,
            ))
        )
        
        # Tempo médio entre cadastro e match nos últimos 31 dias
        try:
            matches_periodo = models.Match.objects.filter(
                created_at__gte=timezone.make_aware(datetime.combine(data_limite, datetime.min.time()))
            ).select_related('fk_paciente')
            
            tempo_total_dias = 0
            count_matches = 0
            for match in matches_periodo:
                if match.fk_paciente.created_at and match.dat_consulta:
                    diferenca = match.dat_consulta - match.fk_paciente.created_at.date()
                    tempo_total_dias += diferenca.days
                    count_matches += 1
            
            tempo_medio_match = tempo_total_dias / count_matches if count_matches > 0 else 0
        except Exception:
            tempo_medio_match = 0
        
        # Contagem de terapeutas ativos (total, não apenas 31 dias)
        total_terapeutas = models.Terapeuta.objects.filter(is_active=True).count()
        
        # Cálculos
        total_marcadas = consulta_stats['total_consultas_marcadas'] or 0
        total_realizadas = consulta_stats['total_consultas_realizadas'] or 0
        receita_recebida = consulta_stats['receita_total_recebida'] or Decimal('0.00')
        consultas_valor_zero = consulta_stats['consultas_valor_zero'] or 0
        consultas_valor_positivo = consulta_stats['consultas_valor_positivo'] or 0
        
        # Taxa de adesão (últimos 31 dias)
        taxa_adesao = (total_realizadas / total_marcadas * 100) if total_marcadas > 0 else 0
        
        # Preço médio realizado (apenas consultas pagas e realizadas nos últimos 31 dias)
        preco_medio_realizado_query = models.Consulta.objects.filter(
            dat_consulta__gte=data_limite,  # Últimos 31 dias
            is_realizado=True,
            vlr_pago__gt=0
        ).aggregate(
            media=Avg('vlr_pago')
        )
        preco_medio_realizado = preco_medio_realizado_query['media'] or Decimal('0.00')
        
        # Porcentagem de inadimplentes (últimos 31 dias)
        total_consultas_valor = consultas_valor_zero + consultas_valor_positivo
        porcentagem_inadimplentes = (consultas_valor_zero / total_consultas_valor * 100) if total_consultas_valor > 0 else 0
        
        return {
            # Taxa de Adesão (últimos 31 dias)
            'taxa_adesao': number_format(taxa_adesao, decimal_pos=1),
            'consultas_realizadas': total_realizadas,
            'consultas_marcadas': total_marcadas,
            
            # Receitas (últimos 31 dias)
            'receita_total_recebida': number_format(receita_recebida, decimal_pos=2, force_grouping=True),
            'receita_acordada_mensal': number_format(paciente_stats['receita_acordada_mensal'] or 0, decimal_pos=2, force_grouping=True),
            
            # Pacientes e Terapeutas
            'captacao_pacientes_mes': paciente_stats['captacao_mes'] or 0,  # Últimos 31 dias
            'pacientes_ativos': paciente_stats['pacientes_ativos'] or 0,    # Total
            'terapeutas_ativos': total_terapeutas,                          # Total
            
            # Preço Médio (últimos 31 dias)
            'preco_medio_realizado': number_format(preco_medio_realizado, decimal_pos=2, force_grouping=True),
            
            # Novas métricas (últimos 31 dias)
            'tempo_medio_match': number_format(tempo_medio_match, decimal_pos=1),
            'porcentagem_inadimplentes': number_format(porcentagem_inadimplentes, decimal_pos=1)
        }
        
    except Exception as e:
        print(f"Erro ao buscar métricas do banco: {e}")
        # Retorna valores padrão em caso de erro
        return {
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
        }


# FUNÇÕES DOS GRÁFICOS - MANTIDAS SEM ALTERAÇÃO
def get_monthly_consultas_data():
    """Obter dados mensais de consultas - MANTIDO PARA GRÁFICOS"""
    try:
        today = timezone.now().date()
        six_months_ago = today - timedelta(days=180)
        
        # UMA query para todos os meses
        monthly_stats = models.Consulta.objects.filter(
            dat_consulta__gte=six_months_ago
        ).annotate(
            month=TruncMonth('dat_consulta')
        ).values('month').annotate(
            consultas_count=Count('pk_consulta')
        ).order_by('month')
        
        return {
            'months': [item['month'].strftime('%b/%Y') for item in monthly_stats],
            'values': [item['consultas_count'] for item in monthly_stats]
        }
    except Exception as e:
        print(f"Erro ao buscar dados mensais de consultas: {e}")
        return {'months': [], 'values': []}


def get_daily_consultas_data():
    """Obter dados diários de consultas - MANTIDO PARA GRÁFICOS"""
    try:
        today = timezone.now().date()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        # UMA query para todos os dias
        daily_stats = models.Consulta.objects.filter(
            dat_consulta__in=last_7_days
        ).values('dat_consulta').annotate(
            consultas_count=Count('pk_consulta')
        ).order_by('dat_consulta')
        
        # Criar dicionário para lookup rápido
        daily_dict = {str(item['dat_consulta']): item['consultas_count'] for item in daily_stats}
        
        return {
            'dates': [str(date) for date in last_7_days],
            'values': [daily_dict.get(str(date), 0) for date in last_7_days]
        }
    except Exception as e:
        print(f"Erro ao buscar dados diários de consultas: {e}")
        return {'dates': [], 'values': []}


def get_daily_valor_data():
    """Obter dados diários de valor - MANTIDO PARA GRÁFICOS"""
    try:
        today = timezone.now().date()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        # UMA query para todos os dias
        daily_stats = models.Consulta.objects.filter(
            dat_consulta__in=last_7_days
        ).values('dat_consulta').annotate(
            valor_total=Sum('vlr_consulta')
        ).order_by('dat_consulta')
        
        # Criar dicionário para lookup rápido
        daily_dict = {str(item['dat_consulta']): float(item['valor_total'] or 0) for item in daily_stats}
        
        return {
            'dates': [str(date) for date in last_7_days],
            'values': [daily_dict.get(str(date), 0) for date in last_7_days]
        }
    except Exception as e:
        print(f"Erro ao buscar dados diários de valor: {e}")
        return {'dates': [], 'values': []}
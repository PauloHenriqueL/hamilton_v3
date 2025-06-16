from django.db.models import Sum, Count, Avg, Q
from django.utils.formats import number_format
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from principais import models


def get_terapeuta_metrics():
    """Obter métricas de consultas por terapeuta - COM FALLBACK"""
    try:
        # Query com todas as agregações por terapeuta
        terapeutas_stats = models.Terapeuta.objects.select_related('fk_associado').annotate(
            total_consultas=Count('consulta'),
            total_consultasrealizadas=Count('consulta', filter=Q(consulta__is_realizado=True)),
            pacientes_ativos=Count('consulta__fk_paciente', distinct=True, filter=Q(consulta__fk_paciente__is_active=True)),
            valor_recebido=Sum('consulta__vlr_pago', filter=Q(consulta__vlr_pago__gt=0)),
            receita_esperada=Sum('consulta__vlr_consulta')
        ).filter(
            is_active=True
        ).values(
            'fk_associado__nome',
            'total_consultas',
            'total_consultasrealizadas', 
            'pacientes_ativos',
            'valor_recebido',
            'receita_esperada'
        )
        
        metricas_detalhadas = []
        for stats in terapeutas_stats:
            total_consultas = stats['total_consultas'] or 0
            total_realizadas = stats['total_consultasrealizadas'] or 0
            valor_recebido = stats['valor_recebido'] or Decimal('0.00')
            receita_esperada = stats['receita_esperada'] or Decimal('0.00')
            
            taxa_adesao = (total_realizadas / total_consultas * 100) if total_consultas > 0 else 0
            diferenca = valor_recebido - receita_esperada
            status_diferenca = "positivo" if diferenca > 0 else ("negativo" if diferenca < 0 else "igual")
            
            metricas_detalhadas.append({
                'nome': stats['fk_associado__nome'],
                'taxa_adesao': number_format(taxa_adesao, decimal_pos=1),
                'pacientes_ativos': stats['pacientes_ativos'] or 0,
                'total_consultas': total_consultas,
                'total_consultasrealizadas': total_realizadas,
                'valor_recebido': number_format(valor_recebido, decimal_pos=2, force_grouping=True),
                'receita_esperada': number_format(receita_esperada, decimal_pos=2, force_grouping=True),
                'diferenca': number_format(abs(diferenca), decimal_pos=2, force_grouping=True),
                'status_diferenca': status_diferenca
            })
        
        return metricas_detalhadas
        
    except Exception as e:
        print(f"Erro ao buscar métricas de terapeutas: {e}")
        raise e  # Re-lança a exceção para debugging


def get_consulta_metrics():
    """Obter métricas principais do dashboard - COM FALLBACK"""
    try:
        hoje = timezone.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Query principal para métricas de consultas
        consulta_stats = models.Consulta.objects.aggregate(
            # Taxa de Adesão
            total_consultas_marcadas=Count('pk_consulta'),
            total_consultas_realizadas=Count('pk_consulta', filter=Q(is_realizado=True)),
            
            # Receitas
            receita_total_recebida=Sum('vlr_pago', filter=Q(vlr_pago__gt=0)),
            receita_total_esperada=Sum('vlr_consulta'),
            
            # Preços médios
            preco_medio_esperado=Avg('vlr_consulta'),
            
            # Sessões do mês
            total_sessoes_mes=Count('pk_consulta', filter=Q(
                dat_consulta__gte=primeiro_dia_mes,
                is_realizado=True
            ))
        )
        
        # Query para métricas de pacientes
        paciente_stats = models.Paciente.objects.aggregate(
            # Preço médio acordado
            preco_medio_acordado=Avg('vlr_sessao', filter=Q(is_active=True)),
            
            # Pacientes ativos
            pacientes_ativos=Count('pk_paciente', filter=Q(is_active=True)),
            
            # Captação do mês (novos pacientes criados no mês atual)
            captacao_mes=Count('pk_paciente', filter=Q(
                created_at__year=hoje.year,
                created_at__month=hoje.month
            ))
        )
        
        # Receita acordada (total do valor da sessão dos pacientes ativos)
        receita_acordada = models.Paciente.objects.filter(
            is_active=True
        ).aggregate(
            total=Sum('vlr_sessao')
        )['total'] or Decimal('0.00')
        
        # Contagem de terapeutas ativos
        total_terapeutas = models.Terapeuta.objects.filter(is_active=True).count()
        
        # Cálculos
        total_marcadas = consulta_stats['total_consultas_marcadas'] or 0
        total_realizadas = consulta_stats['total_consultas_realizadas'] or 0
        receita_recebida = consulta_stats['receita_total_recebida'] or Decimal('0.00')
        receita_esperada = consulta_stats['receita_total_esperada'] or Decimal('0.00')
        
        # Taxa de adesão
        taxa_adesao = (total_realizadas / total_marcadas * 100) if total_marcadas > 0 else 0
        
        # Preço médio realizado (apenas consultas pagas e realizadas)
        preco_medio_realizado_query = models.Consulta.objects.filter(
            is_realizado=True,
            vlr_pago__gt=0
        ).aggregate(
            media=Avg('vlr_pago')
        )
        preco_medio_realizado = preco_medio_realizado_query['media'] or Decimal('0.00')
        
        return {
            # Taxa de Adesão
            'taxa_adesao': number_format(taxa_adesao, decimal_pos=1),
            'consultas_realizadas': total_realizadas,
            'consultas_marcadas': total_marcadas,
            
            # Receitas
            'receita_total_recebida': number_format(receita_recebida, decimal_pos=2, force_grouping=True),
            'receita_total_esperada': number_format(receita_esperada, decimal_pos=2, force_grouping=True),
            'receita_total_acordada': number_format(receita_acordada, decimal_pos=2, force_grouping=True),
            
            # Pacientes e Terapeutas
            'captacao_pacientes_mes': paciente_stats['captacao_mes'] or 0,
            'pacientes_ativos': paciente_stats['pacientes_ativos'] or 0,
            'terapeutas_ativos': total_terapeutas,
            
            # Sessões
            'total_sessoes_mes': consulta_stats['total_sessoes_mes'] or 0,
            
            # Preços Médios
            'preco_medio_acordado': number_format(paciente_stats['preco_medio_acordado'] or 0, decimal_pos=2, force_grouping=True),
            'preco_medio_esperado': number_format(consulta_stats['preco_medio_esperado'] or 0, decimal_pos=2, force_grouping=True),
            'preco_medio_realizado': number_format(preco_medio_realizado, decimal_pos=2, force_grouping=True),
        }
        
    except Exception as e:
        print(f"Erro ao buscar métricas do banco: {e}")
        raise e  # Re-lança a exceção para debugging
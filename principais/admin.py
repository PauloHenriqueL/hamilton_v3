from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Max, Q
from .models import Associado, Paciente, Selecao, Terapeuta, Consulta, Avaliacao, Altadesistencia, Match
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from datetime import date, timedelta


# Base Admin com funcionalidades comuns
class BaseAdmin(admin.ModelAdmin):
    """Admin base com funcionalidades comuns"""
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else ()


# Filtros reutilizáveis
class StatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('active', 'Ativos'),
            ('inactive', 'Inativos'),
            ('all', 'Todos')
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        elif self.value() == 'inactive':
            return queryset.filter(is_active=False)
        # Se value() for 'all' ou None, retorna todos os registros
        return queryset


class SetorFilter(admin.SimpleListFilter):
    title = 'Setor'
    parameter_name = 'setor'
    
    def lookups(self, request, model_admin):
        from acessorios.models import Setor
        return [(setor.pk, setor.setor) for setor in Setor.objects.all()]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(setores__pk=self.value())
        return queryset


class DecanoFilter(admin.SimpleListFilter):
    title = 'É Decano'
    parameter_name = 'is_decano'
    
    def lookups(self, request, model_admin):
        return [
            ('sim', 'Sim'),
            ('nao', 'Não'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'sim':
            return queryset.filter(setores__setor__icontains='decano')
        elif self.value() == 'nao':
            return queryset.exclude(setores__setor__icontains='decano')
        return queryset


class PeriodoFilter(admin.SimpleListFilter):
    title = 'Período'
    parameter_name = 'periodo'
    
    def lookups(self, request, model_admin):
        return [
            ('hoje', 'Hoje'),
            ('semana', 'Esta Semana'),
            ('mes', 'Este Mês'),
        ]
    
    def queryset(self, request, queryset):
        hoje = timezone.now().date()
        if self.value() == 'hoje':
            return queryset.filter(dat_consulta=hoje)
        elif self.value() == 'semana':
            inicio = hoje - timedelta(days=hoje.weekday())
            return queryset.filter(dat_consulta__range=[inicio, inicio + timedelta(days=6)])
        elif self.value() == 'mes':
            return queryset.filter(dat_consulta__year=hoje.year, dat_consulta__month=hoje.month)


# Métodos utilitários
def status_badge(valor, true_text="Ativo", false_text="Inativo"):
    """Cria badge colorido para status"""
    if valor:
        return format_html('<span style="color:green;font-weight:bold;">✓ {}</span>', true_text)
    return format_html('<span style="color:red;font-weight:bold;">✗ {}</span>', false_text)


# Admins
@admin.register(Associado)
class AssociadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cpf', 'telefone', 'get_usuario', 'is_active', 'created_at')
    list_filter = ('is_active', 'sexo', 'setores', 'created_at')
    search_fields = ('nome', 'email', 'cpf', 'telefone')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('setores',)

    
    # Configuração de ManyToMany
    filter_horizontal = ['setores']
    
    # Fieldsets para organizar o formulário
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'usuario', 'email', 'telefone', 'contato_apoio', 'dat_nascimento', 'sexo', 'cpf')
        }),
        ('Informações Acadêmicas/Profissionais', {
            'fields': ('faculdade', 'setores', 'endereco')
        }),
        ('Status e Observações', {
            'fields': ('is_active', 'observacao')
        }),
    )
    
    def get_queryset(self, request):
        """Otimiza as consultas"""
        return super().get_queryset(request).prefetch_related('setores')
    
    def setores_display(self, obj):
        """Mostra os setores do associado"""
        setores = obj.setores.all()
        if setores:
            return ', '.join([setor.setor for setor in setores])
        return '-'
    setores_display.short_description = 'Setores'

    def get_usuario(self, obj):
        return obj.usuario.username if obj.usuario else "Sem usuário"
    get_usuario.short_description = "Usuário"
    get_usuario.admin_order_field = 'usuario__username'

@admin.register(Selecao)
class SelecaoAdmin(admin.ModelAdmin):
    list_display = [
        'pk_selecao',
        'get_avaliador_nome',
        'get_avaliado_nome', 
        'dat_avaliacao',
        'estagio_mudanca',
        'estrutura',
        'acolhimento'
    ]
    
    list_filter = [
        'dat_avaliacao',
        'estagio_mudanca',
        'estrutura',
        'acolhimento',
        'fk_terapeuta_avaliador__fk_associado__setores'
    ]
    
    search_fields = [
        'fk_terapeuta_avaliador__fk_associado__nome',
        'fk_associado_avaliado__nome'
    ]
    
    date_hierarchy = 'dat_avaliacao'
    
    
    # Métodos para exibir nomes nas colunas
    def get_avaliador_nome(self, obj):
        return obj.fk_terapeuta_avaliador.fk_associado.nome
    get_avaliador_nome.short_description = 'Avaliador'
    get_avaliador_nome.admin_order_field = 'fk_terapeuta_avaliador__fk_associado__nome'
    
    def get_avaliado_nome(self, obj):
        return obj.fk_associado_avaliado.nome
    get_avaliado_nome.short_description = 'Avaliado'
    get_avaliado_nome.admin_order_field = 'fk_associado_avaliado__nome'
    
    # Otimizar queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'fk_terapeuta_avaliador__fk_associado',
            'fk_associado_avaliado'
        )
    
    # Personalizar formulário
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "fk_terapeuta_avaliador":
            kwargs["queryset"] = Terapeuta.objects.select_related('fk_associado').filter(is_active=True)
        if db_field.name == "fk_associado_avaliado":
            kwargs["queryset"] = Associado.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)




@admin.register(Paciente)
class PacienteAdmin(BaseAdmin):
    list_display = [
        'nome',
        'telefone',
        'is_active',
        'fk_clinica',
        'fk_modalidade',
        'vlr_sessao',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'fk_clinica',
        'fk_captacao', 
        'fk_modalidade'
    ]
    
    search_fields = [
        'nome',
        'email',
        'telefone',
        'nome_contato_apoio',
        'contato_apoio',
        'oberservacao'
    ]
    
    # Configurações de paginação e ordenação
    list_per_page = 20
    list_max_show_all = 100
    ordering = ['nome']
    date_hierarchy = 'created_at'
    
    # Campos editáveis na listagem
    list_editable = ['is_active']
    
    # Campos somente leitura
    readonly_fields = ['created_at', 'updated_at', 'pk_paciente']
    
    # Filtros laterais
    list_select_related = ['fk_clinica', 'fk_captacao', 'fk_modalidade']
    
    # Ações personalizadas
    actions = ['ativar_pacientes', 'desativar_pacientes']
    
    # Configurações de busca
    search_help_text = "Pesquise por nome, email, telefone, contato de apoio ou observações"
    
    def get_queryset(self, request):
        """Otimiza as consultas"""
        return super().get_queryset(request).select_related(
            'fk_clinica', 'fk_captacao', 'fk_modalidade'
        )
    
    def status_ativo(self, obj):
        """Status com ícone colorido"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">●</span> Ativo'
            )
        return format_html(
            '<span style="color: red;">●</span> Inativo'
        )
    status_ativo.short_description = 'Status'
    status_ativo.admin_order_field = 'is_active'


    # Ações personalizadas
    def ativar_pacientes(self, request, queryset):
        """Ativa pacientes selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} paciente(s) ativado(s) com sucesso.'
        )
    ativar_pacientes.short_description = "Ativar pacientes selecionados"
    
    def desativar_pacientes(self, request, queryset):
        """Desativa pacientes selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} paciente(s) desativado(s) com sucesso.'
        )
    desativar_pacientes.short_description = "Desativar pacientes selecionados"
    
@admin.register(Terapeuta)
class TerapeutaAdmin(BaseAdmin):
    list_display = [
        'associado_nome', 
        'associado_email', 
        'decano_nome',
        'abordagem_display', 
        'clinica_display', 
        'status_display',
        'is_active',  
        'total_pacientes', 
        'total_consultas'
    ]
    
    list_filter = [StatusFilter, 'fk_abordagem', 'fk_clinica', 'fk_nucleo', 'fk_modalidade']
    search_fields = [
        'fk_associado__nome', 
        'fk_associado__email', 
        'fk_associado__telefone',
        'fk_decano__nome'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 20
    ordering = ['fk_associado__nome']
    
    # Campos editáveis na listagem
    list_editable = ['is_active']
    
    # Campos somente leitura
    readonly_fields = ['created_at', 'updated_at', 'pk_terapeuta']
    
    # Filtros laterais - otimização
    list_select_related = [
        'fk_associado', 
        'fk_decano',
        'fk_abordagem', 
        'fk_nucleo',
        'fk_clinica',
        'fk_modalidade'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'fk_associado',
            'fk_decano', 
            'fk_abordagem', 
            'fk_nucleo',
            'fk_clinica',
            'fk_modalidade'
        ).annotate(
            total_consultas=Count('consulta'),
            total_pacientes=Count('consulta__fk_paciente', distinct=True)
        )
    
    def associado_nome(self, obj):
        return obj.fk_associado.nome if obj.fk_associado else '-'
    associado_nome.short_description = 'Nome'
    associado_nome.admin_order_field = 'fk_associado__nome'
    
    def associado_email(self, obj):
        return obj.fk_associado.email if obj.fk_associado else '-'
    associado_email.short_description = 'Email'
    associado_email.admin_order_field = 'fk_associado__email'
    
    def decano_nome(self, obj):
        return obj.fk_decano.nome if obj.fk_decano else '-'
    decano_nome.short_description = 'Decano'
    decano_nome.admin_order_field = 'fk_decano__nome'
    
    def status_display(self, obj):
        return status_badge(obj.is_active)
    status_display.short_description = 'Status'
    
    def abordagem_display(self, obj):
        return obj.fk_abordagem.abordagem if obj.fk_abordagem else '-'
    abordagem_display.short_description = 'Abordagem'
    
    def clinica_display(self, obj):
        return obj.fk_clinica.clinica if obj.fk_clinica else '-'
    clinica_display.short_description = 'Clínica'
    
    def total_pacientes(self, obj):
        return obj.total_pacientes or 0
    total_pacientes.short_description = 'Pacientes'
    
    def total_consultas(self, obj):
        return obj.total_consultas or 0
    total_consultas.short_description = 'Consultas'


@admin.register(Consulta)
class ConsultaAdmin(BaseAdmin):
    list_display = [
        'dat_consulta', 
        'paciente_nome', 
        'terapeuta_nome', 
        'vlr_consulta', 
        'status_realizacao', 
        'status_pagamento'
    ]
    
    # Corrigido: removido 'is_pago' que não existe no modelo
    list_filter = [PeriodoFilter, 'is_realizado']
    
    search_fields = [
        'fk_paciente__nome', 
        'fk_terapeuta__fk_associado__nome'
    ]
    date_hierarchy = 'dat_consulta'
    list_per_page = 30

    # Organização dos campos no formulário
    fieldsets = (
        ('Informações da Consulta', {
            'fields': ('fk_terapeuta', 'fk_paciente', 'dat_consulta')
        }),
        ('Valores', {
            'fields': ('vlr_consulta', 'vlr_pago'),
        }),
        ('Status', {
            'fields': ('is_realizado',),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'fk_terapeuta', 
            'fk_paciente',
            'fk_terapeuta__fk_associado'
        )
    
    def paciente_nome(self, obj):
        return obj.fk_paciente.nome if obj.fk_paciente else '-'
    paciente_nome.short_description = 'Paciente'
    paciente_nome.admin_order_field = 'fk_paciente__nome'
    
    def terapeuta_nome(self, obj):
        return obj.fk_terapeuta.fk_associado.nome if obj.fk_terapeuta and obj.fk_terapeuta.fk_associado else '-'
    terapeuta_nome.short_description = 'Terapeuta'
    terapeuta_nome.admin_order_field = 'fk_terapeuta__fk_associado__nome'
    
    def status_realizacao(self, obj):
        if obj.is_realizado is None:
            return format_html('<span style="color:gray;">? Indefinido</span>')
        return status_badge(obj.is_realizado, "Realizada", "Pendente")
    status_realizacao.short_description = 'Realização'
    
    def status_pagamento(self, obj):
        # Verificar se o campo vlr_pago existe e calcular status
        if hasattr(obj, 'vlr_pago') and obj.vlr_pago and obj.vlr_consulta:
            is_pago = obj.vlr_pago >= obj.vlr_consulta
            return status_badge(is_pago, "Paga", "Pendente")
        elif hasattr(obj, 'vlr_pago') and obj.vlr_pago:
            return format_html('<span style="color:orange;">Parcial</span>')
        else:
            return format_html('<span style="color:red;">Não Paga</span>')
    status_pagamento.short_description = 'Pagamento'
    
    def get_list_filter(self, request):
        """Adicionar filtros dinâmicos baseados nos campos do modelo"""
        filters = list(self.list_filter)
        
        # Adicionar filtro de pagamento apenas se o campo existir
        if hasattr(self.model, 'is_pago'):
            filters.append('is_pago')
        
        return filters
    

@admin.register(Avaliacao)
class AvaliacaoAdmin(BaseAdmin):
    list_display = [
        'paciente_nome', 
        'terapeuta_nome', 
        'dat_consulta', 
        'momento', 
        'created_at'
    ]
    
    list_filter = ['momento', 'consentimento_paciente', 'continuar_terapeuta']
    search_fields = [
        'fk_paciente__nome', 
        'fk_terapeuta__fk_associado__nome'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('fk_paciente', 'fk_terapeuta', 'dat_consulta', 'momento', 'consentimento_paciente', 'continuar_terapeuta', 'continuar_allos')
        }),
        ('Avaliação', {
            'fields': ('individual', 'interpessoal', 'social', 'qualidade_geral', 'geral'),
            'classes': ('wide',),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'fk_terapeuta', 
            'fk_paciente',
            'fk_terapeuta__fk_associado'
        )
    
    def paciente_nome(self, obj):
        return obj.fk_paciente.nome if obj.fk_paciente else '-'
    paciente_nome.short_description = 'Paciente'
    
    def terapeuta_nome(self, obj):
        return obj.fk_terapeuta.fk_associado.nome if obj.fk_terapeuta and obj.fk_terapeuta.fk_associado else '-'
    terapeuta_nome.short_description = 'Terapeuta'


@admin.register(Altadesistencia)
class AltadesistenciaAdmin(BaseAdmin):
    list_display = [
        'paciente_nome', 
        'terapeuta_nome', 
        'alta_desistencia', 
        'dat_sessao', 
        'momento'
    ]
    
    list_filter = ['alta_desistencia', 'momento']
    search_fields = [
        'fk_paciente__nome', 
        'fk_terapeuta__fk_associado__nome'
    ]
    date_hierarchy = 'dat_sessao'
    list_per_page = 30
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('fk_paciente', 'fk_terapeuta', 'dat_sessao', 'cancelador', 'motivo_cancel', 'momento', 'alta_desistencia')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'fk_terapeuta', 
            'fk_paciente',
            'fk_terapeuta__fk_associado'
        )
    
    def paciente_nome(self, obj):
        return obj.fk_paciente.nome if obj.fk_paciente else '-'
    paciente_nome.short_description = 'Paciente'
    
    def terapeuta_nome(self, obj):
        return obj.fk_terapeuta.fk_associado.nome if obj.fk_terapeuta and obj.fk_terapeuta.fk_associado else '-'
    terapeuta_nome.short_description = 'Terapeuta'


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('pk_match', 'fk_terapeuta', 'fk_paciente', 'dat_consulta', 'created_at')
    list_filter = ('dat_consulta', 'created_at', 'fk_terapeuta')
    search_fields = ('fk_terapeuta__nome', 'fk_paciente__nome')
    date_hierarchy = 'dat_consulta'
    ordering = ('-dat_consulta', '-created_at')
    
    fields = ('fk_terapeuta', 'fk_paciente', 'dat_consulta')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando um objeto existente
            return self.readonly_fields + ('created_at', 'updated_at')
        return self.readonly_fields


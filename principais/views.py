from rest_framework import generics
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from . import models, forms, serializers
from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated
from app.permissions import GlobalDefaultPermission
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from .models import Paciente, Terapeuta, Associado
from django.views.decorators.http import require_GET
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


@require_GET
def paciente_valor_sessao(request, pk):
    """Endpoint para obter o valor da sessão de um paciente"""
    try:
        paciente = Paciente.objects.get(pk=pk)
        return JsonResponse({'vlr_sessao': int(paciente.vlr_sessao)})
    except Paciente.DoesNotExist:
        return JsonResponse({'error': 'Paciente não encontrado'}, status=404)


class ConsultaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = models.Consulta
    template_name = 'consulta_list.html'
    context_object_name = 'consultas'
    paginate_by = 10
    permission_required = 'principais.view_consulta'

    def get_queryset(self):
        # Otimização: Usar select_related para reduzir queries
        queryset = models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente',
            'fk_terapeuta__fk_associado',
            'fk_terapeuta__fk_abordagem',
            'fk_terapeuta__fk_clinica'
        )
        
        # Filtrar apenas consultas do terapeuta logado
        try:
            # Buscar o associado do usuário logado
            associado = Associado.objects.get(usuario=self.request.user)
            # Buscar o terapeuta relacionado ao associado
            terapeuta = Terapeuta.objects.get(fk_associado=associado)
            queryset = queryset.filter(fk_terapeuta=terapeuta)
        except (Associado.DoesNotExist, Terapeuta.DoesNotExist):
            # Se não for terapeuta, verificar se é staff para ver todas
            if not self.request.user.is_staff:
                queryset = queryset.none()
        
        # Filtragem por nome
        nome = self.request.GET.get('nome')
        if nome:
            queryset = queryset.filter(
                Q(fk_paciente__nome__icontains=nome) | 
                Q(fk_terapeuta__fk_associado__nome__icontains=nome)
            )
        
        # Ordenação
        order_by = self.request.GET.get('order_by', '-dat_consulta')
        
        # Lista de ordenações válidas
        valid_orders = [
            'pk_consulta', '-pk_consulta',
            'fk_terapeuta__fk_associado__nome', '-fk_terapeuta__fk_associado__nome',
            'fk_paciente__nome', '-fk_paciente__nome',
            'dat_consulta', '-dat_consulta',
            'is_realizado', '-is_realizado',
            'vlr_pago', '-vlr_pago'
        ]
        
        if order_by in valid_orders:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-dat_consulta')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_order'] = self.request.GET.get('order_by', '-dat_consulta')
        context['current_search'] = self.request.GET.get('nome', '')
        return context

class ConsultaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = models.Consulta
    template_name = 'consulta_create.html'
    form_class = forms.ConsultaForm
    success_url = reverse_lazy('consulta-list')
    permission_required = 'principais.add_consulta'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Remover campos que não serão usados no formulário
        for field_name in ['vlr_consulta', 'vlr_pago']:
            if field_name in form.fields:
                del form.fields[field_name]
        
        try:
            # Buscar o associado do usuário logado
            associado = Associado.objects.get(usuario=self.request.user)
            # Buscar o terapeuta relacionado ao associado
            terapeuta = Terapeuta.objects.get(fk_associado=associado)
            
            form.fields['fk_terapeuta'].initial = terapeuta.pk_terapeuta
            form.fields['fk_terapeuta'].widget.attrs.update({
                'readonly': 'readonly',
                'style': 'pointer-events: none; background-color: #343a40 !important; color: #ffffff !important; border-color: #495057 !important;'
            })
            form.fields['fk_terapeuta'].queryset = form.fields['fk_terapeuta'].queryset.filter(pk=terapeuta.pk_terapeuta)
            
        except (Associado.DoesNotExist, Terapeuta.DoesNotExist):
            # Se não encontrar terapeuta, permitir seleção livre (para staff)
            pass
        
        return form
    
    def form_valid(self, form):
        quantidade = int(self.request.POST.get('quantidade', 1))
        vlr_pix_total_str = self.request.POST.get('vlr_pix_total', '')
        
        # Validar se o valor PIX foi preenchido
        if not vlr_pix_total_str or not vlr_pix_total_str.strip():
            form.add_error(None, 'O valor total recebido no PIX é obrigatório.')
            return self.form_invalid(form)
        
        vlr_pix_total = float(vlr_pix_total_str)
        
        # Calcular valor por consulta (PIX dividido pela quantidade)
        vlr_consulta = round(vlr_pix_total / quantidade, 2) if quantidade > 0 else 0
        
        # Validar se todas as datas foram preenchidas
        for i in range(quantidade):
            data_key = f'data_consulta_{i}'
            if not self.request.POST.get(data_key):
                form.add_error(None, f'Data da consulta {i+1} é obrigatória.')
                return self.form_invalid(form)
        
        consulta = form.save(commit=False)
        
        # Definir terapeuta se o usuário for um terapeuta
        try:
            associado = Associado.objects.get(usuario=self.request.user)
            terapeuta = Terapeuta.objects.get(fk_associado=associado)
            consulta.fk_terapeuta = terapeuta
        except (Associado.DoesNotExist, Terapeuta.DoesNotExist):
            # Se não for terapeuta, usar o terapeuta selecionado no form
            if not consulta.fk_terapeuta:
                messages.error(self.request, 'Erro: Terapeuta não foi definido corretamente.')
                return self.form_invalid(form)
        
        # Primeira consulta
        consulta.dat_consulta = self.request.POST.get('data_consulta_0')
        consulta.vlr_consulta = vlr_consulta  # Valor calculado
        consulta.vlr_pago = vlr_consulta      # Mesmo valor (pago via PIX)
        
        # Capturar valores dos checkboxes do formulário (primeira consulta)
        is_realizado_0 = self.request.POST.get('is_realizado_0') == 'on'
        consulta.is_realizado = is_realizado_0
        
        consulta.save()
        
        # Consultas adicionais
        if quantidade > 1:
            for i in range(1, quantidade):
                nova_consulta = models.Consulta(
                    fk_terapeuta=consulta.fk_terapeuta,
                    fk_paciente=consulta.fk_paciente,
                    vlr_consulta=vlr_consulta,  # Valor calculado
                    vlr_pago=vlr_consulta,      # Mesmo valor (pago via PIX)
                )
                
                nova_consulta.dat_consulta = self.request.POST.get(f'data_consulta_{i}')
                
                # Capturar valores dos checkboxes específicos de cada consulta
                is_realizado_i = self.request.POST.get(f'is_realizado_{i}') == 'on'
                nova_consulta.is_realizado = is_realizado_i
                
                nova_consulta.save()
        
        messages.success(self.request, f'{quantidade} consulta(s) cadastrada(s) com sucesso! Valor por consulta: R$ {vlr_consulta:.2f}')
        return redirect(self.success_url)

class ConsultaDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = models.Consulta
    template_name = 'consulta_detail.html'
    permission_required = 'principais.view_consulta'
    
    def get_queryset(self):
        # Otimização: Buscar dados relacionados junto
        return models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente',
            'fk_terapeuta__fk_associado',
            'fk_terapeuta__fk_abordagem',
            'fk_terapeuta__fk_clinica',
            'fk_terapeuta__fk_decano',
            'fk_terapeuta__fk_nucleo',
            'fk_terapeuta__fk_modalidade',
            'fk_paciente__fk_clinica',
            'fk_paciente__fk_modalidade'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consulta = self.object
        
        if consulta.vlr_pago is not None and consulta.vlr_consulta is not None:
            context['diferenca_valor'] = consulta.vlr_pago - consulta.vlr_consulta
        else:
            context['diferenca_valor'] = Decimal('0.00')
            
        return context


class ConsultaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = models.Consulta
    template_name = 'consulta_update.html'
    form_class = forms.ConsultaForm
    permission_required = 'principais.change_consulta'
    
    def get_success_url(self):
        return reverse_lazy('consulta-detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        # Otimização: Buscar dados relacionados junto
        return models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente'
        )
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Remover campos que não são usados na edição
        for field_name in ['quantidade', 'vlr_pix_total']:
            if field_name in form.fields:
                del form.fields[field_name]
        return form
    
    def form_valid(self, form):
        consulta = form.save(commit=False)
        
        # Capturar dados adicionais do formulário
        consulta.dat_consulta = self.request.POST.get('dat_consulta')
        
        # Capturar checkboxes
        is_realizado = self.request.POST.get('is_realizado') == 'on'
        is_pago = self.request.POST.get('is_pago') == 'on'
        
        consulta.is_realizado = is_realizado
        
        # Se foi marcado como pago, usar o valor da consulta se vlr_pago não foi definido
        if is_pago and not consulta.vlr_pago:
            consulta.vlr_pago = consulta.vlr_consulta
        elif not is_pago:
            consulta.vlr_pago = 0
        
        consulta.save()
        messages.success(self.request, 'Consulta atualizada com sucesso!')
        return redirect(self.get_success_url())


class ConsultaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = models.Consulta
    template_name = 'consulta_delete.html'
    success_url = reverse_lazy('consulta-list')
    permission_required = 'principais.delete_consulta'
    
    def get_queryset(self):
        # Otimização: Buscar dados relacionados para mostrar no template
        return models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente',
            'fk_terapeuta__fk_associado'
        )
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Consulta excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class AltaDesistenciaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = models.Altadesistencia
    template_name = 'altadesistencia_create.html'
    form_class = forms.AltaDesistenciaForm
    success_url = reverse_lazy('consulta-list')
    permission_required = 'principais.add_altadesistencia'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        try:
            # Buscar o associado do usuário logado
            associado = Associado.objects.get(usuario=self.request.user)
            # Buscar o terapeuta relacionado ao associado
            terapeuta = Terapeuta.objects.get(fk_associado=associado)
            
            form.fields['fk_terapeuta'].initial = terapeuta.pk_terapeuta
            form.fields['fk_terapeuta'].widget.attrs.update({
                'readonly': 'readonly',
                'style': 'pointer-events: none; background-color: #343a40 !important; color: #ffffff !important; border-color: #495057 !important;'
            })
            form.fields['fk_terapeuta'].queryset = form.fields['fk_terapeuta'].queryset.filter(pk=terapeuta.pk_terapeuta)
            
        except (Associado.DoesNotExist, Terapeuta.DoesNotExist):
            # Se não encontrar terapeuta, permitir seleção livre (para staff)
            pass
        
        return form
    
    def form_valid(self, form):
        altadesistencia = form.save(commit=False)
        
        try:
            associado = Associado.objects.get(usuario=self.request.user)
            terapeuta = Terapeuta.objects.get(fk_associado=associado)
            altadesistencia.fk_terapeuta = terapeuta
        except (Associado.DoesNotExist, Terapeuta.DoesNotExist):
            if not altadesistencia.fk_terapeuta:
                messages.error(self.request, 'Erro: Terapeuta não foi definido corretamente.')
                return self.form_invalid(form)
        
        altadesistencia.save()
        messages.success(self.request, 'Alta/Desistência cadastrada com sucesso!')
        
        return redirect(self.success_url)


# API VIEWS OTIMIZADAS
class ConsultaListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.ConsultaSerializer
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    
    def get_queryset(self):
        # Otimização: Buscar dados relacionados nas APIs
        return models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente',
            'fk_terapeuta__fk_associado',
            'fk_terapeuta__fk_abordagem',
            'fk_terapeuta__fk_clinica'
        )


class ConsultaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ConsultaSerializer
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    
    def get_queryset(self):
        return models.Consulta.objects.select_related(
            'fk_terapeuta',
            'fk_paciente',
            'fk_terapeuta__fk_associado',
            'fk_terapeuta__fk_abordagem',
            'fk_terapeuta__fk_clinica'
        )


class TerapeutaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    serializer_class = serializers.TerapeutaSerializer
    
    def get_queryset(self):
        # Otimização: Buscar dados relacionados + estatísticas
        return models.Terapeuta.objects.select_related(
            'fk_associado',
            'fk_abordagem',
            'fk_clinica',
            'fk_decano'
        ).annotate(
            total_consultas=Count('consulta'),
            total_pacientes=Count('consulta__fk_paciente', distinct=True)
        )


class TerapeutaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    serializer_class = serializers.TerapeutaSerializer
    
    def get_queryset(self):
        return models.Terapeuta.objects.select_related(
            'fk_associado',
            'fk_abordagem',
            'fk_clinica',
            'fk_decano'
        ).annotate(
            total_consultas=Count('consulta'),
            total_pacientes=Count('consulta__fk_paciente', distinct=True)
        )


class PacienteListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Paciente.objects.select_related('fk_clinica', 'fk_captacao', 'fk_modalidade')
    serializer_class = serializers.PacienteSerializer


class PacienteRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Paciente.objects.select_related('fk_clinica', 'fk_captacao', 'fk_modalidade')
    serializer_class = serializers.PacienteSerializer


class AvaliacaoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Avaliacao.objects.select_related('fk_terapeuta__fk_associado', 'fk_paciente')
    serializer_class = serializers.AvaliacaoSerializer


class AvaliacaoRetrieveUpdateDestroyAPIView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Avaliacao.objects.select_related('fk_terapeuta__fk_associado', 'fk_paciente')
    serializer_class = serializers.AvaliacaoSerializer


class AltadesistenciaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Altadesistencia.objects.select_related('fk_terapeuta__fk_associado', 'fk_paciente')
    serializer_class = serializers.AltadesistenciaSerializer


class AltadesistenciaRetrieveUpdateDestroyAPIView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = models.Altadesistencia.objects.select_related('fk_terapeuta__fk_associado', 'fk_paciente')
    serializer_class = serializers.AltadesistenciaSerializer
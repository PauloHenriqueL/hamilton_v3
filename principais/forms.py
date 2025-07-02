from django import forms
from django.core.exceptions import ObjectDoesNotExist
from . import models 
import logging

logger = logging.getLogger('principais')
class ConsultaForm(forms.ModelForm):
    
    class Meta:
        model = models.Consulta
        fields = [
            'fk_terapeuta', 
            'fk_paciente', 
            'vlr_consulta',
            'vlr_pago',
        ]
        widgets = {
            'vlr_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fk_terapeuta': forms.Select(attrs={'class': 'form-control'}),
            'fk_paciente': forms.Select(attrs={'class': 'form-control', 'id': 'paciente-select'}),
            'vlr_consulta': forms.NumberInput(attrs={'class': 'form-control', 'id': 'valor-consulta'}),
        }
        labels = {
            'fk_terapeuta': 'Terapeuta', 
            'fk_paciente': 'Paciente', 
            'vlr_consulta': 'Valor da consulta',
        }

    quantidade = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        required=False,
        label='Quantidade de consultas'
    )
    
    vlr_pix_total = forms.DecimalField(
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label='Valor total recebido no PIX'
    )
    
    def __init__(self, *args, **kwargs):
        # Extrair parâmetros customizados antes de chamar super()
        user_terapeuta = kwargs.pop('user_terapeuta', None)
        super().__init__(*args, **kwargs)
        
        logger.info(f"Inicializando formulário. user_terapeuta: {user_terapeuta}")
        
        # Se um terapeuta foi passado para o formulário, configurar os campos
        if user_terapeuta:
            logger.info(f"Configurando terapeuta: {user_terapeuta.pk_terapeuta} - {user_terapeuta.nome}")
            
            # Definir o valor inicial e desabilitar o campo
            self.fields['fk_terapeuta'].initial = user_terapeuta.pk_terapeuta
            self.fields['fk_terapeuta'].widget.attrs.update({
                'disabled': 'disabled',
                'readonly': 'readonly'
            })
            
            logger.info(f"Campo terapeuta configurado. Initial: {self.fields['fk_terapeuta'].initial}")
        
        # Se o formulário for preenchido com dados POST e tiver paciente selecionado
        if args and isinstance(args[0], dict) and 'fk_paciente' in args[0]:
            paciente_id = args[0].get('fk_paciente')
            if paciente_id:
                try:
                    paciente = models.Paciente.objects.get(pk=paciente_id)
                    self.fields['vlr_consulta'].initial = paciente.vlr_sessao
                    logger.info(f"Valor da consulta definido automaticamente: {paciente.vlr_sessao}")
                except ObjectDoesNotExist:
                    logger.warning(f"Paciente com ID {paciente_id} não encontrado")
    
    def clean(self):
        cleaned_data = super().clean()
        vlr_consulta = cleaned_data.get('vlr_consulta')
        
        # Validação de valores positivos
        if vlr_consulta is not None and vlr_consulta <= 0:
            self.add_error('vlr_consulta', 'O valor da consulta deve ser positivo.')
        
        return cleaned_data


class AltaDesistenciaForm(forms.ModelForm):
    
    class Meta:
        model = models.Altadesistencia
        fields = [
            'fk_terapeuta', 
            'fk_paciente', 
            'dat_sessao',
            'alta_desistencia',
            'cancelador',
            'motivo_cancel',
            'momento',
        ]
        widgets = {
            'fk_terapeuta': forms.Select(attrs={'class': 'form-control'}),
            'fk_paciente': forms.Select(attrs={'class': 'form-control'}),
            'dat_sessao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'alta_desistencia': forms.Select(attrs={'class': 'form-control'}),
            'cancelador': forms.Select(attrs={'class': 'form-control'}),
            'motivo_cancel': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'momento': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'fk_terapeuta': 'Terapeuta', 
            'fk_paciente': 'Paciente', 
            'dat_sessao': 'Data da Sessão',
            'alta_desistencia': 'Alta ou Desistência',
            'cancelador': 'Quem cancelou?',
            'motivo_cancel': 'Motivo do Cancelamento',
            'momento': 'Quando ocorreu?',
        }
    
    def __init__(self, *args, **kwargs):

        user_terapeuta = kwargs.pop('user_terapeuta', None)
        super().__init__(*args, **kwargs)

        if user_terapeuta:
            self.fields['fk_terapeuta'].initial = user_terapeuta.pk_terapeuta
            self.fields['fk_terapeuta'].widget.attrs.update({
                'disabled': 'disabled',
                'readonly': 'readonly'
            })
            self.fields['fk_terapeuta'].required = False



class MatchForm(forms.ModelForm):
    
    class Meta:
        model = models.Match
        fields = [
            'fk_terapeuta', 
            'fk_paciente', 
            'dat_consulta',
        ]
        widgets = {
            'fk_terapeuta': forms.Select(attrs={'class': 'form-control'}),
            'fk_paciente': forms.Select(attrs={'class': 'form-control'}),
            'dat_consulta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'fk_terapeuta': 'Terapeuta', 
            'fk_paciente': 'Paciente', 
            'dat_consulta': 'Data da Sessão',
        }
    
    def __init__(self, *args, **kwargs):
        # Extrair parâmetros customizados antes de chamar super()
        user_terapeuta = kwargs.pop('user_terapeuta', None)
        super().__init__(*args, **kwargs)
        
        # Se um terapeuta foi passado para o formulário, configurar os campos
        if user_terapeuta:
            # Definir o valor inicial e desabilitar o campo
            self.fields['fk_terapeuta'].initial = user_terapeuta.pk_terapeuta
            self.fields['fk_terapeuta'].widget.attrs.update({
                'disabled': 'disabled',
                'readonly': 'readonly'
            })
            
            # IMPORTANTE: Marcar o campo como não obrigatório quando desabilitado
            self.fields['fk_terapeuta'].required = False



def clean(self):
    cleaned_data = super().clean()
    vlr_consulta = cleaned_data.get('vlr_consulta')
    vlr_pago = cleaned_data.get('vlr_pago')
    is_realizado = cleaned_data.get('is_realizado')
    is_pago = cleaned_data.get('is_pago')
    
    # Validação de valores positivos
    if vlr_consulta is not None and vlr_consulta <= 0:
        self.add_error('vlr_consulta', 'O valor da consulta deve ser positivo.')
    
    if vlr_pago is not None and vlr_pago < 0:
        self.add_error('vlr_pago', 'O valor pago não pode ser negativo.')
    
    # Consultas não realizadas não podem estar pagas
    if is_realizado is False and is_pago is True:
        self.add_error('is_pago', 'Uma consulta não realizada não pode estar paga.')
    
    return cleaned_data





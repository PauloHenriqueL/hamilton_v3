from rest_framework import serializers
from .models import (
    Captacao, Clinica, Modalidade, Nucleo, 
    Abordagem, Setor
)


class CaptacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Captacao
        fields = '__all__'
        read_only_fields = ('pk_captacao', 'created_at', 'updated_at')


class ClinicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinica
        fields = '__all__'
        read_only_fields = ('pk_clinica', 'created_at', 'updated_at')


class ModalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modalidade
        fields = '__all__'
        read_only_fields = ('pk_modalidade', 'created_at', 'updated_at')


class NucleoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nucleo
        fields = '__all__'
        read_only_fields = ('pk_nucleo', 'created_at', 'updated_at')


class AbordagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abordagem
        fields = '__all__'
        read_only_fields = ('pk_abordagem', 'created_at', 'updated_at')


class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = '__all__'
        read_only_fields = ('pk_setor', 'created_at', 'updated_at')

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Captacao(models.Model):
    pk_captacao = models.AutoField(primary_key=True, verbose_name="ID")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.nome

    class Meta:
        db_table = "captacoes"
        verbose_name = "Captação"
        verbose_name_plural = "Captações"


class Clinica(models.Model):
    pk_clinica = models.AutoField(primary_key=True, verbose_name="ID")
    clinica = models.CharField(max_length=10, verbose_name="Clínica")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.clinica

    class Meta:
        db_table = "clinicas"
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"


class Modalidade(models.Model):
    pk_modalidade = models.AutoField(primary_key=True, verbose_name="ID")
    modalidade = models.CharField(max_length=10, verbose_name="Modalidade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.modalidade
    
    class Meta:
        db_table = "modalidades"
        verbose_name = "Modalidade"
        verbose_name_plural = "Modalidades"


class Nucleo(models.Model):
    pk_nucleo = models.AutoField(primary_key=True, verbose_name="ID")
    nucleo = models.CharField(max_length=30, verbose_name="Núcleo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.nucleo

    class Meta:
        db_table = "nucleos"
        verbose_name = "Núcleo"
        verbose_name_plural = "Núcleos"


class Abordagem(models.Model):
    pk_abordagem = models.AutoField(primary_key=True, verbose_name="ID")
    abordagem = models.CharField(max_length=255, verbose_name="Abordagem")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.abordagem

    class Meta:
        db_table = "abordagens"
        verbose_name = "Abordagem"
        verbose_name_plural = "Abordagens"


class Setor(models.Model):
    pk_setor = models.AutoField(primary_key=True, verbose_name="ID")
    setor = models.CharField(max_length=255, verbose_name="Setor")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.setor

    class Meta:
        db_table = "setores"
        verbose_name = "Setor"
        verbose_name_plural = "Setores"


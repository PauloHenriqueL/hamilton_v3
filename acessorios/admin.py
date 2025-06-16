from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import (
    Captacao, Clinica, Modalidade, Nucleo, 
    Abordagem, Setor
)


@admin.register(Captacao)
class CaptacaoAdmin(admin.ModelAdmin):
    list_display = ('pk_captacao', 'nome', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('nome',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'is_active')
        }),
    )


@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('pk_clinica', 'clinica', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('clinica',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('clinica',)
        }),
    )


@admin.register(Modalidade)
class ModalidadeAdmin(admin.ModelAdmin):
    list_display = ('pk_modalidade', 'modalidade', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('modalidade',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('modalidade',)
        }),
    )


@admin.register(Nucleo)
class NucleoAdmin(admin.ModelAdmin):
    list_display = ('pk_nucleo', 'nucleo', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('nucleo',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nucleo',)
        }),
    )


@admin.register(Abordagem)
class AbordagemAdmin(admin.ModelAdmin):
    list_display = ('pk_abordagem', 'abordagem', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('abordagem',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('abordagem',)
        }),
    )


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('pk_setor', 'setor', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('setor',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('setor',)
        }),
    )

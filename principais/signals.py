from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Altadesistencia
import logging

logger = logging.getLogger('principais')

@receiver(post_save, sender=Altadesistencia)
def desativar_paciente_alta_desistencia(sender, instance, created, **kwargs):
    """
    Signal que desativa automaticamente o paciente quando uma alta/desistência é cadastrada
    """
    if created:  # Só executa quando um NOVO registro é criado (não em updates)
        try:
            # Pega o paciente relacionado à alta/desistência
            paciente = instance.fk_paciente
            
            # Desativa o paciente
            paciente.is_active = False
            paciente.save(update_fields=['is_active', 'updated_at'])
            
            # Log para acompanhamento
            logger.info(
                f"Paciente '{paciente.nome}' (ID: {paciente.pk_paciente}) "
                f"foi DESATIVADO automaticamente devido à alta/desistência "
                f"cadastrada pelo terapeuta '{instance.fk_terapeuta.nome}'"
            )
            
        except Exception as e:
            # Log de erro caso algo dê errado
            logger.error(
                f"ERRO ao desativar paciente na alta/desistência ID {instance.pk_alta_desistencia}: {str(e)}"
            )

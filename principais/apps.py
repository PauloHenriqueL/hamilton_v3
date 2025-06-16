from django.apps import AppConfig


class PrincipaisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'principais'

    def ready(self):
        """Importa os signals quando a aplicação está pronta"""
        import principais.signals

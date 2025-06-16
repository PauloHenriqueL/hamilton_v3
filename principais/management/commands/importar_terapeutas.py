import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.db import transaction

class Command(BaseCommand):
    help = 'Importa terapeutas a partir de um arquivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('arquivo_csv', type=str, help='Caminho para o arquivo CSV com os dados dos terapeutas')

    def handle(self, *args, **options):
        arquivo_csv = options['arquivo_csv']
        
        # Verificar se o arquivo existe
        if not os.path.exists(arquivo_csv):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {arquivo_csv}'))
            return
            
        try:
            # Carregar o CSV com encoding CP1252 (Windows Latin-1)
            df = pd.read_csv(arquivo_csv, encoding='cp1252')
            self.stdout.write(self.style.SUCCESS(f'Arquivo carregado com sucesso. {len(df)} registros encontrados.'))
            
            # Verificar ou criar o grupo de Terapeutas
            terapeuta_group, created = Group.objects.get_or_create(name='Terapeuta')
            if created:
                self.stdout.write(self.style.SUCCESS('Grupo de Terapeutas criado'))
            
            # Estatísticas
            usuarios_criados = 0
            usuarios_atualizados = 0
            erros = 0
            
            # Processar cada linha do CSV dentro de uma transação
            with transaction.atomic():
                for i, row in df.iterrows():
                    try:
                        nome_completo = row['NOME'].strip()
                        username = row['USUARIO'].strip()
                        senha = row['SENHA'].strip()
                        
                        # Dividir o nome completo em primeiro nome e sobrenome
                        partes_nome = nome_completo.split()
                        primeiro_nome = partes_nome[0] if partes_nome else ''
                        sobrenome = ' '.join(partes_nome[1:]) if len(partes_nome) > 1 else ''
                        
                        # Verificar se o usuário já existe
                        try:
                            usuario = User.objects.get(username=username)
                            # Atualizar usuário existente
                            usuario.first_name = primeiro_nome
                            usuario.last_name = sobrenome
                            usuario.set_password(senha)
                            usuario.save()
                            
                            # Adicionar ao grupo de Terapeutas se ainda não estiver
                            if terapeuta_group not in usuario.groups.all():
                                usuario.groups.add(terapeuta_group)
                            
                            usuarios_atualizados += 1
                            self.stdout.write(f"Usuário atualizado: {username}")
                        
                        except User.DoesNotExist:
                            # Criar novo usuário
                            usuario = User.objects.create(
                                username=username,
                                password=make_password(senha),  # Criptografa a senha
                                first_name=primeiro_nome,
                                last_name=sobrenome,
                                is_active=True,
                                is_staff=True,  # Permissão para acessar a área de administração
                                is_superuser=False  # Não é um superusuário
                            )
                            
                            # Adicionar ao grupo de Terapeutas
                            usuario.groups.add(terapeuta_group)
                            
                            usuarios_criados += 1
                            self.stdout.write(f"Usuário criado: {username}")
                    
                    except Exception as e:
                        erros += 1
                        self.stdout.write(self.style.ERROR(f"Erro ao processar linha {i+1} ({nome_completo}): {str(e)}"))
            
            # Mostrar resumo
            self.stdout.write(self.style.SUCCESS("\nImportação concluída!"))
            self.stdout.write(f"Usuários criados: {usuarios_criados}")
            self.stdout.write(f"Usuários atualizados: {usuarios_atualizados}")
            self.stdout.write(f"Erros: {erros}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar o arquivo: {e}"))
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from acessorios.models import Abordagem, Nucleo, Clinica, Modalidade, Captacao, Setor
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import re
from django.core.exceptions import ValidationError


def validar_cpf(cpf):
    cpf = re.sub(r'[.-]', '', cpf)
    
    if len(cpf) != 11 or not cpf.isdigit():
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    if digito1 == 10:
        digito1 = 0
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    if digito2 == 10:
        digito2 = 0
    
    if cpf[-2:] != f"{digito1}{digito2}":
        raise ValidationError('CPF inválido.')

telefone_validator = RegexValidator(
    regex=r'^\d{10,11}$',
    message="O telefone deve conter 10 ou 11 dígitos numéricos. Exemplo: 31988553344"
)

class Associado(models.Model):
    pk_associado = models.AutoField(primary_key=True, verbose_name="ID")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    
    # Relacionamento Many-to-Many com Setores
    setores = models.ManyToManyField(
        Setor,
        verbose_name="Setores",
        help_text="Selecione um ou mais setores para este associado"
    )
    
    email = models.EmailField(
        unique=True, 
        verbose_name="E-mail",
        validators=[EmailValidator(message="Informe um endereço de e-mail válido.")]
    )
    faculdade = models.CharField(max_length=255, verbose_name="Faculdade")

    telefone = models.CharField(
        max_length=20, 
        verbose_name="Telefone", 
        help_text="Exemplo: 31988553344 Não coloque +55/espaços/parênteses",
        validators=[telefone_validator]
    )
    contato_apoio = models.CharField(
        null=True, 
        blank=True, 
        max_length=20, 
        verbose_name="Telefone do Contato de Apoio",
        validators=[telefone_validator]
    )
    dat_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    sexo = models.CharField(
        max_length=1, 
        choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')],
        verbose_name="Sexo"
    )
    cpf = models.CharField(
        max_length=14, 
        unique=True, 
        verbose_name='CPF',
        validators=[validar_cpf],
        help_text='Exemplo: 123.456.789-01'
    )
    endereco = models.CharField(
        max_length=100, 
        verbose_name='Endereço',
        help_text='Exemplo: MG, Belo Horizonte'
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    observacao = models.TextField(null=True, blank=True, verbose_name="Observações")
    
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário",
        help_text="Usuário vinculado ao associado (opcional)"
    )
 
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        ordering = ['nome']
        db_table = "associados"
        verbose_name = "Associado"
        verbose_name_plural = "Associados"
    
    def __str__(self):
        return self.nome
    
    @property
    def is_decano(self):
        """Verifica se o associado é um decano"""
        return self.setores.filter(setor__icontains='decano').exists()
    
    
    @classmethod
    def get_decanos(cls):
        """Retorna todos os associados que são decanos"""
        return cls.objects.filter(setores__setor__icontains='decano', is_active=True).distinct()

    

class Paciente(models.Model):
    pk_paciente = models.AutoField(primary_key=True, verbose_name="ID")
    fk_clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE, 
        db_column='fk_clinica',
        verbose_name="Clínica"
    )
    fk_captacao = models.ForeignKey(
        Captacao,
        on_delete=models.CASCADE, 
        db_column='fk_captacao',
        verbose_name="Captação"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome")
    
    fk_modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.CASCADE, 
        db_column='fk_modalidade',
        verbose_name="Modalidade"
    )

    email = models.EmailField(
        blank=True, 
        null=True, 
        verbose_name="E-mail",
        validators=[EmailValidator(message="Informe um endereço de e-mail válido.")]
    )

    telefone = models.CharField(
        max_length=20, 
        verbose_name="Telefone do Paciente", 
        help_text="Exemplo: 31988553344 Não coloque +55/espaços/parênteses",
        validators=[telefone_validator]
    )
    
    nome_contato_apoio = models.CharField(null=True, blank=True, max_length=200, verbose_name="Nome do Contato de Apoio")
    parentesco_contato_apoio = models.CharField(null=True, blank=True, max_length=200, verbose_name="Parentesco do Contato de Apoio")
    
    contato_apoio = models.CharField(
        null=True, 
        blank=True, 
        max_length=20, 
        verbose_name="Telefone do Contato de Apoio",
        validators=[telefone_validator]
    )
    
    dat_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    vlr_sessao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Acordado")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    observacao = models.TextField(null=True, blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']
        db_table = "pacientes"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"


class Terapeuta(models.Model):
    pk_terapeuta = models.AutoField(primary_key=True, verbose_name="ID")
    fk_associado = models.ForeignKey(
        Associado, 
        on_delete=models.CASCADE, 
        db_column='fk_associado',
        verbose_name="Associado"
    )
    
    # Decano agora é um Associado que tem setor "Decano"
    fk_decano = models.ForeignKey(
        Associado,
        on_delete=models.CASCADE, 
        db_column='fk_decano',
        verbose_name="Decano",
        related_name="terapeutas_supervisionados",
        limit_choices_to={'setores__setor__icontains': 'decano', 'is_active': True}
    )
    
    fk_abordagem = models.ForeignKey(
        Abordagem,
        on_delete=models.CASCADE, 
        db_column='fk_abordagem',
        verbose_name="Abordagem"
    )
    fk_nucleo = models.ForeignKey(
        Nucleo,
        on_delete=models.CASCADE, 
        db_column='fk_nucleo',
        verbose_name="Núcleo"
    )
    fk_clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE, 
        db_column='fk_clinica',
        verbose_name="Clínica"
    )
    fk_modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.CASCADE, 
        db_column='fk_modalidade',
        verbose_name="Modalidade"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        ordering = ['fk_associado__nome']
        db_table = "terapeutas"
        verbose_name = "Terapeuta"
        verbose_name_plural = "Terapeutas"
    
    def __str__(self):
        return f"{self.fk_associado.nome} (Decano: {self.fk_decano.nome})"


class Consulta(models.Model):
    pk_consulta = models.AutoField(primary_key=True, verbose_name="ID")
    fk_terapeuta = models.ForeignKey(
        Terapeuta, 
        on_delete=models.CASCADE, 
        db_column='fk_terapeuta',
        verbose_name="Terapeuta"
    )
    fk_paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        db_column='fk_paciente',
        verbose_name="Paciente"
    )
    vlr_consulta = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor da Consulta"
    )   
    is_realizado = models.BooleanField(null=True, blank=True, verbose_name="Realizada")
    vlr_pago = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Valor Pago"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    dat_consulta = models.DateField(verbose_name="Data da Consulta")

    class Meta:
        db_table = "consultas"
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        constraints = [
            models.CheckConstraint(
                check=models.Q(vlr_pago__gte=0),
                name='check_vlr_pago_greater_equal_0'
            ),
        ]
    
    def __str__(self):
        return f"Consulta do {self.fk_paciente} pelo {self.fk_terapeuta}"


class Altadesistencia(models.Model):
    pk_alta_desistencia = models.AutoField(primary_key=True, verbose_name="ID")
    fk_terapeuta = models.ForeignKey(
        Terapeuta, 
        on_delete=models.CASCADE, 
        db_column='fk_terapeuta',
        verbose_name="Terapeuta"
    )
    fk_paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        db_column='fk_paciente',
        verbose_name="Paciente"
    )
    dat_sessao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da Sessão"
    )
    cancelador = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ('paciente', 'Paciente'),
            ('terapeuta', 'Terapeuta'),
        ],
        verbose_name="Cancelador"
    )
    motivo_cancel = models.TextField(
        null=True,
        blank=True,
        verbose_name="Motivo do Cancelamento"
    )
    momento = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=[
            ('Antes da primeira sessão', 'Antes da primeira sessão'),
            ('Depois da primeira sessão', 'Depois da primeira sessão'),
        ],
        verbose_name="Momento"
    )
    alta_desistencia = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ('alta', 'Alta'),
            ('desistencia', 'Desistencia'),
        ],
        verbose_name="Alta ou Desistencia"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        db_table = "altadesistencia"
        verbose_name = "Altadesistencia"
        verbose_name_plural = "Altadesistencia"


class Avaliacao(models.Model):
    pk_avaliacao = models.AutoField(primary_key=True, verbose_name="ID")
    fk_terapeuta = models.ForeignKey(
        Terapeuta, 
        on_delete=models.CASCADE, 
        db_column='fk_terapeuta',
        verbose_name="Terapeuta"
    )
    fk_paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        db_column='fk_paciente',
        verbose_name="Paciente"
    )
    dat_consulta = models.DateField(verbose_name="Data da última sessão")
    
    consentimento_paciente = models.BooleanField(
        null=True, 
        blank=True,
        default=False, 
        verbose_name="Consentimento do Paciente"
    )
    individual = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Bem-estar Pessoal (0-10)"
    )
    interpessoal = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Família/Relacionamentos Íntimos (0-10)"
    )
    social = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Trabalho/Faculdade/Família (0-10)"
    )
    geral = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Estado Geral de Bem-estar (0-10)"
    )
    qualidade_geral = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Qualidade geral do atendimento (0-10)"
    )
    continuar_terapeuta = models.BooleanField(
        default=False,
        verbose_name="Deseja continuar com o mesmo terapeuta"
    )
    continuar_allos = models.BooleanField(
        default=False,
        verbose_name="Deseja continuar sendo atendido na Allos"
    )
    momento = models.CharField(
        max_length=100,
        choices=[
            ('No início do processo (primeira sessão)', 'No início do processo (primeira sessão)'),
            ('Durante o acompanhamento terapêutico', 'Durante o acompanhamento terapêutico'),
            ('Após o encerramento da terapia', 'Após o encerramento da terapia'),
        ],
        verbose_name="Momento"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        db_table = "avaliação"
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
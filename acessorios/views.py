from rest_framework import generics
from . import models
from . import serializers
from rest_framework.permissions import IsAuthenticated
from app.permissions import GlobalDefaultPermission
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from principais.models import Terapeuta, Consulta



# ===== API VIEWS =====

# Abordagem Views
class AbordagemListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Abordagem.objects.all()
    serializer_class = serializers.AbordagemSerializer


class AbordagemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Abordagem.objects.all()
    serializer_class = serializers.AbordagemSerializer


# Captação Views
class CaptacaoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Captacao.objects.all()
    serializer_class = serializers.CaptacaoSerializer


class CaptacaoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Captacao.objects.all()
    serializer_class = serializers.CaptacaoSerializer


# Clínica Views
class ClinicaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Clinica.objects.all()
    serializer_class = serializers.ClinicaSerializer


class ClinicaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Clinica.objects.all()
    serializer_class = serializers.ClinicaSerializer


# Modalidade Views
class ModalidadeListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Modalidade.objects.all()
    serializer_class = serializers.ModalidadeSerializer


class ModalidadeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Modalidade.objects.all()
    serializer_class = serializers.ModalidadeSerializer


# Núcleo Views
class NucleoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Nucleo.objects.all()
    serializer_class = serializers.NucleoSerializer


class NucleoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Nucleo.objects.all()
    serializer_class = serializers.NucleoSerializer


# Setor Views
class SetorListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Setor.objects.all()
    serializer_class = serializers.SetorSerializer


class SetorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = models.Setor.objects.all()
    serializer_class = serializers.SetorSerializer


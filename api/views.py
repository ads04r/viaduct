"""
API view definitions.

Defines DRF viewsets that expose User and GraphModel resources.
"""

from django.shortcuts import get_object_or_404
from .models.user import User
from .models.arches import ArchesInstance, GraphModel, Thesaurus
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .serializers import UserSerializer, ArchesInstanceSerializer, GraphModelSerializer, GraphModelCondensedSerializer, ThesaurusSerializer, CompleteThesaurusSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
	"""
	ViewSet for listing and managing users.

	- queryset: returns all users ordered by date_joined descending.
	- serializer_class: UserSerializer
	- permission_classes: requires authentication

	Example::

		GET /api/users/  -> list users (authenticated)
	"""
	queryset = User.objects.all().order_by("-date_joined")
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated]

class ArchesInstanceViewSet(viewsets.ModelViewSet):
	queryset = ArchesInstance.objects.all()
	serializer_class = ArchesInstanceSerializer
	permission_classes = [permissions.IsAuthenticated]

class GraphModelViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = GraphModel.objects.all()
	serializer_class = GraphModelCondensedSerializer
	permission_classes = [permissions.IsAuthenticated]
	def list(self, request):
		queryset = GraphModel.objects.all()
		serializer = GraphModelCondensedSerializer(queryset, many=True)
		return Response(serializer.data)
	def retrieve(self, request, pk=None):
		queryset = GraphModel.objects.all()
		instance = get_object_or_404(queryset, pk=pk)
		serializer = GraphModelSerializer(instance, context={'request': request})
		return Response(serializer.data)

class ThesaurusViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Thesaurus.objects.all()
	permission_classes = [permissions.IsAuthenticated]
	def get_serializer_class(self):
		if self.action == 'retrieve':
			return CompleteThesaurusSerializer
		return ThesaurusSerializer

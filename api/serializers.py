"""
Serializers for the api application.

Contains HyperlinkedModelSerializer implementations for exposed resources.
"""

from .models.user import User
from .models.arches import GraphModel, ArchesInstance, Thesaurus
from .importers.arches import load_instance_models, load_instance_thesauri
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for User model exposing url and username fields.

    Fields:
    - url: hyperlinked identity
    - username: Django username
    """
    class Meta:
        model = User
        fields = ['url', 'username']

class ArchesInstanceSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for Arches instances that are searchable with this
    instance of Viaduct
    """
    def create(self, validated_data):
        instance = ArchesInstance.objects.create(**validated_data)
        load_instance_models(instance)
        load_instance_thesauri(instance)
        return instance
    class Meta:
        model = ArchesInstance
        fields = ['label', 'url', 'models', 'thesauri']
        read_only_fields = ['models', 'thesauri']

class GraphModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for GraphModel objects exposing a small subset of fields.

    Fields:
    - url: hyperlinked identity
    - name: human readable name
    - description: short description text
    """
    schema = serializers.SerializerMethodField('get_schema')
    def get_schema(self, instance):
        return instance.load_schema()
    class Meta:
        model = GraphModel
        fields = ['url', 'name', 'description', 'export_url', 'schema']

class GraphModelCondensedSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for GraphModel objects exposing a small subset of fields.

    Fields:
    - url: hyperlinked identity
    - name: human readable name
    - description: short description text
    """
    class Meta:
        model = GraphModel
        fields = ['url', 'name', 'description', 'export_url']

class ThesaurusSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Thesaurus
		fields = ['label', 'url', 'instance', 'skos_url']

class CompleteThesaurusSerializer(serializers.HyperlinkedModelSerializer):
	concepts = serializers.ListField(source='build_description', read_only=True)
	class Meta:
		model = Thesaurus
		fields = ['label', 'url', 'instance', 'skos_url', 'concepts']
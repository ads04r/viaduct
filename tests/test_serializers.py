# tests/test_serializers.py
import pytest
from api.serializers import (
    UserSerializer, ArchesInstanceSerializer, GraphModelSerializer,
    ThesaurusSerializer, CompleteThesaurusSerializer
)


@pytest.mark.django_db
class TestUserSerializer:
    """Test UserSerializer."""
    
    def test_serialize_user(self, user):
        """Test serializing a User instance."""
        serializer = UserSerializer(user, context={'request': None})
        data = serializer.data
        assert 'url' in data
        assert data['username'] == 'testuser'


@pytest.mark.django_db
class TestArchesInstanceSerializer:
    """Test ArchesInstanceSerializer."""
    
    def test_serialize_instance(self, arches_instance):
        """Test serializing an ArchesInstance."""
        serializer = ArchesInstanceSerializer(arches_instance, context={'request': None})
        data = serializer.data
        assert data['label'] == 'Test Instance'
        assert data['url'] == 'https://test.arches.example.com'


@pytest.mark.django_db
class TestGraphModelSerializer:
    """Test GraphModelSerializer."""
    
    def test_serialize_model(self, graph_model):
        """Test serializing a GraphModel."""
        serializer = GraphModelSerializer(graph_model, context={'request': None})
        data = serializer.data
        assert 'url' in data
        assert data['name'] == 'Test Model'
        assert 'export_url' in data


@pytest.mark.django_db
class TestThesaurusSerializer:
    """Test ThesaurusSerializer."""
    
    def test_serialize_thesaurus(self, thesaurus):
        """Test serializing a Thesaurus."""
        serializer = ThesaurusSerializer(thesaurus, context={'request': None})
        data = serializer.data
        assert data['label'] == 'Test Thesaurus'
        assert 'skos_url' in data


@pytest.mark.django_db
class TestCompleteThesaurusSerializer:
    """Test CompleteThesaurusSerializer."""
    
    def test_serialize_thesaurus_with_concepts(self, thesaurus, concept):
        """Test serializing thesaurus with concepts."""
        serializer = CompleteThesaurusSerializer(thesaurus, context={'request': None})
        data = serializer.data
        assert data['label'] == 'Test Thesaurus'
        assert 'concepts' in data

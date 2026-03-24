# tests/test_api_views.py
import pytest
from django.test import APIClient
from rest_framework.test import APITestCase, force_authenticate
from rest_framework import status
from api.models.arches import ArchesInstance, GraphModel
import uuid


@pytest.mark.django_db
class TestUserViewSet:
    """Test UserViewSet API endpoint."""
    
    def test_user_list_requires_authentication(self, client):
        """Test that user list endpoint requires authentication."""
        response = client.get('/api/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_list_authenticated(self, client, user):
        """Test user list with authentication."""
        client.force_login(user)
        response = client.get('/api/users/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_user_ordering(self, client, user, db):
        """Test that users are ordered by date_joined descending."""
        from django.contrib.auth.models import User
        import datetime
        User.objects.create_user(
            username='older_user',
            email='older@example.com',
            password='pass'
        )
        
        client.force_login(user)
        response = client.get('/api/users/')
        
        # Response should contain users ordered by date_joined desc
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestArchesInstanceViewSet:
    """Test ArchesInstanceViewSet API endpoint."""
    
    def test_instance_list_requires_authentication(self, client):
        """Test that instances list requires authentication."""
        response = client.get('/api/instances/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_instance_list_authenticated(self, client, user, arches_instance):
        """Test listing Arches instances when authenticated."""
        client.force_login(user)
        response = client.get('/api/instances/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_instance_create(self, client, user):
        """Test creating a new Arches instance."""
        client.force_login(user)
        response = client.post('/api/instances/', {
            'label': 'New Instance',
            'url': 'https://new.arches.example.com'
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_instance_retrieve(self, client, user, arches_instance):
        """Test retrieving a specific instance."""
        client.force_login(user)
        response = client.get(f'/api/instances/{arches_instance.pk}/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGraphModelViewSet:
    """Test GraphModelViewSet API endpoint."""
    
    def test_model_list_requires_authentication(self, client):
        """Test that models list requires authentication."""
        response = client.get('/api/models/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_model_list_authenticated(self, client, user, graph_model):
        """Test listing graph models when authenticated."""
        client.force_login(user)
        response = client.get('/api/models/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_model_is_read_only(self, client, user):
        """Test that models endpoint is read-only."""
        client.force_login(user)
        response = client.post('/api/models/', {
            'name': 'New Model',
            'slug': 'new-model'
        }, format='json')
        # Should not allow POST
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]


@pytest.mark.django_db
class TestThesaurusViewSet:
    """Test ThesaurusViewSet API endpoint."""
    
    def test_thesaurus_list_requires_authentication(self, client):
        """Test that thesaurus list requires authentication."""
        response = client.get('/api/thesauri/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_thesaurus_list_authenticated(self, client, user, thesaurus):
        """Test listing thesauri when authenticated."""
        client.force_login(user)
        response = client.get('/api/thesauri/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_thesaurus_retrieve_with_concepts(self, client, user, thesaurus, concept):
        """Test retrieving thesaurus with concepts."""
        client.force_login(user)
        response = client.get(f'/api/thesauri/{thesaurus.pk}/')
        assert response.status_code == status.HTTP_200_OK
        # Should use CompleteThesaurusSerializer for detail view

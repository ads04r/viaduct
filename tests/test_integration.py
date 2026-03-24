# tests/test_integration.py
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.models.arches import ArchesInstance, GraphModel, Thesaurus, Concept


@pytest.mark.django_db
class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    def test_keyword_search_flow(self, arches_instance, client, user):
        """Test complete keyword search flow."""
        client.force_login(user)
        
        # Mock the actual Arches API call
        with patch.object(ArchesInstance, 'keyword_search', return_value=[]):
            from search.views import home
            factory = pytest.RequestFactory()
            request = factory.post('/', {'q': 'test'})
            request.user = user
            
            response = home(request)
            assert response.status_code == 200
    
    def test_concept_search_with_properties(self, thesaurus, concept):
        """Test concept search with properties."""
        from api.models.arches import ConceptProperty
        from search.util import concept_search
        
        ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Test Label',
            lang='en'
        )
        
        results = concept_search('Test')
        assert len(results) > 0


@pytest.mark.django_db  
class TestModelRelationships:
    """Test model relationships and cascading."""
    
    def test_instance_deletion_cascades(self, arches_instance, graph_model):
        """Test that deleting instance deletes related models."""
        model_id = graph_model.pk
        arches_instance.delete()
        
        assert not GraphModel.objects.filter(pk=model_id).exists()
    
    def test_user_deletion_cascades(self, user):
        """Test that user profile is deleted with user."""
        profile_id = user.profile.pk
        user.delete()
        
        from api.models.user import UserProfile
        assert not UserProfile.objects.filter(pk=profile_id).exists()

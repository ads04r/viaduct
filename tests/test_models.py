# tests/test_models.py
import pytest
import uuid
from django.contrib.auth.models import User
from api.models.user import UserProfile, create_new_userprofile
from api.models.arches import (
    ArchesInstance, ArchesLogin, GraphModel, Thesaurus, Concept,
    ConceptProperty, ConceptPredicate
)


class TestUserProfile:
    """Test UserProfile model and signal handling."""
    
    def test_user_profile_creation_signal(self, user):
        """Test that UserProfile is auto-created when User is created."""
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)
        assert user.profile.user_settings == {}
    
    def test_user_profile_default_factory(self):
        """Test the factory function for default user_settings."""
        result = create_new_userprofile()
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_user_profile_settings_storage(self, user_profile):
        """Test that user_settings can store and retrieve preferences."""
        user_profile.user_settings['theme'] = 'dark'
        user_profile.user_settings['language'] = 'es'
        user_profile.save()
        
        refreshed = UserProfile.objects.get(pk=user_profile.pk)
        assert refreshed.user_settings['theme'] == 'dark'
        assert refreshed.user_settings['language'] == 'es'
    
    def test_user_profile_str_representation(self, user_profile):
        """Test string representation of UserProfile."""
        assert str(user_profile) == 'testuser'


class TestArchesInstance:
    """Test ArchesInstance model."""
    
    def test_arches_instance_creation(self, arches_instance):
        """Test basic ArchesInstance creation."""
        assert arches_instance.label == 'Test Instance'
        assert arches_instance.url == 'https://test.arches.example.com'
    
    def test_arches_instance_str_representation(self, arches_instance):
        """Test string representation."""
        assert str(arches_instance) == 'Test Instance'
    
    def test_arches_instance_timestamps(self, arches_instance):
        """Test that created_time and updated_time are set."""
        assert arches_instance.created_time is not None
        assert arches_instance.updated_time is not None
    
    def test_arches_instance_url_validation(self, db):
        """Test that invalid URLs are rejected."""
        with pytest.raises(Exception):  # Expect ValidationError
            ArchesInstance.objects.create(
                label='Bad Instance',
                url='not-a-valid-url'
            )


class TestArchesLogin:
    """Test ArchesLogin model."""
    
    def test_arches_login_creation(self, user, arches_instance, db):
        """Test ArchesLogin creation with ForeignKeys."""
        login = ArchesLogin.objects.create(
            user=user,
            instance=arches_instance,
            username='arches_user',
            password='arches_pass'
        )
        assert login.user == user
        assert login.instance == arches_instance
    
    def test_arches_login_unique_constraint(self, user, arches_instance, db):
        """Test that user-instance combination must be unique."""
        ArchesLogin.objects.create(
            user=user,
            instance=arches_instance,
            username='user1',
            password='pass1'
        )
        with pytest.raises(Exception):  # IntegrityError
            ArchesLogin.objects.create(
                user=user,
                instance=arches_instance,
                username='user2',
                password='pass2'
            )
    
    def test_arches_login_cascade_delete(self, user, arches_instance, db):
        """Test that login is deleted when instance is deleted."""
        login = ArchesLogin.objects.create(
            user=user,
            instance=arches_instance,
            username='user',
            password='pass'
        )
        arches_instance.delete()
        assert not ArchesLogin.objects.filter(pk=login.pk).exists()


class TestGraphModel:
    """Test GraphModel model."""
    
    def test_graph_model_creation(self, graph_model):
        """Test GraphModel creation with required fields."""
        assert graph_model.name == 'Test Model'
        assert graph_model.slug == 'test-model'
        assert graph_model.instance.label == 'Test Instance'
    
    def test_graph_model_slug_validation(self, arches_instance, db):
        """Test slug field validation."""
        with pytest.raises(Exception):  # ValidationError
            GraphModel.objects.create(
                instance=arches_instance,
                graphid=uuid.uuid4(),
                slug='invalid slug!'  # Contains space and special char
            )
    
    def test_graph_model_unique_constraint(self, arches_instance, db):
        """Test that (instance, graphid) combination is unique."""
        graphid = uuid.uuid4()
        GraphModel.objects.create(
            instance=arches_instance,
            graphid=graphid,
            name='Model 1',
            slug='model-1'
        )
        with pytest.raises(Exception):  # IntegrityError
            GraphModel.objects.create(
                instance=arches_instance,
                graphid=graphid,
                name='Model 2',
                slug='model-2'
            )
    
    def test_graph_model_export_url_property(self, graph_model):
        """Test export_url property formatting."""
        expected = f'https://test.arches.example.com/graph/{graph_model.graphid}/export'
        assert graph_model.export_url == expected
    
    def test_graph_model_str_representation(self, graph_model):
        """Test string representation."""
        assert str(graph_model) == 'Test Instance / Test Model'
    
    def test_graph_model_null_fields(self, arches_instance, db):
        """Test that optional fields can be null."""
        model = GraphModel.objects.create(
            instance=arches_instance,
            graphid=uuid.uuid4(),
            slug='minimal'
        )
        assert model.name is None
        assert model.description is None


class TestThesaurus:
    """Test Thesaurus model."""
    
    def test_thesaurus_creation(self, thesaurus):
        """Test Thesaurus creation."""
        assert thesaurus.label == 'Test Thesaurus'
        assert thesaurus.load_on_demand is False
    
    def test_thesaurus_unique_constraint(self, arches_instance, db):
        """Test that (instance, thesaurusid) is unique."""
        thesaurus_id = uuid.uuid4()
        Thesaurus.objects.create(
            instance=arches_instance,
            thesaurusid=thesaurus_id,
            label='Thesaurus 1'
        )
        with pytest.raises(Exception):
            Thesaurus.objects.create(
                instance=arches_instance,
                thesaurusid=thesaurus_id,
                label='Thesaurus 2'
            )
    
    def test_thesaurus_skos_url_property(self, thesaurus):
        """Test SKOS URL property formatting."""
        expected = f'https://test.arches.example.com/concepts/export/{thesaurus.thesaurusid}'
        assert thesaurus.skos_url == expected
    
    def test_thesaurus_str_representation(self, thesaurus):
        """Test string representation."""
        assert str(thesaurus) == 'Test Instance / Test Thesaurus'


class TestConcept:
    """Test Concept model."""
    
    def test_concept_creation(self, concept):
        """Test Concept creation."""
        assert concept.thesaurus is not None
        assert concept.conceptid is not None
    
    def test_concept_unique_constraint(self, thesaurus, db):
        """Test that (thesaurus, conceptid) is unique."""
        concept_id = uuid.uuid4()
        Concept.objects.create(thesaurus=thesaurus, conceptid=concept_id)
        with pytest.raises(Exception):
            Concept.objects.create(thesaurus=thesaurus, conceptid=concept_id)
    
    def test_concept_cascade_delete(self, concept, db):
        """Test cascade delete of related properties."""
        prop = ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Test Label',
            lang='en'
        )
        concept_id = concept.pk
        concept.delete()
        assert not ConceptProperty.objects.filter(pk=prop.pk).exists()


class TestConceptProperty:
    """Test ConceptProperty model."""
    
    def test_concept_property_creation(self, concept, db):
        """Test ConceptProperty creation."""
        prop = ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Test Label',
            lang='en',
            type='literal'
        )
        assert prop.value == 'Test Label'
        assert prop.lang == 'en'


class TestConceptPredicate:
    """Test ConceptPredicate model."""
    
    def test_concept_predicate_creation(self, concept, thesaurus, db):
        """Test ConceptPredicate creation."""
        concept2 = Concept.objects.create(
            thesaurus=thesaurus,
            conceptid=uuid.uuid4()
        )
        pred = ConceptPredicate.objects.create(
            subject=concept,
            property='narrower',
            object=concept2
        )
        assert pred.subject == concept
        assert pred.object == concept2

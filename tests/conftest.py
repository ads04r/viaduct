# tests/conftest.py
import os
import django
from django.conf import settings
import pytest
from django.test import override_settings

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viaduct.settings')

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'api.apps.ApiConfig',
            'search.apps.SearchConfig',
        ],
        SECRET_KEY='test-secret-key',
        USER_AGENT='Viaduct/0.1',
        ARCHES_SEARCH_TIMEOUT=30,
    )
    django.setup()

@pytest.fixture
def db_setup(db):
    """Fixture to ensure database is ready for tests."""
    return db

@pytest.fixture
def user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

@pytest.fixture
def arches_instance(db):
    from api.models.arches import ArchesInstance
    return ArchesInstance.objects.create(
        label='Test Instance',
        url='https://test.arches.example.com'
    )

@pytest.fixture
def user_profile(user):
    """UserProfile is created automatically via signal."""
    return user.profile

@pytest.fixture
def graph_model(arches_instance):
    from api.models.arches import GraphModel
    import uuid
    return GraphModel.objects.create(
        instance=arches_instance,
        graphid=uuid.uuid4(),
        name='Test Model',
        slug='test-model',
        description='A test model',
    )

@pytest.fixture
def thesaurus(arches_instance):
    from api.models.arches import Thesaurus
    import uuid
    return Thesaurus.objects.create(
        instance=arches_instance,
        thesaurusid=uuid.uuid4(),
        label='Test Thesaurus',
    )

@pytest.fixture
def concept(thesaurus):
    from api.models.arches import Concept
    import uuid
    return Concept.objects.create(
        thesaurus=thesaurus,
        conceptid=uuid.uuid4(),
    )

# tests/test_search_utils.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from search.util import (
    strip_html_tags, build_context, keyword_search, concept_search
)
from api.models.arches import ArchesInstance, Concept, Thesaurus


class TestStripHtmlTags:
    """Test HTML tag stripping utility."""
    
    def test_strip_simple_html(self):
        """Test stripping basic HTML tags."""
        html = '<p>Hello <b>World</b></p>'
        result = strip_html_tags(html)
        assert result == 'Hello   World'
    
    def test_strip_nested_tags(self):
        """Test stripping nested HTML tags."""
        html = '<div><span>Content</span></div>'
        result = strip_html_tags(html)
        assert result == 'Content'
    
    def test_strip_tags_with_attributes(self):
        """Test stripping tags with attributes."""
        html = '<a href="http://example.com">Link</a>'
        result = strip_html_tags(html)
        assert result == 'Link'
    
    def test_strip_whitespace_handling(self):
        """Test that extra spaces are preserved and leading/trailing trimmed."""
        html = '  <p>Text</p>  '
        result = strip_html_tags(html)
        assert result == 'Text'
    
    def test_strip_empty_string(self):
        """Test stripping from empty string."""
        assert strip_html_tags('') == ''
    
    def test_strip_no_html(self):
        """Test string without HTML."""
        text = 'Plain text'
        assert strip_html_tags(text) == 'Plain text'


class TestBuildContext:
    """Test build_context function for search."""
    
    def test_build_context_no_query(self, db):
        """Test build_context with no search query."""
        factory = RequestFactory()
        request = factory.post('/search', {})
        
        context = build_context(request)
        
        assert context['query'] == ''
        assert context['searchtype'] == 'keyword'
        assert context['results'] is None
        assert isinstance(context['instances'], list)
    
    def test_build_context_with_query(self, db, arches_instance):
        """Test build_context with search query."""
        factory = RequestFactory()
        request = factory.post('/search', {'q': 'mosque'})
        
        context = build_context(request)
        
        assert context['query'] == 'mosque'
        assert context['searchtype'] == 'keyword'
    
    def test_build_context_search_type(self, db):
        """Test build_context with concept search type."""
        factory = RequestFactory()
        request = factory.post('/search', {
            'q': 'test',
            'search-type': 'concept'
        })
        
        context = build_context(request)
        
        assert context['searchtype'] == 'concept'
    
    def test_build_context_instance_selection(self, db, arches_instance):
        """Test build_context with instance selection."""
        factory = RequestFactory()
        request = factory.post('/search', {
            'arches-instance': str(arches_instance.pk)
        })
        
        context = build_context(request)
        instances = context['instances']
        
        selected = [i for i in instances if i['selected']]
        assert len(selected) == 1
        assert selected[0]['pk'] == arches_instance.pk
    
    def test_build_context_multiple_instances(self, db, arches_instance):
        """Test build_context lists all instances."""
        factory = RequestFactory()
        request = factory.post('/search', {})
        
        context = build_context(request)
        
        assert len(context['instances']) >= 1
        assert any(i['pk'] == arches_instance.pk for i in context['instances'])


class TestConceptSearch:
    """Test concept_search function."""
    
    def test_concept_search_exact_match(self, db, concept):
        """Test concept search finds exact property matches."""
        # Create a concept with a property
        from api.models.arches import ConceptProperty
        ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Heritage Place',
            lang='en'
        )
        
        results = concept_search('Heritage Place')
        
        assert len(results) > 0
        assert any(r['pk'] == concept.pk for r in results)
    
    def test_concept_search_partial_match(self, db, concept):
        """Test concept search with partial matching."""
        from api.models.arches import ConceptProperty
        ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Heritage Place Name',
            lang='en'
        )
        
        results = concept_search('Heritage')
        
        assert len(results) > 0
    
    def test_concept_search_case_insensitive(self, db, concept):
        """Test that concept search is case-insensitive."""
        from api.models.arches import ConceptProperty
        ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='HERITAGE',
            lang='en'
        )
        
        results = concept_search('heritage')
        
        assert len(results) > 0
    
    def test_concept_search_no_results(self, db):
        """Test concept search with no matches."""
        results = concept_search('nonexistent_term_xyz')
        assert results == []
    
    def test_concept_search_result_structure(self, db, concept):
        """Test that results have expected structure."""
        from api.models.arches import ConceptProperty
        ConceptProperty.objects.create(
            subject=concept,
            property='prefLabel',
            value='Test Concept',
            lang='en'
        )
        
        results = concept_search('Test')
        
        assert len(results) > 0
        result = results[0]
        assert 'pk' in result
        assert 'label' in result
        assert 'uri' in result
        assert 'source' in result

"""
Arches-related models and helpers.

This module defines models that represent remote Arches instances, logins and
graph models. Many methods perform HTTP requests against an Arches API and
return parsed JSON responses.
"""

from django.db import models
from django.conf import settings
from django.core.validators import validate_slug
from django.contrib.auth.models import User
from django.core.cache import cache
from urllib.parse import urlencode
from rdflib import Graph
from rdflib.namespace import RDF, SKOS, DC, DCTERMS, FOAF, DOAP, VOID, XSD
from rdflib.term import URIRef, Literal
import uuid, requests, json, datetime, logging, hashlib

logging.captureWarnings(True)
logger = logging.getLogger(__name__)

class ArchesInstance(models.Model):
	"""
	Represents a remote Arches instance.

	:param label: human-readable label for the instance
	:type label: str
	:param url: base URL of the remote Arches instance
	:type url: str

	Methods perform HTTP GET requests (using requests) to fetch resources and
	metadata from the instance. All requests set the 'User-Agent' header using
	the project's USER_AGENT setting.

	Example::

		instance = ArchesInstance.objects.create(label='Test', url='https://arches.example')
		models = instance.get_models()
	"""
	label = models.CharField(max_length=64, null=False)
	url = models.URLField(null=False)
	created_time = models.DateTimeField(auto_now_add=True)
	updated_time = models.DateTimeField(auto_now=True)
	def get_models(self):
		"""
		Fetch a list of resource models from the instance.

		:returns: list of models or None when the response does not include 'resources'
		:rtype: list or None

		:raises requests.RequestException: on network or response errors
		"""
		url = self.url.rstrip('/') + "/search_component_data/resource-type-filter"
		data = {}
		with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
			data = r.json()
		if data is None:
			return None
		if not 'resources' in data:
			return None
		return data['resources']
	def get_advanced_search_parameters(self):
		"""
		Retrieve information required in order to perform an advanced search on this instance.

		:returns: JSON data returned from the HTTP call
		:rtype: dict

		:raises requests.RequestException: on network or response errors
		"""
		url = self.url.rstrip('/') + "/search_component_data/advanced-search"
		with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
			return r.json()
	def get_collections(self):
		"""
		Retrieve the list of collections from the Arches instance.

		:returns: list of collections
		:rtype: dict
		"""
		url = self.url.rstrip('/') + "/concepts/tree/collections"
		with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
			return r.json()
	def get_thesauri(self):
		"""
		Fetch a list of thesauri from the instance.

		:returns: list of thesauri
		:rtype: dict
		"""
		url = self.url.rstrip('/') + "/concepts/tree/semantic"
		try:
			with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
				return r.json()
		except:
			return []

	def _get_search_page(self, query_string, page=1):
		filter = [{'inverted': False, 'type': 'string', 'context': '', 'context_label': '', 'id': query_string, 'text': 'Contains Term: ' + query_string, 'value': query_string, 'selected': True}]
		query = {'paging-filter': page, 'tiles': 'true', 'format': 'tilecsv', 'reportlink': 'true', 'language': '*', 'term-filter': json.dumps(filter)}
		url = self.url.rstrip('/') + "/search/resources?" + urlencode(query)
		try:
			with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
				data = r.json()
		except:
			data = {}
		if not 'results' in data:
			return []
		if not 'hits' in data['results']:
			return []
		if not 'hits' in data['results']['hits']:
			return []
		ret = []
		for x in data['results']['hits']['hits']:
			if '_source' in x:
				x['_source']['source'] = {"url": self.url, "label": self.label}
				if 'resourceinstanceid' in x['_source']:
					x['_source']['url'] = self.url.rstrip('/') + "/report/" + str(x['_source']['resourceinstanceid'])
			ret.append(x)
		return ret

	def keyword_search(self, query_string):
		"""
		Search the Arches instance for resources matching query_string.

		:param query_string: the search term
		:type query_string: str
		:returns: list of results (possibly empty)
		:rtype: list

		Example::

			>>> instance.search('mosque')
			[{'_id': '...', '_source': ...}, ...]
		"""
		cache_key = 'keyword_' + str(self.pk) + '_' + hashlib.sha1(query_string.lower().encode('utf8')).hexdigest()
		ret = cache.get(cache_key)
		if not ret is None:
			return ret
		ret = []
		dt_limit = datetime.datetime.now() + datetime.timedelta(seconds=settings.ARCHES_SEARCH_TIMEOUT)
		i = 1
		while True:
			page = self._get_search_page(query_string, i)
			i = i + 1
			if len(page) == 0:
				break
			if datetime.datetime.now() >= dt_limit:
				break
			ret = ret + page
		cache.set(cache_key, ret, 900) # Cache the results for 15 minutes
		return ret
	
	def __str__(self):
		return self.label

class ArchesLogin(models.Model):

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arches_logins')
	instance = models.ForeignKey(ArchesInstance, on_delete=models.CASCADE, related_name='logins')
	username = models.CharField(max_length=128, null=False)
	password = models.CharField(max_length=128, null=False)
	created_time = models.DateTimeField(auto_now_add=True)
	updated_time = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.user + ' / ' + str(self.instance)

	class Meta:
		unique_together = ('user', 'instance',)

class GraphModel(models.Model):
	"""
	Represents a model definition (resource model) provided by an Arches instance.

	:param instance: owning Arches instance
	:param graphid: unique (to the instance) id for model
	:param name: optional human readable name
	"""
	instance = models.ForeignKey(ArchesInstance, on_delete=models.CASCADE, related_name='models')
	graphid = models.UUIDField(default=uuid.uuid4)
	name = models.CharField(max_length=128, blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	version = models.TextField(blank=True, null=True)
	iconclass = models.TextField(blank=True, null=True)
	color = models.TextField(blank=True, null=True)
	subtitle = models.TextField(blank=True, null=True)
	slug = models.TextField(validators=[validate_slug])
	config = models.JSONField(db_column="config", default=dict)
	created_time = models.DateTimeField(auto_now_add=True)
	updated_time = models.DateTimeField(auto_now=True)

	@property
	def export_url(self):
		return self.instance.url.rstrip('/') + '/graph/' + str(self.graphid) + '/export'

	class Meta:
		unique_together = ('instance', 'graphid',)

	def __str__(self):
		return str(self.instance) + ' / ' + self.name

class Thesaurus(models.Model):

	instance = models.ForeignKey(ArchesInstance, on_delete=models.CASCADE, related_name='thesauri')
	thesaurusid = models.UUIDField(default=uuid.uuid4)
	label = models.CharField(max_length=128, default='')
	labelid = models.UUIDField(null=True, blank=True)
	load_on_demand = models.BooleanField(default=False)

	class Meta:
		unique_together = ('instance', 'thesaurusid',)

	def __str__(self):
		return str(self.instance) + ' / ' + self.label
	
	@property
	def skos_url(self):
		return self.instance.url + 'concepts/export/' + str(self.thesaurusid)
	
	def load_skos(self):
		g = Graph()
		with requests.get(self.skos_url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
			g.parse(data=r.content, format='xml')
		return g
	
	def build_description(self):
		return sorted([{"id": str(x.conceptid), "label": str(x.label)} for x in self.concepts.all()], key=lambda x: x['label'])

class Concept(models.Model):

	thesaurus = models.ForeignKey(Thesaurus, on_delete=models.CASCADE, related_name='concepts')
	conceptid = models.UUIDField(default=uuid.uuid4)

	@property
	def label(self):
		label = self.properties.filter(property='prefLabel', lang__startswith='en').first()
		if label:
			return str(label.value)
		return self.conceptid
	
	@property
	def uri(self):
		return str(self.thesaurus.instance.url).rstrip('/') + '/concepts/' + str(self.conceptid)

	def _get_search_page(self, page=1):
		filter = [{'inverted': False, 'type': 'concept', 'value': str(self.conceptid), 'selected': True}]
		query = {'paging-filter': page, 'tiles': 'true', 'format': 'tilecsv', 'reportlink': 'true', 'language': '*', 'term-filter': json.dumps(filter)}
		url = str(self.thesaurus.instance.url).rstrip('/') + "/search/resources?" + urlencode(query)
		print(url)
		try:
			with requests.get(url, verify=False, headers={'User-Agent': settings.USER_AGENT}) as r:
				data = r.json()
		except:
			data = {}
		if not 'results' in data:
			return []
		if not 'hits' in data['results']:
			return []
		if not 'hits' in data['results']['hits']:
			return []
		ret = []
		for x in data['results']['hits']['hits']:
			if '_source' in x:
				x['_source']['source'] = {"url": str(self.thesaurus.instance.url), "label": str(self.thesaurus.instance.label)}
				if 'resourceinstanceid' in x['_source']:
					x['_source']['url'] = str(self.thesaurus.instance.url).rstrip('/') + "/report/" + str(x['_source']['resourceinstanceid'])
			ret.append(x)
		return ret

	def search(self):
		"""
		Search the Arches instance for resources matching this concept.

		:returns: list of results (possibly empty)
		:rtype: list
		"""
		ret = []
		dt_limit = datetime.datetime.now() + datetime.timedelta(seconds=settings.ARCHES_SEARCH_TIMEOUT)
		i = 1
		while True:
			page = self._get_search_page(i)
			i = i + 1
			if len(page) == 0:
				break
			if datetime.datetime.now() >= dt_limit:
				break
			ret = ret + page
		return ret

	def rdf(self):
		g = Graph()
		s = URIRef(self.uri)
		g.add((s, RDF.type, SKOS.Concept))
		for pred in self.predicates.all():
			if not hasattr(SKOS, pred.property):
				continue
			g.add((s, getattr(SKOS, pred.property), URIRef(pred.object.uri)))
		for pred in self.predicates_rev.all():
			if not hasattr(SKOS, pred.property):
				continue
			g.add((URIRef(pred.subject.uri), getattr(SKOS, pred.property), s))
		for prop in self.properties.all():
			prop_uri = None
			for ns in [SKOS, DC, DCTERMS, RDF, DOAP, VOID, XSD, FOAF]:
				if hasattr(ns, prop.property):
					prop_uri = getattr(ns, prop.property)
					break
			if prop_uri is None:
				continue
			g.add((s, prop_uri, Literal(prop.value, lang=prop.lang)))

		return g

	def __str__(self):
		return str(self.thesaurus) + ' / ' + str(self.label)

	class Meta:
		unique_together = ('thesaurus', 'conceptid',)


class ConceptProperty(models.Model):

	subject = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='properties')
	property = models.SlugField(max_length=128)
	value = models.TextField(default='')
	type = models.SlugField(max_length=64, default='literal')
	lang = models.SlugField(max_length=64, default='en')

class ConceptPredicate(models.Model):

	subject = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='predicates')
	property = models.SlugField(max_length=128)
	object = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='predicates_rev')

class ConceptContext(models.Model):

	contextid = models.UUIDField(default=uuid.uuid4)
	concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='contexts')
	label = models.CharField(max_length=128, blank=True, null=True)
	class Meta:
		unique_together = ('concept', 'contextid',)

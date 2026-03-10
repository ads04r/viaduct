from rdflib.namespace import RDF, SKOS
from ..models import GraphModel, Thesaurus, Concept, ConceptPredicate, ConceptProperty
from tqdm import tqdm
import json, uuid

def load_instance_models(arches):
	"""Loads the resource models contained within an Arches instance, and stores them locally."""
	models_list = arches.get_models()
	if models_list is None:
		models_list = []
	for item in models_list:
		try:
			model = GraphModel.objects.get(instance=arches, graphid=item['graphid'])
		except:
			model = GraphModel(instance=arches, graphid=item['graphid'])
		model.name = item['name']
		model.description = item['description']
		model.version = item['version']
		model.iconclass = item['iconclass']
		model.color = item['color']
		model.subtitle = item['subtitle']
		model.slug = item['slug']
		model.config = item['config']
		if model.slug is None:
			model.slug = ''
		model.save()

def load_instance_thesauri(arches):
	"""Loads information about the thesauri contained on an Arches instance, and stores them locally."""
	for item in arches.get_thesauri():
		try:
			thesaurus = Thesaurus.objects.get(instance=arches, thesaurusid=item['id'])
		except:
			thesaurus = Thesaurus(instance=arches, thesaurusid=item['id'])
		thesaurus.label = item['label']
		thesaurus.labelid = item['labelid']
		thesaurus.load_on_demand = item['load_on_demand']
		thesaurus.save()

def __convert_arches_skos_to_string(value):

	try:
		lang = value.language
	except:
		lang = 'en'
	try:
		parsed_value = json.loads(str(value))
	except json.decoder.JSONDecodeError:
		parsed_value = value
	if isinstance(parsed_value, str):
		return (parsed_value, lang)
	if isinstance(parsed_value, dict):
		if 'value' in parsed_value:
			return (parsed_value['value'], lang)
	return (str(value), lang)

def __create_or_get_concept(uri, thesaurus=None):
	concept_id = str(uri).replace('#', '/').split('/')[-1]
	if len(concept_id) != 36:
		concept_id = concept_id[-36:]
	try:
		id = uuid.UUID(concept_id) # check to make sure this is a valid UUID, we'll have problems otherwise
	except:
		return None
	try:
		concept = Concept.objects.get(thesaurus=thesaurus, conceptid=concept_id)
	except:
		concept = Concept(thesaurus=thesaurus, conceptid=concept_id)
		concept.save()
	return concept

def __create_or_get_property(subject, property, value, lang='en', type='literal'):

	try:
		ret = ConceptProperty.objects.get(subject=subject, property=property, value=value, lang=lang, type=type)
	except:
		ret = ConceptProperty(subject=subject, property=property, value=value, lang=lang, type=type)
		ret.save()
	return ret

def __create_or_get_predicate(subject, property, object):

	try:
		ret = ConceptPredicate.objects.get(subject=subject, property=property, object=object)
	except:
		ret = ConceptPredicate(subject=subject, property=property, object=object)
		ret.save()
	return ret

def import_thesaurus(thesaurus, quiet=True):
	"""Loads a thesaurus proper from an Arches instance, parses the SKOS, and stores locally within the Viaduct database."""
	bar_format = str(thesaurus) + " |{bar}| {n_fmt}/{total_fmt}"
	if quiet:
		bar_format = ""
	g = thesaurus.load_skos()
	ConceptProperty.objects.filter(subject__thesaurus=thesaurus).delete()
	ConceptPredicate.objects.filter(subject__thesaurus=thesaurus).delete()
	concepts = []
	for concept, p, o in g.triples((None, RDF.type, SKOS.Concept)):
		concepts.append(concept)
	with tqdm(concepts, leave=False, bar_format=bar_format) as prog:
		for concept in prog:
			item = __create_or_get_concept(str(concept), thesaurus)
			if item is None:
				continue # This tends to happen if the remote Arches isn't set up correctly. Nothing we can do, so skip.
			for s, p, o in g.triples((concept, None, None)):
				if o.__class__.__name__ == 'URIRef':
					continue
				p_uri = str(p)
				if p_uri == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
					continue
				p_id = p_uri.replace('#', '/').split('/')[-1]
				value, lang = __convert_arches_skos_to_string(o)
				prop = __create_or_get_property(item, p_id, value, lang, 'literal')
			for s, p, o in g.triples((concept, None, None)):
				if not o.__class__.__name__ == 'URIRef':
					continue
				p_uri = str(p)
				if p_uri == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
					continue
				p_id = p_uri.replace('#', '/').split('/')[-1]
				object = __create_or_get_concept(str(o), thesaurus)
				pred = __create_or_get_predicate(item, p_id, object)

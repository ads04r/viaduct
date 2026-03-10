from django.shortcuts import render
from django.http import QueryDict
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from api.models.arches import ArchesInstance
from search.util import keyword_search, concept_search, advanced_search
import logging, json

logger = logging.getLogger(__name__)

def home(request):
	if 'q' in request.POST:
		query = str(request.POST['q'])
	else:
		query = ''
	selected_instances = []
	opts = []
	results = None
	type = 'keyword'
	postdata = dict(QueryDict(request.body.decode('utf-8')))
	if 'arches-instance' in postdata:
		opts = postdata['arches-instance']
		if not isinstance(opts, list):
			opts = [opts]
		for opt in opts:
			selected_instances.append(int(opt))
	searchtype = 'keyword'
	if 'search-type' in request.POST:
		searchtype = str(request.POST['search-type'])
	instances = [{"pk": instance.pk, "label": instance.label, "selected": (instance.pk in selected_instances)} for instance in ArchesInstance.objects.all()]

	if query:
		if searchtype == 'keyword':
			results = keyword_search(query)
		if searchtype == 'concept':
			results = concept_search(query)

	return render(request, 'search/index.html', {"query": query, "searchtype": searchtype, "instances": instances, "results": results})


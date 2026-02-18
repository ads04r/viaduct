from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from search.util import keyword_search, concept_search, advanced_search
import logging, json

logger = logging.getLogger(__name__)

def home(request):
	return render(request, 'search/index.html', {})

@csrf_exempt
def results(request):
	if 'q' in request.POST:
		query = str(request.POST['q'])
		logger.info("Keyword search: " + query)
		results = keyword_search(query)
		concepts = concept_search(query)
	else:
		query = ''
		if 'previousquery' in request.POST:
			query = request.POST['previousquery']
		ids = []
		for kk in request.POST.keys():
			k = str(kk)
			if k.startswith('concept_'):
				ids.append(k[8:])
		logger.info("Advanced search: " + json.dumps(ids))
		results, concepts = advanced_search(ids)
	mode = 'list'
	if 'category_map' in request.POST:
		mode = 'map'
	return render(request, 'search/results.html', {"query": query, "mode": mode, "results": results, "concepts": concepts, "mapboxkey": settings.MAPBOX_KEY})

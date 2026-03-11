from django.http import QueryDict
from api.models.arches import ArchesInstance, Concept
import re, asyncio, hashlib

def strip_html_tags(text):
    return (re.sub(r'<.*?>', ' ', text)).strip()

def build_context(request):

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

    return {"query": query, "searchtype": searchtype, "instances": instances, "results": results}


def keyword_search(query_string):
    global results, ct, loop
    results = []
    ct = ArchesInstance.objects.count()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    def callback(fut):
        global results, ct, loop
        results = results + fut.result()
        ct = ct - 1
        if ct<= 0:
            loop.stop()
    futures = []
    for arches in ArchesInstance.objects.all():
        fut = asyncio.ensure_future(asyncio.to_thread(arches.keyword_search, query_string))
        fut.add_done_callback(callback)
        futures.append(fut)
    loop.run_forever()

    ret = []
    for x in sorted(results, key=lambda x: x['_score']):
        if not '_source' in x:
            continue
        if 'displaydescription' in x['_source']:
            x['_source']['displaydescription'] = strip_html_tags(x['_source']['displaydescription'])
        ret.append(x['_source'])
    return ret

def concept_search(query_string):
    ret = []
    for concept in Concept.objects.filter(properties__value__icontains=query_string).distinct():
        ret.append({'pk': concept.pk, 'label': concept.label, 'uri': concept.uri, 'source': str(concept.thesaurus.instance)})
    return ret

def advanced_search(concept_ids):
    global results, ct, loop
    query_string = ' '.join(concept_ids)
    cache_key = hashlib.sha1(query_string.encode('utf8')).hexdigest()
    results = cache.get(cache_key)
    if not results is None:
        return results
    results = []
    concept_items = Concept.objects.filter(pk__in=concept_ids)
    ct = concept_items.count()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    def callback(fut):
        global results, ct, loop
        results = results + fut.result()
        ct = ct - 1
        if ct<= 0:
            loop.stop()
    futures = []
    concepts = []
    for concept in concept_items:
        concepts.append({'pk': concept.pk, 'label': concept.label, 'uri': concept.uri, 'source': str(concept.thesaurus.instance)})
        fut = asyncio.ensure_future(asyncio.to_thread(concept.search))
        fut.add_done_callback(callback)
        futures.append(fut)
    loop.run_forever()

    ret = []
    for x in sorted(results, key=lambda x: x['_score']):
        if not '_source' in x:
            continue
        if 'displaydescription' in x['_source']:
            x['_source']['displaydescription'] = strip_html_tags(x['_source']['displaydescription'])
        ret.append(x['_source'])
    cache.set(cache_key, ret, 300) # Cache the results for five minutes
    return (ret, concepts)

# https://database.eamena.org/search?paging-filter=1&tiles=true&format=tilecsv&reportlink=false&precision=6&exportsystemvalues=false&
# term-filter=%5B%7B%22context%22%3A%22%22%2C%22context_label%22%3A%22Heritage%20Place%20-%20Resource%20Name%22%2C%22id%22%3A%22termmosqueHeritage%20Place%20-%20Resource%20Name%22%2C%22nodegroupid%22%3A%2234cfe9dd-c2c0-11ea-9026-02e7594ce0a0%22%2C%22text%22%3A%22mosque%22%2C%22type%22%3A%22term%22%2C%22value%22%3A%22mosque%22%2C%22inverted%22%3Afalse%2C%22selected%22%3Atrue%7D%5D&language=*
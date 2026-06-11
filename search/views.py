from django.shortcuts import render
from search.util import build_context

def home(request):

	return render(request, 'search/index.html', build_context(request))



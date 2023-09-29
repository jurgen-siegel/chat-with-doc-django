from .ai import AI
from .contents import extract_text_from_pdf, extract_text_from_txt, extract_text_from_docx
from django.shortcuts import render
from .config import Config
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from urllib.parse import unquote
from django.http import JsonResponse

# Initialize the AI instance
ai_instance = AI(Config())

def webui(request):
    contents = []
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        filename = default_storage.save(file.name, file)

        # Extract content based on file type
        if filename.endswith('.pdf'):
            contents, lang = extract_text_from_pdf(default_storage.path(filename))
        elif filename.endswith('.txt'):
            contents, lang = extract_text_from_txt(default_storage.path(filename))
        elif filename.endswith('.docx'):
            with default_storage.open(filename, 'rb') as f:
                contents, lang = extract_text_from_docx(f)

        # Save contents to session for later use
        request.session['contents'] = contents

        return render(request, 'webui.html', {'contents': contents})

    return render(request, 'webui.html', {'contents': None})

@csrf_exempt
def process_query(request):
    if request.method == 'POST':
        query = request.POST.get('query')

        # Retrieve context (contents) from the session
        context = request.session.get('contents', [])

        # Process the query using the AI instance
        response = ai_instance.completion(query, context)

        return JsonResponse({"response": response})

    return JsonResponse({"error": "Only POST requests are allowed"})

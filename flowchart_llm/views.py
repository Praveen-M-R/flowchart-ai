from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .llm_utils import generate_flowchart_from_code

@csrf_exempt
@require_http_methods(["POST"])
def generate_flowchart_view(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    uploaded_file = request.FILES['file']
    file_content = uploaded_file.read().decode('utf-8')

    try:
        mermaid_flowchart = generate_flowchart_from_code(file_content)
        return JsonResponse({'mermaid_flowchart': mermaid_flowchart})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

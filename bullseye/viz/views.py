from django.shortcuts import render


def viz(request):
    return render(request, 'viz/viz.html')

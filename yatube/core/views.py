from django.shortcuts import render


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    template = 'core/404.html'
    return render(request, template, {'path': request.path}, status=404)


def server_error(request):
    template = 'core/500.html'
    return render(request, template, status=500)


def permission_denied(request, exception):
    template = 'core/403.html'
    return render(request, template, status=403)


def csrf_failure(request, reason=''):
    template = 'core/403csrf.html'
    return render(request, template)